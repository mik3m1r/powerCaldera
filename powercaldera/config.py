"""Gestión de configuración desde YAML y variables de entorno."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
import sys

import yaml


logger = logging.getLogger(__name__)


@dataclass
class Config:
    server_url: str = "http://localhost:8888"
    api_key: str = ""
    refresh_interval: int = 30
    templates_dir: str | None = None
    log_level: str = "INFO"

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        data: dict = {}
        if path and path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    raw = yaml.safe_load(f) or {}
                if isinstance(raw, dict):
                    server = raw.get("server", {})
                    settings = raw.get("settings", {})
                    data["server_url"] = server.get("url", cls.server_url)
                    data["api_key"] = server.get("api_key", "")
                    data["refresh_interval"] = settings.get("refresh_interval", 30)
                    data["templates_dir"] = settings.get("templates_dir")
                    data["log_level"] = settings.get("log_level", "INFO")
            except yaml.YAMLError as e:
                logger.warning("Invalid YAML config at %s: %s", path, e, exc_info=True)
                print(
                    f"[powerCaldera] Warning: config file '{path}' has invalid YAML: {e}",
                    file=sys.stderr,
                )
            except OSError as e:
                logger.warning("Cannot read config file %s: %s", path, e, exc_info=True)
                print(
                    f"[powerCaldera] Warning: cannot read config file '{path}': {e}",
                    file=sys.stderr,
                )
            except TypeError as e:
                logger.warning("Invalid config data in %s: %s", path, e, exc_info=True)
                print(
                    f"[powerCaldera] Warning: invalid config file '{path}': {e}",
                    file=sys.stderr,
                )
            except Exception as e:
                logger.warning("Unexpected error loading config %s: %s", path, e, exc_info=True)
                print(
                    f"[powerCaldera] Warning: error loading config file '{path}': {e}",
                    file=sys.stderr,
                )

        data["server_url"] = os.environ.get("CALDERA_URL", data.get("server_url", cls.server_url))
        data["api_key"] = os.environ.get("CALDERA_API_KEY", data.get("api_key", ""))
        data["log_level"] = os.environ.get("CALDERA_LOG_LEVEL", data.get("log_level", "INFO"))

        config = cls(**data)
        config._validate()
        return config

    def _validate(self) -> None:
        """Valida la configuración cargada."""
        if not self.api_key:
            logger.warning("No API key configured — connections to Caldera will likely fail")
        if not self.server_url.startswith(("http://", "https://")):
            raise ValueError(
                f"server_url debe empezar con http:// o https://: {self.server_url}"
            )


DEFAULT_CONFIG_PATH = Path.home() / ".powercaldera" / "config.yaml"
