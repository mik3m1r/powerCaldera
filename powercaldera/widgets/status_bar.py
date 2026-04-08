"""Barra de estado inferior con conexión y última actualización."""

from __future__ import annotations

from datetime import datetime

from textual.widgets import Static


class StatusBar(Static):

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: #16213e;
        color: #aaa;
        padding: 0 2;
    }
    """

    def __init__(self) -> None:
        super().__init__("")
        self._connected = False
        self._server_url = ""
        self._agents = 0

    def set_status(
        self, connected: bool, server_url: str = "", agents: int = 0
    ) -> None:
        self._connected = connected
        self._server_url = server_url
        self._agents = agents
        self._render_status()

    def _render_status(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        if self._connected:
            icon = "[#00ff41]\u25cf Conectado[/]"
        else:
            icon = "[#ff4444]\u25cf Desconectado[/]"
        self.update(
            f"{icon}  |  {self._server_url}  |  "
            f"Agentes: {self._agents}  |  {now}"
        )
