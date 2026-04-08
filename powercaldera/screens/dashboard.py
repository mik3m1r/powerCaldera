"""Pantalla de Dashboard — resumen de agentes y operaciones."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Static, Footer

from ..widgets.header_bar import HeaderBar
from ..widgets.status_bar import StatusBar


class DashboardScreen(Screen):

    BINDINGS = [("r", "refresh", "Refrescar")]

    def compose(self) -> ComposeResult:
        yield HeaderBar()
        yield Static("[bold #00ff41]--- Dashboard ---[/]", classes="section-title")
        yield Static("[bold]Agentes Conectados[/]")
        yield DataTable(id="agents-table")
        yield Static("[bold]Operaciones[/]")
        yield DataTable(id="operations-table")
        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        agents_table = self.query_one("#agents-table", DataTable)
        agents_table.add_columns("PAW", "Host", "Plataforma", "Usuario", "Privilegio", "Última Conexión", "Grupo")

        ops_table = self.query_one("#operations-table", DataTable)
        ops_table.add_columns("ID", "Nombre", "Estado", "Adversario", "Inicio", "Fin")

        self.load_data()

    def load_data(self) -> None:
        self.run_worker(self._load_data(), exclusive=True)

    async def _load_data(self) -> None:
        status_bar = self.query_one(StatusBar)
        client = self.app.client

        try:
            connected = await client.health_check()
            agents = await client.list_agents() if connected else []
            operations = await client.list_operations() if connected else []

            status_bar.set_status(
                connected=connected,
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
            status_bar.set_status(connected=False, server_url=self.app.config.server_url)
            self.notify(f"Error de conexión: {e}", severity="error")

    def action_refresh(self) -> None:
        self.load_data()
