"""Pantalla de Dashboard — resumen de agentes y operaciones."""

from __future__ import annotations

import logging

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.markup import escape
from textual.timer import Timer
from textual.widgets import DataTable, Static, Footer

from ..widgets.header_bar import HeaderBar
from ..widgets.status_bar import StatusBar
from .base import BaseScreen

logger = logging.getLogger(__name__)


class DashboardScreen(BaseScreen):

    BINDINGS = [("r", "refresh", "Refrescar")]

    def __init__(self) -> None:
        super().__init__()
        self._refresh_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield HeaderBar()
        yield Static("[bold #00ff41]--- Dashboard ---[/]", classes="section-title")
        with Vertical(classes="dashboard-section"):
            yield Static("[bold]Agentes Conectados[/]", classes="dashboard-label")
            yield DataTable(id="agents-table")
        with Vertical(classes="dashboard-section"):
            yield Static("[bold]Operaciones[/]", classes="dashboard-label")
            yield DataTable(id="operations-table")
        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        agents_table = self.query_one("#agents-table", DataTable)
        agents_table.add_columns("PAW", "Host", "Plataforma", "Usuario", "Privilegio", "Última Conexión", "Grupo")

        ops_table = self.query_one("#operations-table", DataTable)
        ops_table.add_columns("ID", "Nombre", "Estado", "Adversario", "Inicio", "Fin")

        self.load_data()

        # Auto-refresh wired to config.refresh_interval
        interval = float(getattr(getattr(self.app, "config", None), "refresh_interval", 30))
        self._refresh_timer = self.set_interval(interval, self.load_data)

    async def _load_data(self) -> None:
        try:
            status_bar = self.query_one(StatusBar)
            client = self.app.client
            state = await client.health_check()
            is_connected = state == "connected"
            agents = await client.list_agents() if is_connected else []
            operations = await client.list_operations() if is_connected else []

            status_bar.set_status(
                connected=state,
                server_url=self.app.config.server_url,
                agents=len(agents),
            )

            agents_table = self.query_one("#agents-table", DataTable)
            agents_table.clear()
            for agent in agents:
                agents_table.add_row(
                    agent.paw,
                    agent.host,
                    agent.platform,
                    agent.username,
                    agent.privilege,
                    agent.last_seen[:19] if agent.last_seen else "-",
                    agent.group,
                )

            ops_table = self.query_one("#operations-table", DataTable)
            ops_table.clear()
            for op in operations:
                adv_name = op.adversary.name if op.adversary else "-"
                ops_table.add_row(
                    op.id[:8],
                    op.name,
                    op.state,
                    adv_name,
                    op.start[:19] if op.start else "-",
                    op.finish[:19] if op.finish else "-",
                )

        except Exception as e:
            logger.error("Error cargando dashboard: %s", e, exc_info=True)
            try:
                status_bar = self.query_one(StatusBar)
                status_bar.set_status(connected=False, server_url=self.app.config.server_url)
            except Exception:
                logger.debug("No se pudo actualizar el estado del dashboard", exc_info=True)
            self.notify(f"Error de conexión: {escape(str(e))}", severity="error")

    def action_refresh(self) -> None:
        self.load_data()
