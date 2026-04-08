"""Pantalla de Operaciones — crear, controlar y ver resultados."""

from __future__ import annotations

import base64
import logging

logger = logging.getLogger(__name__)

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.markup import escape
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    DataTable, Footer, Static, Button, Input, Select, RichLog,
)

from ..api.models import (
    Adversary, CreateOperationRequest, Operation, OperationLink, Planner, Source,
)
from ..widgets.header_bar import HeaderBar
from ..widgets.status_bar import StatusBar


class CreateOperationModal(ModalScreen[bool]):
    """Modal para crear una operación."""

    DEFAULT_CSS = """
    CreateOperationModal {
        align: center middle;
    }
    #create-op-dialog {
        width: 80;
        height: auto;
        max-height: 35;
        background: #1a1a2e;
        border: thick #0f3460;
        padding: 1 2;
    }
    """

    def __init__(
        self,
        adversaries: list[Adversary],
        planners: list[Planner],
        sources: list[Source],
    ) -> None:
        super().__init__()
        self._adversaries = adversaries
        self._planners = planners
        self._sources = sources

    def compose(self) -> ComposeResult:
        with Vertical(id="create-op-dialog"):
            yield Static("[bold #00ff41]Crear Nueva Operación[/]")
            yield Static("Nombre:")
            yield Input(placeholder="Nombre de la operación", id="op-name")
            yield Static("Adversario:")
            yield Select(
                [(a.name, a.adversary_id) for a in self._adversaries],
                prompt="Seleccionar adversario",
                id="op-adversary",
            )
            yield Static("Planner:")
            yield Select(
                [(p.name, p.id) for p in self._planners],
                prompt="Seleccionar planner",
                id="op-planner",
            )
            yield Static("Source:")
            yield Select(
                [(s.name, s.id) for s in self._sources],
                prompt="Seleccionar source",
                id="op-source",
            )
            yield Static("Grupo de agentes (vacío = todos):")
            yield Input(placeholder="red, blue, etc.", id="op-group")
            with Horizontal():
                yield Button("Crear", variant="success", id="btn-create")
                yield Button("Cancelar", variant="error", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        elif event.button.id == "btn-create":
            self.run_worker(self._create_operation(), exclusive=True)

    async def _create_operation(self) -> None:
        try:
            name = self.query_one("#op-name", Input).value.strip()
            if not name:
                self.notify("El nombre es obligatorio", severity="error")
                return

            adv_select = self.query_one("#op-adversary", Select)
            planner_select = self.query_one("#op-planner", Select)
            source_select = self.query_one("#op-source", Select)

            if adv_select.value is Select.BLANK:
                self.notify("Selecciona un adversario", severity="error")
                return

            req = CreateOperationRequest(
                name=name,
                adversary={"adversary_id": str(adv_select.value)},
                planner={"id": str(planner_select.value) if planner_select.value is not Select.BLANK else "atomic"},
                source={"id": str(source_select.value) if source_select.value is not Select.BLANK else "basic"},
                group=self.query_one("#op-group", Input).value.strip(),
            )
            await self.app.client.create_operation(req)
            logger.info("Operación '%s' creada desde modal", name)
            self.notify(f"Operación '{name}' creada", severity="information")
            self.dismiss(True)
        except Exception as e:
            logger.error("Error creando operación: %s", e, exc_info=True)
            self.notify(f"Error: {escape(str(e))}", severity="error")


class OperationsScreen(Screen):

    BINDINGS = [
        ("r", "refresh", "Refrescar"),
        ("c", "create", "Crear"),
        ("p", "pause", "Pausar"),
        ("f", "finish", "Finalizar"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._operations: list[Operation] = []
        self._adversaries: list[Adversary] = []
        self._planners: list[Planner] = []
        self._sources: list[Source] = []
        self._selected_op: Operation | None = None

    def compose(self) -> ComposeResult:
        yield HeaderBar()
        yield Static("[bold #00ff41]--- Operaciones ---[/]", classes="section-title")
        with Horizontal(classes="split-horizontal"):
            with Vertical():
                yield DataTable(id="ops-table")
                with Horizontal():
                    yield Button("Crear", variant="success", id="btn-new-op")
                    yield Button("Pausar", id="btn-pause-op")
                    yield Button("Reanudar", id="btn-resume-op")
                    yield Button("Finalizar", variant="error", id="btn-finish-op")
                    yield Button("Reporte", id="btn-report-op")
            yield Vertical(
                Static("[bold]Detalle de Operación[/]", id="op-detail"),
                Static("[bold]Links Ejecutados:[/]"),
                RichLog(id="op-links-log", wrap=True),
                id="preview-panel",
            )
        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#ops-table", DataTable)
        table.add_columns("ID", "Nombre", "Estado", "Adversario", "Inicio")
        table.cursor_type = "row"
        self.load_data()

    def load_data(self) -> None:
        self.run_worker(self._load_data(), exclusive=True)

    async def _load_data(self) -> None:
        try:
            connected = await self.app.client.health_check()
            if not connected:
                logger.warning("OperationsScreen: sin conexión a Caldera")
                self.notify(
                    "Sin conexión con Caldera. Verifica URL y API key ([r] para reintentar).",
                    severity="warning",
                    timeout=8,
                )
                return
            client = self.app.client
            self._operations = await client.list_operations()
            self._adversaries = await client.list_adversaries()
            try:
                self._planners = await client.list_planners()
            except Exception:
                logger.debug("No se pudieron cargar planners", exc_info=True)
                self._planners = []
            try:
                self._sources = await client.list_sources()
            except Exception:
                logger.debug("No se pudieron cargar sources", exc_info=True)
                self._sources = []

            table = self.query_one("#ops-table", DataTable)
            table.clear()
            for op in self._operations:
                adv_name = op.adversary.name if op.adversary else "-"
                table.add_row(
                    op.id[:8],
                    op.name[:30],
                    op.state,
                    adv_name[:25],
                    op.start[:19] if op.start else "-",
                )
        except Exception as e:
            logger.error("Error al cargar operaciones: %s", e, exc_info=True)
            self.notify(f"Error al cargar operaciones: {escape(str(e))}", severity="error")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        idx = event.cursor_row
        if 0 <= idx < len(self._operations):
            self._selected_op = self._operations[idx]
            self._show_detail(self._selected_op)
            self.run_worker(self._load_links(self._selected_op.id), exclusive=True)

    def _show_detail(self, op: Operation) -> None:
        detail = self.query_one("#op-detail", Static)
        adv_name = op.adversary.name if op.adversary else "-"
        planner_name = op.planner.get("name", op.planner.get("id", "-"))
        detail.update(
            f"[bold #00ff41]{op.name}[/]\n\n"
            f"[bold]ID:[/] {op.id}\n"
            f"[bold]Estado:[/] {op.state}\n"
            f"[bold]Adversario:[/] {adv_name}\n"
            f"[bold]Planner:[/] {planner_name}\n"
            f"[bold]Inicio:[/] {op.start[:19] if op.start else '-'}\n"
            f"[bold]Fin:[/] {op.finish[:19] if op.finish else '-'}"
        )

    async def _load_links(self, op_id: str) -> None:
        try:
            links = await self.app.client.get_operation_links(op_id)
            log = self.query_one("#op-links-log", RichLog)
            log.clear()
            if not links:
                log.write("[dim]Sin links ejecutados[/]")
                return
            for link in links:
                ability_name = link.ability.get("name", "?") if link.ability else "?"
                status_icon = {0: "[green]\u2713[/]", -2: "[yellow]\u25cb[/]", 1: "[red]\u2717[/]"}.get(
                    link.status, f"[dim]{link.status}[/]"
                )
                log.write(f"{status_icon} {ability_name} [dim](paw: {link.paw})[/]")
                if link.output:
                    try:
                        decoded = base64.b64decode(link.output).decode("utf-8", errors="replace")
                        log.write(f"  [dim]{decoded[:200]}[/]")
                    except Exception:
                        logger.debug("Error decodificando output base64 del link", exc_info=True)
                        log.write(f"  [dim]{link.output[:200]}[/]")
        except Exception as e:
            logger.error("Error cargando links de operación %s: %s", op_id[:8], e, exc_info=True)
            log = self.query_one("#op-links-log", RichLog)
            log.clear()
            log.write(f"[red]Error cargando links: {e}[/]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-new-op":
            self.action_create()
        elif event.button.id == "btn-pause-op":
            self.run_worker(self._change_state("paused"), exclusive=True)
        elif event.button.id == "btn-resume-op":
            self.run_worker(self._change_state("running"), exclusive=True)
        elif event.button.id == "btn-finish-op":
            self.run_worker(self._change_state("finished"), exclusive=True)
        elif event.button.id == "btn-report-op":
            self.run_worker(self._generate_report(), exclusive=True)

    async def _change_state(self, state: str) -> None:
        if not self._selected_op:
            self.notify("Selecciona una operación primero", severity="warning")
            return
        try:
            await self.app.client.update_operation_state(self._selected_op.id, state)
            logger.info("Operación %s estado → '%s'", self._selected_op.id[:8], state)
            self.notify(f"Estado cambiado a '{state}'", severity="information")
            self.load_data()
        except Exception as e:
            logger.error("Error cambiando estado de operación: %s", e, exc_info=True)
            self.notify(f"Error: {escape(str(e))}", severity="error")

    async def _generate_report(self) -> None:
        if not self._selected_op:
            self.notify("Selecciona una operación primero", severity="warning")
            return
        try:
            report = await self.app.client.get_operation_report(self._selected_op.id)
            log = self.query_one("#op-links-log", RichLog)
            log.clear()
            log.write("[bold #00ff41]--- Reporte de Operación ---[/]\n")
            steps = report.get("steps", {})
            for paw, paw_steps in steps.items():
                log.write(f"\n[bold]Agente: {paw}[/]")
                for step in paw_steps:
                    ab_name = step.get("ability_id", "?")
                    status = step.get("status", "?")
                    log.write(f"  {status}: {ab_name}")
            self.notify("Reporte generado", severity="information")
        except Exception as e:
            logger.error("Error generando reporte: %s", e, exc_info=True)
            self.notify(f"Error: {escape(str(e))}", severity="error")

    def action_refresh(self) -> None:
        self.load_data()

    def action_create(self) -> None:
        def on_dismiss(result: bool) -> None:
            if result:
                self.load_data()
        self.app.push_screen(
            CreateOperationModal(self._adversaries, self._planners, self._sources),
            callback=on_dismiss,
        )

    def action_pause(self) -> None:
        self.run_worker(self._change_state("paused"), exclusive=True)

    def action_finish(self) -> None:
        self.run_worker(self._change_state("finished"), exclusive=True)
