"""Tests para carga de configuración."""

from pathlib import Path

import pytest

from powercaldera.config import Config


class TestConfigLoad:
    def test_yaml_completo(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(
            "server:\n"
            "  url: 'http://caldera:9999'\n"
            "  api_key: 'SECRET'\n"
            "settings:\n"
            "  refresh_interval: 60\n"
            "  templates_dir: '/custom/templates'\n",
            encoding="utf-8",
        )
        config = Config.load(cfg_file)
        assert config.server_url == "http://caldera:9999"
        assert config.api_key == "SECRET"
        assert config.refresh_interval == 60
        assert config.templates_dir == "/custom/templates"

    def test_archivo_faltante(self, tmp_path):
        config = Config.load(tmp_path / "no_existe.yaml")
        assert config.server_url == "http://localhost:8888"
        assert config.api_key == ""
        assert config.refresh_interval == 30

    def test_path_none(self):
        config = Config.load(None)
        assert config.server_url == "http://localhost:8888"
        assert config.api_key == ""

    def test_yaml_parcial_solo_url(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(
            "server:\n  url: 'http://custom:1234'\n",
            encoding="utf-8",
        )
        config = Config.load(cfg_file)
        assert config.server_url == "http://custom:1234"
        assert config.api_key == ""
        assert config.refresh_interval == 30

    def test_yaml_vacio(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("", encoding="utf-8")
        config = Config.load(cfg_file)
        assert config.server_url == "http://localhost:8888"
        assert config.api_key == ""

    def test_env_var_override_url(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(
            "server:\n  url: 'http://from-file:8888'\n  api_key: 'file-key'\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("CALDERA_URL", "http://from-env:9999")
        config = Config.load(cfg_file)
        assert config.server_url == "http://from-env:9999"
        assert config.api_key == "file-key"

    def test_env_var_override_api_key(self, monkeypatch):
        monkeypatch.setenv("CALDERA_API_KEY", "env-secret")
        config = Config.load(None)
        assert config.api_key == "env-secret"

    def test_env_vars_sin_archivo(self, monkeypatch):
        monkeypatch.setenv("CALDERA_URL", "http://env-only:5555")
        monkeypatch.setenv("CALDERA_API_KEY", "env-key")
        config = Config.load(None)
        assert config.server_url == "http://env-only:5555"
        assert config.api_key == "env-key"
