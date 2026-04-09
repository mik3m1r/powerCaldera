"""Pantalla de Plantillas — importar JSON, preview y desplegar."""

from __future__ import annotations

import logging
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.markup import escape
from textual.widgets import (
    Button, DataTable, Footer, Input, RichLog, Static, TabbedContent, TabPane, TextArea,
)

from ..templates.loader import TemplateLoader
from ..templates.models import TemplateModel
from ..widgets.header_bar import HeaderBar
from ..widgets.status_bar import StatusBar
from .base import BaseScreen

logger = logging.getLogger(__name__)


class TemplatesScreen(BaseScreen):

    BINDINGS = [
        ("r", "refresh", "Refrescar"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._loader = TemplateLoader()
        self._builtin: list[tuple[str, TemplateModel]] = []
        self._selected_builtin: TemplateModel | None = None
        self._imported_template: TemplateModel | None = None

    def compose(self) -> ComposeResult:
        yield HeaderBar()
        yield Static("[bold #00ff41]--- Templates ---[/]", classes="section-title")
        with TabbedContent(initial="tab-builtin"):
            with TabPane("Predefinidas", id="tab-builtin"):
                with Horizontal(classes="content-area"):
                    with Vertical(classes="pane-left"):
                        yield DataTable(id="builtin-table")
                        with Horizontal(classes="button-row"):
                            yield Button("Desplegar", variant="success", id="btn-deploy-builtin")
                    with Vertical(classes="pane-right"):
                        yield Static("Selecciona una plantilla para ver el detalle", id="builtin-preview")
            with TabPane("Importar JSON", id="tab-import"):
                with Vertical(classes="content-area"):
                    with Horizontal(classes="button-row"):
                        yield Input(placeholder="Ruta al archivo .json (opcional)", id="file-path-input")
                        yield Button("Cargar archivo", id="btn-load-file")
                    yield TextArea(id="json-input")
                    with Horizontal(classes="button-row"):
                        yield Button("Validar", variant="primary", id="btn-validate")
                        yield Button("Desplegar", variant="success", id="btn-deploy-import")
                    yield RichLog(id="import-preview-log", markup=True)
        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        # Inicializar loader con templates_dir desde config si está configurado
        config = getattr(self.app, "config", None)
        if config is not None:
            td = getattr(config, "templates_dir", None)
            if td:
                self._loader = TemplateLoader(extra_dirs=[Path(td)])
        # Defer table setup until after TabbedContent has fully mounted its children
        self.call_after_refresh(self._init_builtin_table)

    def _init_builtin_table(self) -> None:
        table = self.query_one("#builtin-table", DataTable)
        table.add_columns("Archivo", "Nombre", "Habilidades", "Tácticas")
        table.cursor_type = "row"
        self._load_builtin()

    async def _load_data(self) -> None:
        """Recarga las plantillas builtin (llamado por load_data / acción refresh)."""
        self._load_builtin()

    def _load_builtin(self) -> None:
        try:
            self._builtin = self._loader.list_builtin()
            table = self.query_one("#builtin-table", DataTable)
            table.clear()
            for filename, tpl in self._builtin:
                tactics = ", ".join(sorted(set(ab.tactic for ab in tpl.abilities)))
                table.add_row(filename, tpl.name, str(len(tpl.abilities)), tactics[:40])
        except Exception as e:
            logger.error("Error loading builtin templates: %s", e, exc_info=True)
            self.notify(f"Error cargando plantillas: {escape(str(e))}", severity="error")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id == "builtin-table":
            idx = event.cursor_row
            if 0 <= idx < len(self._builtin):
                _, tpl = self._builtin[idx]
                self._selected_builtin = tpl
                self._show_builtin_preview(tpl)

    def _show_builtin_preview(self, tpl: TemplateModel) -> None:
        preview = self.query_one("#builtin-preview", Static)
        tags = ", ".join(tpl.tags) if tpl.tags else "-"
        abilities_text = ""
        for i, ab in enumerate(tpl.abilities, 1):
            platforms = []
            if ab.platforms.windows:
                platforms.append("win")
            if ab.platforms.linux:
                platforms.append("linux")
            if ab.platforms.darwin:
                platforms.append("mac")
            plat = "/".join(platforms)
            abilities_text += (
                f"\n  {i}. [bold]{ab.name}[/]"
                f"\n     {ab.tactic} | {ab.technique_id} — {ab.technique_name}"
                f"\n     Plataformas: {plat}"
            )

        preview.update(
            f"[bold #00ff41]{tpl.name}[/]\n\n"
            f"[bold]Descripción:[/] {tpl.description or '-'}\n"
            f"[bold]Tags:[/] [#ffd700]{tags}[/]\n"
            f"[bold]Habilidades ({len(tpl.abilities)}):[/]{abilities_text}"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-validate":
            self._validate_json()
        elif event.button.id == "btn-load-file":
            self._load_file()
        elif event.button.id == "btn-deploy-builtin":
            self.run_worker(self._deploy_template(self._selected_builtin, "predefinida"), exclusive=True)
        elif event.button.id == "btn-deploy-import":
            self.run_worker(self._deploy_template(self._imported_template, "importada"), exclusive=True)

    def _validate_json(self) -> None:
        text = self.query_one("#json-input", TextArea).text.strip()
        log = self.query_one("#import-preview-log", RichLog)
        log.clear()

        if not text:
            log.write("[red]Pega un JSON de plantilla en el área de texto[/]")
            return

        ok, error = TemplateLoader.validate(text)
        if ok:
            tpl = TemplateLoader.load_from_string(text)
            self._imported_template = tpl
            self._show_import_preview(tpl)
            log.write("[green]\u2713 JSON válido — listo para desplegar[/]\n")
        else:
            self._imported_template = None
            log.write(f"[red]\u2717 {error}[/]")

    def _load_file(self) -> None:
        path_str = self.query_one("#file-path-input", Input).value.strip()
        log = self.query_one("#import-preview-log", RichLog)
        log.clear()

        if not path_str:
            log.write("[red]Ingresa la ruta al archivo .json[/]")
            return

        path = Path(path_str)
        if not path.exists():
            log.write(f"[red]Archivo no encontrado: {path}[/]")
            return

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            tpl = TemplateLoader.load_from_string(content)
            self._imported_template = tpl
            self.query_one("#json-input", TextArea).text = content
            self._show_import_preview(tpl)
            log.write(f"[green]\u2713 Archivo cargado: {path.name}[/]\n")
        except Exception as e:
            logger.error("Error cargando archivo de plantilla '%s': %s", path_str, e, exc_info=True)
            self._imported_template = None
            log.write(f"[red]Error: {escape(str(e))}[/]")

    def _show_import_preview(self, tpl: TemplateModel) -> None:
        log = self.query_one("#import-preview-log", RichLog)
        tags = ", ".join(tpl.tags) if tpl.tags else "-"
        log.write(f"[bold #00ff41]{tpl.name}[/]")
        log.write(f"Descripción: {tpl.description or '-'}")
        log.write(f"Tags: {tags}")
        log.write(f"Habilidades: {len(tpl.abilities)}\n")
        for i, ab in enumerate(tpl.abilities, 1):
            log.write(
                f"  {i}. {ab.name} — {ab.tactic} ({ab.technique_id})"
            )

    async def _deploy_template(self, tpl: TemplateModel | None, source: str) -> None:
        if not tpl:
            self.notify(f"No hay plantilla {source} seleccionada", severity="warning")
            return

        # Intentar usar el log del panel de importar para progreso detallado
        deploy_log: RichLog | None = None
        try:
            deploy_log = self.query_one("#import-preview-log", RichLog)
            deploy_log.clear()
            deploy_log.write(f"[bold #00ff41]Desplegando '{escape(tpl.name)}'…[/]\n")
        except Exception:
            pass  # En la pestaña builtin no hay log

        self.notify(f"Desplegando '{tpl.name}'...", severity="information")

        def on_progress(msg: str) -> None:
            logger.info("Deploy progress: %s", msg)
            if deploy_log is not None:
                deploy_log.write(f"  {escape(msg)}")

        try:
            adversary, ability_ids = await TemplateLoader.deploy(
                tpl, self.app.client, on_progress=on_progress
            )
            self.app.invalidate_cache()
            logger.info("Plantilla '%s' desplegada: adversario '%s' con %d habilidades", tpl.name, adversary.name, len(ability_ids))
            self.notify(
                f"Adversario '{adversary.name}' creado con {len(ability_ids)} habilidades",
                severity="information",
            )
        except Exception as e:
            logger.error("Error al desplegar plantilla '%s': %s", tpl.name, e, exc_info=True)
            if deploy_log is not None:
                deploy_log.write(f"\n[red]✗ Error: {escape(str(e))}[/]")
            self.notify(f"Error al desplegar: {escape(str(e))}", severity="error")

    def action_refresh(self) -> None:
        self.load_data()
