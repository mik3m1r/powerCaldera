"""Modelos Pydantic para plantillas JSON de adversarios."""

from __future__ import annotations

from pydantic import BaseModel, field_validator

VALID_TACTICS = [
    "reconnaissance", "resource-development", "initial-access", "execution",
    "persistence", "privilege-escalation", "defense-evasion", "credential-access",
    "discovery", "lateral-movement", "collection", "command-and-control",
    "exfiltration", "impact",
]

VALID_EXECUTORS = ["psh", "cmd", "sh", "bash", "pwsh"]
VALID_PLATFORMS = ["windows", "linux", "darwin"]


class TemplatePlatforms(BaseModel):
    """Comandos por plataforma. Clave = nombre del ejecutor, valor = comando."""
    windows: dict[str, str] | None = None
    linux: dict[str, str] | None = None
    darwin: dict[str, str] | None = None

    @field_validator("windows", "linux", "darwin", mode="before")
    @classmethod
    def validate_executors(cls, v):
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("Debe ser un diccionario executor→comando")
        for key in v:
            if key not in VALID_EXECUTORS:
                raise ValueError(
                    f"Ejecutor '{key}' no válido. Usar: {', '.join(VALID_EXECUTORS)}"
                )
        return v


class TemplateAbility(BaseModel):
    name: str
    tactic: str
    technique_id: str
    technique_name: str
    description: str = ""
    platforms: TemplatePlatforms

    @field_validator("tactic")
    @classmethod
    def validate_tactic(cls, v):
        if v not in VALID_TACTICS:
            raise ValueError(
                f"Táctica '{v}' no válida. Usar: {', '.join(VALID_TACTICS)}"
            )
        return v

    @field_validator("technique_id")
    @classmethod
    def validate_technique_id(cls, v):
        if not v.startswith("T"):
            raise ValueError("technique_id debe empezar con 'T' (ej: T1082)")
        return v


class TemplateModel(BaseModel):
    name: str
    description: str = ""
    tags: list[str] = []
    abilities: list[TemplateAbility]

    @field_validator("abilities")
    @classmethod
    def at_least_one_ability(cls, v):
        if not v:
            raise ValueError("Debe incluir al menos una habilidad")
        return v
