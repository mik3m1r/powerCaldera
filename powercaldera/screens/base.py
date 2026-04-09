"""Clase base para pantallas con patrones comunes."""

from __future__ import annotations

import logging

from textual.screen import Screen

logger = logging.getLogger(__name__)


class BaseScreen(Screen):
    """Pantalla base con utilidades compartidas."""

    def load_data(self) -> None:
        self.run_worker(self._load_data(), exclusive=True)

    async def _load_data(self) -> None:
        raise NotImplementedError

    async def _check_connection(self) -> bool:
        """Health check + notificación si falla. Retorna True si conectado."""
        state = await self.app.client.health_check()
        if state == "connected":
            return True
        if state == "auth_error":
            logger.warning("%s: error de autenticación con Caldera", self.__class__.__name__)
            self.notify(
                "Error de autenticación. Verifica tu API key en la configuración.",
                severity="error",
                timeout=8,
            )
        else:
            logger.warning("%s: sin conexión a Caldera", self.__class__.__name__)
            self.notify(
                "Sin conexión con Caldera. Verifica URL y API key ([r] para reintentar).",
                severity="warning",
                timeout=8,
            )
        return False
