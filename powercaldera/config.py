"""Gestión de configuración desde YAML y variables de entorno."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Config:
    server_url: str = "http://localhost:8888"
    api_key: str = ""
    refresh_interval: int = 30
    templates_dir: str | None = None

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        data: dict = {}
        if path and path.exists():
            with open(path, encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            server = raw.get("server", {})
            settings = raw.get("settings", {})
            data["server_url"] = server.get("url", cls.server_url)
            data["api_key"] = server.get("api_key", "")
            data["refresh_interval"] = settings.get("refresh_interval", 30)
            data["templates_dir"] = settings.get("templates_dir")

        data["server_url"] = os.environ.get("CALDERA_URL", data.get("server_url", cls.server_url))
        data["api_key"] = os.environ.get("CALDERA_API_KEY", data.get("api_key", ""))
        return cls(**data)


DEFAULT_CONFIG_PATH = Path.home() / ".powercaldera" / "config.yaml"
