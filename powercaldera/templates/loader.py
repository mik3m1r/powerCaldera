"""Carga, validación y despliegue de plantillas JSON."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Callable
from pathlib import Path

from pydantic import ValidationError

from ..api.client import CalderaClient
from ..api.models import CreateAbilityRequest, CreateAdversaryRequest, Adversary
from .models import TemplateModel, TemplateAbility, TemplatePlatforms

logger = logging.getLogger(__name__)


BUILTIN_DIR = Path(__file__).parent / "builtin"


def _generate_id(prefix: str = "pc") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _ability_to_executors(ability: TemplateAbility) -> list[dict]:
    """Convierte TemplatePlatforms a lista de executors para la API de Caldera."""
    executors = []
    for platform_name in ("windows", "linux", "darwin"):
        platform_cmds: dict[str, str] | None = getattr(ability.platforms, platform_name)
        if platform_cmds:
            for executor_name, command in platform_cmds.items():
                executors.append({
                    "name": executor_name,
                    "platform": platform_name,
                    "command": command,
                    "payloads": [],
                })
    return executors


class TemplateLoader:
    def __init__(self, extra_dirs: list[Path] | None = None):
        self._dirs = [BUILTIN_DIR]
        if extra_dirs:
            self._dirs.extend(extra_dirs)

    def list_builtin(self) -> list[tuple[str, TemplateModel]]:
        """Retorna (filename, template) para cada plantilla builtin."""
        results = []
        for d in self._dirs:
            if not d.exists():
                continue
            for f in sorted(d.glob("*.json")):
                try:
                    tpl = self.load_from_file(f)
                    results.append((f.name, tpl))
                except (json.JSONDecodeError, ValidationError, OSError) as e:
                    logger.warning("Skipping invalid template %s: %s", f.name, e)
                    continue
        return results

    @staticmethod
    def load_from_file(path: Path) -> TemplateModel:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return TemplateModel.model_validate(data)

    @staticmethod
    def load_from_string(text: str) -> TemplateModel:
        """Parse and validate a template from a JSON string.

        Raises json.JSONDecodeError or ValidationError on failure.
        """
        data = json.loads(text)
        return TemplateModel.model_validate(data)

    @staticmethod
    def validate(text: str) -> tuple[bool, str]:
        """Valida JSON y retorna (ok, mensaje_error)."""
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            return False, f"JSON inválido: {e}"
        try:
            TemplateModel.model_validate(data)
            return True, ""
        except ValidationError as e:
            errors = []
            for err in e.errors():
                loc = " → ".join(str(l) for l in err["loc"])
                errors.append(f"  {loc}: {err['msg']}")
            return False, "Errores de validación:\n" + "\n".join(errors)

    @staticmethod
    async def deploy(
        template: TemplateModel,
        client: CalderaClient,
        on_progress: Callable[[str], None] | None = None,
    ) -> tuple[Adversary, list[str]]:
        """Despliega una plantilla: crea abilities y adversario.

        Args:
            template:    La plantilla a desplegar.
            client:      Cliente de la API de Caldera.
            on_progress: Callback opcional llamado en cada paso con un mensaje descriptivo.

        Returns:
            (adversary_creado, lista_de_ability_ids_creados)
        """
        created_ability_ids: list[str] = []
        total = len(template.abilities)
        logger.info("Deploying template '%s' (%d abilities)", template.name, total)

        def _progress(msg: str) -> None:
            if on_progress:
                on_progress(msg)

        try:
            for i, ability in enumerate(template.abilities, 1):
                _progress(f"Creando habilidad {i}/{total}: {ability.name}…")
                aid = _generate_id("pc-ab")
                req = CreateAbilityRequest(
                    ability_id=aid,
                    name=ability.name,
                    description=ability.description,
                    tactic=ability.tactic,
                    technique_id=ability.technique_id,
                    technique_name=ability.technique_name,
                    executors=_ability_to_executors(ability),
                )
                await client.create_ability(req)
                created_ability_ids.append(aid)

            _progress(f"Creando adversario '{template.name}'…")
            adv_req = CreateAdversaryRequest(
                adversary_id=_generate_id("pc-adv"),
                name=template.name,
                description=template.description,
                atomic_ordering=created_ability_ids,
                tags=template.tags,
            )
            adversary = await client.create_adversary(adv_req)
            _progress(f"✓ Despliegue completado: '{adversary.name}' con {len(created_ability_ids)} habilidades.")
            return adversary, created_ability_ids

        except Exception:
            logger.error("Deploy failed for '%s', rolling back %d abilities", template.name, len(created_ability_ids), exc_info=True)
            if created_ability_ids:
                _progress(f"Error — revirtiendo {len(created_ability_ids)} habilidades creadas…")
            rollback_errors = []
            for aid in created_ability_ids:
                try:
                    await client.delete_ability(aid)
                except Exception as rb_err:
                    logger.warning("Rollback: failed to delete ability %s", aid, exc_info=True)
                    rollback_errors.append(str(rb_err))
            if rollback_errors:
                _progress(f"⚠ Rollback parcial — {len(rollback_errors)} habilidades no eliminadas.")
            raise
