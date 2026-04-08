"""Aplicación TUI principal de powerCaldera."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from textual.app import App
from textual.binding import Binding

from .api.client import CalderaClient
from .api.models import Ability
from .config import Config
from .screens.dashboard import DashboardScreen
from .screens.abilities import AbilitiesScreen
from .screens.adversaries import AdversariesScreen
from .screens.operations import OperationsScreen
from .screens.templates_screen import TemplatesScreen

logger = logging.getLogger(__name__)


@dataclass
class AbilitiesCache:
    """Cache de habilidades con TTL, compartida entre pantallas."""

    abilities: list[Ability] = field(default_factory=list)
    ability_map: dict[str, Ability] = field(default_factory=dict)
    _timestamp: float = 0.0
    _ttl: float = 120.0
    _search_index: dict[str, str] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        return bool(self.abilities) and (time.monotonic() - self._timestamp) < self._ttl

    def update(self, abilities: list[Ability]) -> None:
        self.abilities = abilities
        self.ability_map = {ab.ability_id: ab for ab in abilities}
        self._search_index = {
            ab.ability_id: f"{ab.name.lower()} {ab.tactic.lower()} {ab.technique_id.lower()} {ab.technique_name.lower()}"
            for ab in abilities
        }
        self._timestamp = time.monotonic()

    def invalidate(self) -> None:
        self._timestamp = 0.0

    def search(self, query: str) -> list[Ability]:
        q = query.lower()
        return [ab for ab in self.abilities if q in self._search_index.get(ab.ability_id, "")]


class PowerCalderaApp(App):
    TITLE = "powerCaldera"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("d", "switch_mode('dashboard')", "Dashboard", priority=True),
        Binding("a", "switch_mode('abilities')", "Habilidades", priority=True),
        Binding("v", "switch_mode('adversaries')", "Adversarios", priority=True),
        Binding("t", "switch_mode('templates')", "Plantillas", priority=True),
        Binding("o", "switch_mode('operations')", "Operaciones", priority=True),
        Binding("q", "quit", "Salir", priority=True),
    ]

    MODES = {
        "dashboard": DashboardScreen,
        "abilities": AbilitiesScreen,
        "adversaries": AdversariesScreen,
        "templates": TemplatesScreen,
        "operations": OperationsScreen,
    }

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.client = CalderaClient(config.server_url, config.api_key)
        self.abilities_cache = AbilitiesCache()

    async def get_abilities(self, force: bool = False) -> list[Ability]:
        """Retorna habilidades desde cache o API."""
        if not force and self.abilities_cache.is_valid:
            logger.debug("Abilities cache hit (%d items)", len(self.abilities_cache.abilities))
            return self.abilities_cache.abilities
        try:
            abilities = await self.client.list_abilities()
            self.abilities_cache.update(abilities)
            logger.debug("Abilities fetched from API: %d items", len(abilities))
            return abilities
        except Exception as e:
            logger.error("Error fetching abilities: %s", e, exc_info=True)
            return self.abilities_cache.abilities

    def invalidate_cache(self) -> None:
        self.abilities_cache.invalidate()

    async def on_mount(self) -> None:
        self.switch_mode("dashboard")
        # Pre-fetch en background — solo si hay conexión
        try:
            connected = await self.client.health_check()
            if connected:
                logger.info("Conectado a Caldera en %s", self.config.server_url)
                await self.get_abilities()
            else:
                logger.warning("Sin conexión a Caldera en %s al iniciar", self.config.server_url)
        except Exception:
            logger.warning("Error al intentar conectar a Caldera al iniciar", exc_info=True)

    async def action_quit(self) -> None:
        logger.info("Cerrando powerCaldera")
        try:
            await self.client.close()
        except Exception as e:
            logger.warning("Error closing client: %s", e, exc_info=True)
        self.exit()

    def on_exception(self, error: Exception) -> None:
        """Catch-all for unhandled exceptions — log them and show a notification."""
        logger.critical("Unhandled exception in app: %s", error, exc_info=True)
        try:
            from textual.markup import escape

            self.notify(f"Error inesperado: {escape(str(error))}", severity="error", timeout=8)
        except Exception as notify_error:
            logger.error("Failed to notify about unhandled exception: %s", notify_error, exc_info=True)
