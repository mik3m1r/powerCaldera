"""Modelos Pydantic para objetos de la API de Caldera."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class CalderaBaseModel(BaseModel):
    """Base para modelos de respuesta de la API — ignora campos extra."""

    model_config = ConfigDict(extra="ignore")


class Executor(CalderaBaseModel):
    name: str = ""
    platform: str = ""
    command: Optional[str] = ""
    payloads: list[str] = []

    @field_validator("command", mode="before")
    @classmethod
    def coerce_none_command(cls, v: Any) -> str:
        return v if isinstance(v, str) else ""


class Ability(CalderaBaseModel):
    ability_id: str = ""
    name: str = ""
    description: str = ""
    tactic: str = ""
    technique_id: str = ""
    technique_name: str = ""
    executors: list[Executor] = []
    plugin: str = ""


class Adversary(CalderaBaseModel):
    adversary_id: str = ""
    name: str = ""
    description: str = ""
    atomic_ordering: list[str] = []
    tags: list[str] = []
    plugin: str = ""


class Agent(CalderaBaseModel):
    paw: str = ""
    host: str = ""
    platform: str = ""
    username: str = ""
    privilege: str = ""
    last_seen: str = ""
    trusted: bool = False
    executors: list[str] = []
    group: str = ""


class Operation(CalderaBaseModel):
    id: str = ""
    name: str = ""
    state: str = ""
    adversary: Adversary | None = None
    host_group: list[dict[str, Any]] = []
    start: str = ""
    finish: str = ""
    planner: dict[str, Any] = {}
    source: dict[str, Any] = {}


class OperationLink(CalderaBaseModel):
    id: str = ""
    command: str = ""
    status: int = -1
    paw: str = ""
    ability: dict[str, Any] = {}
    finish: str = ""
    output: str = ""


class Planner(CalderaBaseModel):
    id: str = ""
    name: str = ""
    description: str = ""


class Source(CalderaBaseModel):
    id: str = ""
    name: str = ""
    facts: list[dict[str, Any]] = []


# --- Request models ---

class CreateAbilityRequest(BaseModel):
    ability_id: str
    name: str
    description: str = ""
    tactic: str
    technique_id: str
    technique_name: str
    executors: list[dict[str, Any]]


class CreateAdversaryRequest(BaseModel):
    adversary_id: str
    name: str
    description: str = ""
    atomic_ordering: list[str]
    tags: list[str] = []


class CreateOperationRequest(BaseModel):
    name: str
    adversary: dict[str, Any]
    planner: dict[str, Any]
    source: dict[str, Any]
    group: str = ""
    auto_close: bool = False
    autonomous: int = 1
