"""Barra de cabecera con título y teclas de navegación."""

from textual.app import ComposeResult
from textual.widgets import Static


NAV_HELP = "[d] Dashboard  [a] Habilidades  [v] Adversarios  [t] Plantillas  [o] Operaciones  [q] Salir"


class HeaderBar(Static):

    DEFAULT_CSS = """
    HeaderBar {
        dock: top;
        height: 3;
        background: #1a1a2e;
        padding: 0 2;
        layout: horizontal;
    }
    """

    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold #00ff41]>> powerCaldera[/]  " + f"[#888]{NAV_HELP}[/]"
        )
