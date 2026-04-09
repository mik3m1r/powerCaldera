"""Pantalla de Adversarios — listar, ver detalle y crear."""

from __future__ import annotations

import logging
import uuid

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.markup import escape
from textual.screen import ModalScreen
from textual.timer import Timer
from textual.widgets import (
    DataTable, Footer, Input, Static, Button, SelectionList,
)

from ..api.models import Ability, Adversary, CreateAdversaryRequest
from ..utils import truncate
from ..widgets.header_bar import HeaderBar
from ..widgets.status_bar import StatusBar
from .base import BaseScreen

logger = logging.getLogger(__name__)

SEARCH_DEBOUNCE_S = 0.3


class CreateAdversaryModal(ModalScreen[bool]):
    """Modal para crear un adversario custom."""

    DEFAULT_CSS = """
    CreateAdversaryModal {
        align: center middle;
    }
    #create-adv-dialog {
        width: 90;
        height: auto;
        max-height: 40;
        background: #1a1a2e;
        border: thick #0f3460;
        padding: 1 2;
    }
    """

    def __init__(self, abilities: list[Ability]) -> None:
        super().__init__()
        self._abilities = abilities

    def compose(self) -> ComposeResult:
        with Vertical(id="create-adv-dialog"):
            yield Static("[bold #00ff41]Crear Nuevo Adversario[/]")
            yield Static("Nombre:")
            yield Input(placeholder="Nombre del adversario", id="adv-name")
            yield Static("Descripción:")
            yield Input(placeholder="Descripción", id="adv-desc")
            yield Static("Tags (separados por coma):")
            yield Input(placeholder="apt, lateral-movement", id="adv-tags")
            yield Static("[bold]Seleccionar Habilidades (orden de ejecución):[/]")
            yield SelectionList[str](
                *[
                    (f"{ab.name} ({ab.tactic} - {ab.technique_id})", ab.ability_id)
                    for ab in self._abilities
                ],
                id="adv-abilities",
            )
            with Horizontal():
                yield Button("Crear", variant="success", id="btn-create")
                yield Button("Cancelar", variant="error", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-create":
            self.run_worker(self._create_adversary(), exclusive=True)

    async def _create_adversary(self) -> None:
        try:
            name = self.query_one("#adv-name", Input).value.strip()
            if not name:
                self.notify("El nombre es obligatorio", severity="error")
                return

            selection_list = self.query_one("#adv-abilities", SelectionList)
            selected_ids = list(selection_list.selected)
            if not selected_ids:
                self.notify("Selecciona al menos una habilidad", severity="error")
                return

            tags_raw = self.query_one("#adv-tags", Input).value.strip()
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

            req = CreateAdversaryRequest(
                adversary_id=f"pc-adv-{uuid.uuid4().hex[:8]}",
                name=name,
                description=self.query_one("#adv-desc", Input).value.strip(),
                atomic_ordering=selected_ids,
                tags=tags,
            )
            await self.app.client.create_adversary(req)
            logger.info("Adversario '%s' creado desde modal", name)
            self.notify(f"Adversario '{name}' creado", severity="information")
            self.dismiss(True)
        except Exception as e:
            logger.error("Error creando adversario: %s", e, exc_info=True)
            self.notify(f"Error: {escape(str(e))}", severity="error")


class AdversariesScreen(BaseScreen):

    BINDINGS = [
        ("r", "refresh", "Refrescar"),
        ("c", "create", "Crear"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._adversaries: list[Adversary] = []
        self._displayed: list[Adversary] = []
        self._abilities: list[Ability] = []
        self._ability_map: dict[str, Ability] = {}
        self._search_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield HeaderBar()
        yield Static("[bold #00ff41]--- Adversarios ---[/]", classes="section-title")
        yield Input(placeholder="Buscar por nombre, ID o tag...", id="search-input")
        yield Static("", id="result-count")
        with Horizontal(classes="content-area"):
            with Vertical(classes="pane-left"):
                yield DataTable(id="adversaries-table")
            with Vertical(classes="pane-right"):
                yield Static("Selecciona un adversario para ver detalles", id="adversary-detail")
        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#adversaries-table", DataTable)
        table.add_columns("ID", "Nombre", "Habilidades", "Tags")
        table.cursor_type = "row"
        self.load_data()

    async def _load_data(self) -> None:
        try:
            if not await self._check_connection():
                return
            self._adversaries = await self.app.client.list_adversaries()
            self._abilities = await self.app.get_abilities()
            self._ability_map = self.app.abilities_cache.ability_map
            self._render_table(self._adversaries)
        except Exception as e:
            logger.error("Error al cargar adversarios: %s", e, exc_info=True)
            self.notify(f"Error al cargar adversarios: {escape(str(e))}", severity="error")

    def _render_table(self, adversaries: list[Adversary]) -> None:
        self._displayed = adversaries
        table = self.query_one("#adversaries-table", DataTable)
        table.clear()
        for adv in self._displayed:
            tags = ", ".join(adv.tags[:3]) if adv.tags else "-"
            table.add_row(
                adv.adversary_id[:12],
                truncate(adv.name, 35),
                str(len(adv.atomic_ordering)),
                tags,
            )
        count_label = self.query_one("#result-count", Static)
        total = len(self._adversaries)
        shown = len(self._displayed)
        if shown < total:
            count_label.update(f"[dim]Mostrando {shown} de {total} adversarios[/]")
        else:
            count_label.update(f"[dim]{total} adversarios[/]")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            if self._search_timer is not None:
                self._search_timer.stop()
            self._search_timer = self.set_timer(SEARCH_DEBOUNCE_S, self._do_search)

    def _do_search(self) -> None:
        q = self.query_one("#search-input", Input).value.strip().lower()
        if not q:
            self._render_table(self._adversaries)
        else:
            filtered = [
                adv for adv in self._adversaries
                if q in adv.name.lower()
                or q in adv.adversary_id.lower()
                or any(q in tag.lower() for tag in adv.tags)
                or q in (adv.description or "").lower()
            ]
            self._render_table(filtered)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key is not None:
            idx = event.cursor_row
            if 0 <= idx < len(self._displayed):
                self._show_detail(self._displayed[idx])

    def _show_detail(self, adv: Adversary) -> None:
        detail = self.query_one("#adversary-detail", Static)
        abilities_text = ""
        for i, aid in enumerate(adv.atomic_ordering, 1):
            ab = self._ability_map.get(aid)
            if ab:
                abilities_text += f"\n  {i}. {ab.name} ({ab.tactic} - {ab.technique_id})"
            else:
                abilities_text += f"\n  {i}. {aid} (no encontrada)"

        tags = ", ".join(adv.tags) if adv.tags else "-"

        detail.update(
            f"[bold #00ff41]{adv.name}[/]\n\n"
            f"[bold]ID:[/] {adv.adversary_id}\n"
            f"[bold]Descripción:[/] {adv.description or '-'}\n"
            f"[bold]Tags:[/] [#ffd700]{tags}[/]\n"
            f"[bold]Plugin:[/] {adv.plugin or '-'}\n"
            f"[bold]Cadena de Ataque ({len(adv.atomic_ordering)} habilidades):[/]{abilities_text or ' (vacía)'}"
        )

    def action_refresh(self) -> None:
        self.load_data()

    def action_create(self) -> None:
        def on_dismiss(result: bool) -> None:
            if result:
                self.load_data()
        self.app.push_screen(CreateAdversaryModal(self._abilities), callback=on_dismiss)
