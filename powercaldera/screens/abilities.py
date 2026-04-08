"""Pantalla de Habilidades — buscar, ver detalle y crear."""

from __future__ import annotations

import logging
import uuid

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.markup import escape
from textual.screen import ModalScreen
from textual.timer import Timer
from textual.widgets import (
    DataTable, Footer, Input, Static, Button, TextArea, Select,
)

from ..api.models import Ability, CreateAbilityRequest
from ..utils import truncate
from ..widgets.header_bar import HeaderBar
from ..widgets.status_bar import StatusBar
from .base import BaseScreen

logger = logging.getLogger(__name__)

MAX_ROWS = 200
SEARCH_DEBOUNCE_S = 0.3


class CreateAbilityModal(ModalScreen[bool]):
    """Modal para crear una habilidad manualmente."""

    DEFAULT_CSS = """
    CreateAbilityModal {
        align: center middle;
    }
    #create-ability-dialog {
        width: 80;
        height: auto;
        max-height: 38;
        background: #1a1a2e;
        border: thick #0f3460;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="create-ability-dialog"):
            yield Static("[bold #00ff41]Crear Nueva Habilidad[/]")
            yield Static("Nombre:")
            yield Input(placeholder="Nombre de la habilidad", id="ab-name")
            yield Static("Descripción:")
            yield Input(placeholder="Descripción", id="ab-desc")
            yield Static("Táctica:")
            yield Select(
                [(t, t) for t in [
                    "reconnaissance", "resource-development", "initial-access",
                    "execution", "persistence", "privilege-escalation",
                    "defense-evasion", "credential-access", "discovery",
                    "lateral-movement", "collection", "command-and-control",
                    "exfiltration", "impact",
                ]],
                prompt="Seleccionar táctica",
                id="ab-tactic",
            )
            yield Static("ID Técnica (ej: T1082):")
            yield Input(placeholder="T1082", id="ab-tech-id")
            yield Static("Nombre Técnica:")
            yield Input(placeholder="System Information Discovery", id="ab-tech-name")
            yield Static("Plataforma:")
            yield Select(
                [("windows", "windows"), ("linux", "linux"), ("darwin", "darwin")],
                prompt="Seleccionar plataforma",
                id="ab-platform",
            )
            yield Static("Ejecutor:")
            yield Select(
                [("psh", "psh"), ("cmd", "cmd"), ("sh", "sh"), ("bash", "bash")],
                prompt="Seleccionar ejecutor",
                id="ab-executor",
            )
            yield Static("Comando:")
            yield TextArea(id="ab-command")
            with Horizontal():
                yield Button("Crear", variant="success", id="btn-create")
                yield Button("Cancelar", variant="error", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-create":
            self.run_worker(self._create_ability(), exclusive=True)

    async def _create_ability(self) -> None:
        try:
            name = self.query_one("#ab-name", Input).value.strip()
            if not name:
                self.notify("El nombre es obligatorio", severity="error")
                return

            tactic_select = self.query_one("#ab-tactic", Select)
            if tactic_select.value is Select.BLANK:
                self.notify("Selecciona una táctica", severity="error")
                return

            platform_select = self.query_one("#ab-platform", Select)
            executor_select = self.query_one("#ab-executor", Select)
            command = self.query_one("#ab-command", TextArea).text.strip()

            if not command:
                self.notify("El comando es obligatorio", severity="error")
                return

            req = CreateAbilityRequest(
                ability_id=f"pc-ab-{uuid.uuid4().hex[:8]}",
                name=name,
                description=self.query_one("#ab-desc", Input).value.strip(),
                tactic=str(tactic_select.value),
                technique_id=self.query_one("#ab-tech-id", Input).value.strip() or "T0000",
                technique_name=self.query_one("#ab-tech-name", Input).value.strip() or name,
                executors=[{
                    "name": str(executor_select.value) if executor_select.value is not Select.BLANK else "psh",
                    "platform": str(platform_select.value) if platform_select.value is not Select.BLANK else "windows",
                    "command": command,
                    "payloads": [],
                }],
            )
            await self.app.client.create_ability(req)
            self.app.invalidate_cache()
            logger.info("Habilidad '%s' creada desde modal", name)
            self.notify(f"Habilidad '{name}' creada", severity="information")
            self.dismiss(True)
        except Exception as e:
            logger.error("Error creando habilidad: %s", e, exc_info=True)
            self.notify(f"Error: {escape(str(e))}", severity="error")


class AbilitiesScreen(BaseScreen):

    BINDINGS = [
        ("r", "refresh", "Refrescar"),
        ("c", "create", "Crear"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._abilities: list[Ability] = []
        self._displayed: list[Ability] = []
        self._search_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield HeaderBar()
        yield Static("[bold #00ff41]--- Habilidades ---[/]", classes="section-title")
        yield Input(placeholder="Buscar por nombre, táctica o técnica...", id="search-input")
        yield Static("", id="result-count")
        with Horizontal(classes="split-horizontal"):
            yield DataTable(id="abilities-table")
            yield Static("Selecciona una habilidad para ver detalles", id="ability-detail")
        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#abilities-table", DataTable)
        table.add_columns("ID", "Nombre", "Táctica", "Técnica", "Plataformas")
        table.cursor_type = "row"
        self.load_data()

    async def _load_data(self) -> None:
        try:
            if not await self._check_connection():
                return
            self._abilities = await self.app.get_abilities()
            self._render_table(self._abilities)
        except Exception as e:
            logger.error("Error al cargar habilidades: %s", e, exc_info=True)
            self.notify(f"Error al cargar habilidades: {escape(str(e))}", severity="error")

    def _render_table(self, abilities: list[Ability]) -> None:
        self._displayed = abilities[:MAX_ROWS]
        table = self.query_one("#abilities-table", DataTable)
        table.clear()
        for ab in self._displayed:
            platforms = ", ".join(set(e.platform for e in ab.executors)) or "-"
            table.add_row(
                ab.ability_id[:12],
                truncate(ab.name, 40),
                ab.tactic,
                ab.technique_id,
                platforms,
            )
        count_label = self.query_one("#result-count", Static)
        total = len(abilities)
        shown = len(self._displayed)
        if total > MAX_ROWS:
            count_label.update(f"[dim]Mostrando {shown} de {total} habilidades (usa búsqueda para filtrar)[/]")
        else:
            count_label.update(f"[dim]{total} habilidades[/]")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            if self._search_timer is not None:
                self._search_timer.stop()
            self._search_timer = self.set_timer(
                SEARCH_DEBOUNCE_S, self._do_search
            )

    def _do_search(self) -> None:
        q = self.query_one("#search-input", Input).value.strip()
        if not q:
            self._render_table(self._abilities)
        else:
            filtered = self.app.abilities_cache.search(q)
            self._render_table(filtered)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key is not None:
            idx = event.cursor_row
            if 0 <= idx < len(self._displayed):
                self._show_detail(self._displayed[idx])

    def _show_detail(self, ab: Ability) -> None:
        detail = self.query_one("#ability-detail", Static)
        executors_text = ""
        for ex in ab.executors:
            executors_text += f"\n  [{ex.platform}] {ex.name}: {ex.command[:100]}"

        detail.update(
            f"[bold #00ff41]{ab.name}[/]\n\n"
            f"[bold]ID:[/] {ab.ability_id}\n"
            f"[bold]Táctica:[/] {ab.tactic}\n"
            f"[bold]Técnica:[/] {ab.technique_id} — {ab.technique_name}\n"
            f"[bold]Descripción:[/] {ab.description or '-'}\n"
            f"[bold]Plugin:[/] {ab.plugin or '-'}\n"
            f"[bold]Ejecutores:[/]{executors_text or ' (ninguno)'}"
        )

    def action_refresh(self) -> None:
        self.app.invalidate_cache()
        self.load_data()

    def action_create(self) -> None:
        def on_dismiss(result: bool) -> None:
            if result:
                self.load_data()
        self.app.push_screen(CreateAbilityModal(), callback=on_dismiss)
