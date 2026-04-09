"""Barra de estado inferior con conexión y última actualización."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from textual.widgets import Static

ConnectionState = Literal["connected", "auth_error", "offline"]


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
        self._state: ConnectionState = "offline"
        self._server_url = ""
        self._agents = 0

    def set_status(
        self,
        connected: bool | ConnectionState,
        server_url: str = "",
        agents: int = 0,
    ) -> None:
        """Acepta tanto bool (retrocompatibilidad) como str literal de estado."""
        self._server_url = server_url
        self._agents = agents
        if isinstance(connected, bool):
            self._state = "connected" if connected else "offline"
        else:
            self._state = connected
        self._render_status()

    def _render_status(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        if self._state == "connected":
            icon = "[#00ff41]\u25cf Conectado[/]"
        elif self._state == "auth_error":
            icon = "[#ffaa00]\u25cf Auth fallida — verifica API key[/]"
        else:
            icon = "[#ff4444]\u25cf Desconectado[/]"
        self.update(
            f"{icon}  |  {self._server_url}  |  "
            f"Agentes: {self._agents}  |  {now}"
        )
