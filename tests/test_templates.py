"""Tests para TemplateLoader, modelos de plantilla y deploy."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from powercaldera.templates.models import (
    TemplateAbility,
    TemplateModel,
    TemplatePlatforms,
)
from powercaldera.templates.loader import TemplateLoader, BUILTIN_DIR


# --- TemplateModel validation ---

class TestTemplateModelValidation:
    def test_template_valido(self, valid_template_json):
        tpl = TemplateModel.model_validate(valid_template_json)
        assert tpl.name == "Test Template"
        assert len(tpl.abilities) == 2
        assert tpl.tags == ["test"]

    def test_tactica_invalida(self, valid_template_json):
        valid_template_json["abilities"][0]["tactic"] = "hacking"
        with pytest.raises(ValidationError, match="no válida"):
            TemplateModel.model_validate(valid_template_json)

    def test_technique_id_sin_t(self, valid_template_json):
        valid_template_json["abilities"][0]["technique_id"] = "1082"
        with pytest.raises(ValidationError, match="empezar con 'T'"):
            TemplateModel.model_validate(valid_template_json)

    def test_executor_invalido(self, valid_template_json):
        valid_template_json["abilities"][0]["platforms"]["windows"] = {"python": "print('hi')"}
        with pytest.raises(ValidationError, match="no válido"):
            TemplateModel.model_validate(valid_template_json)

    def test_abilities_vacio(self):
        with pytest.raises(ValidationError, match="al menos una habilidad"):
            TemplateModel.model_validate({
                "name": "Empty", "abilities": [],
            })

    def test_campos_opcionales_default(self):
        tpl = TemplateModel.model_validate({
            "name": "Minimal",
            "abilities": [{
                "name": "x", "tactic": "discovery",
                "technique_id": "T1", "technique_name": "x",
                "platforms": {"linux": {"sh": "ls"}},
            }],
        })
        assert tpl.description == ""
        assert tpl.tags == []
        assert tpl.abilities[0].description == ""

    def test_plataforma_no_dict(self, valid_template_json):
        valid_template_json["abilities"][0]["platforms"]["windows"] = "not a dict"
        with pytest.raises(ValidationError):
            TemplateModel.model_validate(valid_template_json)

    def test_todas_plataformas_none_es_valido(self):
        tpl = TemplateModel.model_validate({
            "name": "x",
            "abilities": [{
                "name": "x", "tactic": "discovery",
                "technique_id": "T1", "technique_name": "x",
                "platforms": {},
            }],
        })
        assert tpl.abilities[0].platforms.windows is None


# --- TemplateLoader.load_from_file ---

class TestLoadFromFile:
    def test_carga_builtin_real(self):
        path = BUILTIN_DIR / "discovery_recon.json"
        tpl = TemplateLoader.load_from_file(path)
        assert tpl.name == "Reconocimiento y Descubrimiento"
        assert len(tpl.abilities) == 6

    def test_archivo_inexistente(self):
        with pytest.raises(FileNotFoundError):
            TemplateLoader.load_from_file(Path("/no/existe.json"))

    def test_json_invalido(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            TemplateLoader.load_from_file(bad)

    def test_json_valido_schema_invalido(self, tmp_path):
        bad = tmp_path / "bad_schema.json"
        bad.write_text('{"name": "x", "abilities": []}', encoding="utf-8")
        with pytest.raises(ValidationError):
            TemplateLoader.load_from_file(bad)


# --- TemplateLoader.load_from_string ---

class TestLoadFromString:
    def test_string_valido(self, valid_template_json):
        text = json.dumps(valid_template_json)
        tpl = TemplateLoader.load_from_string(text)
        assert tpl.name == "Test Template"

    def test_string_invalido(self):
        with pytest.raises(json.JSONDecodeError):
            TemplateLoader.load_from_string("{broken")


# --- TemplateLoader.validate ---

class TestValidate:
    def test_json_valido(self, valid_template_json):
        ok, msg = TemplateLoader.validate(json.dumps(valid_template_json))
        assert ok is True
        assert msg == ""

    def test_json_roto(self):
        ok, msg = TemplateLoader.validate("{broken")
        assert ok is False
        assert "JSON inválido" in msg

    def test_schema_invalido(self):
        ok, msg = TemplateLoader.validate('{"name":"x","abilities":[]}')
        assert ok is False
        assert "Errores de validación" in msg


# --- TemplateLoader.list_builtin ---

class TestListBuiltin:
    def test_retorna_6_plantillas(self):
        loader = TemplateLoader()
        builtin = loader.list_builtin()
        assert len(builtin) == 6
        names = [tpl.name for _, tpl in builtin]
        assert "Reconocimiento y Descubrimiento" in names
        assert "Simulación de Ransomware" in names

    def test_con_directorio_extra_vacio(self, tmp_path):
        loader = TemplateLoader(extra_dirs=[tmp_path])
        builtin = loader.list_builtin()
        assert len(builtin) == 6  # solo builtins, extra está vacío

    def test_ignora_json_invalido_en_directorio(self, tmp_path):
        (tmp_path / "bad.json").write_text("{invalid", encoding="utf-8")
        loader = TemplateLoader(extra_dirs=[tmp_path])
        builtin = loader.list_builtin()
        assert len(builtin) == 6  # ignora el archivo malo


# --- TemplateLoader.deploy ---

class TestDeploy:
    @pytest.mark.asyncio
    async def test_deploy_crea_abilities_y_adversario(self, valid_template_json):
        tpl = TemplateModel.model_validate(valid_template_json)
        mock_client = AsyncMock()
        mock_client.create_ability = AsyncMock(side_effect=[
            MagicMock(ability_id="ab-1"),
            MagicMock(ability_id="ab-2"),
        ])
        mock_client.create_adversary = AsyncMock(
            return_value=MagicMock(name="Test Template", adversary_id="adv-1")
        )

        adversary, ability_ids = await TemplateLoader.deploy(tpl, mock_client)

        assert mock_client.create_ability.call_count == 2
        assert mock_client.create_adversary.call_count == 1
        assert len(ability_ids) == 2

        # Verificar que atomic_ordering contiene los IDs generados
        adv_call = mock_client.create_adversary.call_args
        req = adv_call[0][0]
        assert len(req.atomic_ordering) == 2

    @pytest.mark.asyncio
    async def test_deploy_rollback_si_falla(self, valid_template_json):
        """Si falla la segunda ability, debe eliminar la primera."""
        tpl = TemplateModel.model_validate(valid_template_json)
        mock_client = AsyncMock()
        mock_client.create_ability = AsyncMock(side_effect=[
            MagicMock(ability_id="ab-1"),  # primera OK
            Exception("API Error"),  # segunda falla
        ])
        mock_client.delete_ability = AsyncMock()

        with pytest.raises(Exception, match="API Error"):
            await TemplateLoader.deploy(tpl, mock_client)

        # Debe haber intentado eliminar la ability creada
        mock_client.delete_ability.assert_called_once()


# --- _ability_to_executors helper ---

class TestAbilityToExecutors:
    def test_conversion_multiplatforma(self):
        from powercaldera.templates.loader import _ability_to_executors
        ab = TemplateAbility(
            name="x", tactic="discovery", technique_id="T1",
            technique_name="x",
            platforms=TemplatePlatforms(
                windows={"psh": "whoami", "cmd": "whoami"},
                linux={"sh": "id"},
            ),
        )
        executors = _ability_to_executors(ab)
        assert len(executors) == 3
        platforms = [e["platform"] for e in executors]
        assert "windows" in platforms
        assert "linux" in platforms

    def test_plataforma_unica(self):
        from powercaldera.templates.loader import _ability_to_executors
        ab = TemplateAbility(
            name="x", tactic="discovery", technique_id="T1",
            technique_name="x",
            platforms=TemplatePlatforms(linux={"sh": "ls"}),
        )
        executors = _ability_to_executors(ab)
        assert len(executors) == 1
        assert executors[0]["platform"] == "linux"
        assert executors[0]["name"] == "sh"
