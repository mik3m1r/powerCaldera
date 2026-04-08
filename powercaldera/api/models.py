"""Modelos Pydantic para objetos de la API de Caldera."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Executor(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = ""
    platform: str = ""
    command: str = ""
    payloads: list[str] = []


class Ability(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ability_id: str = ""
    name: str = ""
    description: str = ""
    tactic: str = ""
    technique_id: str = ""
    technique_name: str = ""
    executors: list[Executor] = []
    plugin: str = ""


class Adversary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    adversary_id: str = ""
    name: str = ""
    description: str = ""
    atomic_ordering: list[str] = []
    tags: list[str] = []
    plugin: str = ""


class Agent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    paw: str = ""
    host: str = ""
    platform: str = ""
    username: str = ""
    privilege: str = ""
    last_seen: str = ""
    trusted: bool = False
    executors: list[str] = []
    group: str = ""


class Operation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = ""
    name: str = ""
    state: str = ""
    adversary: Adversary | None = None
    host_group: list[dict] = []
    start: str = ""
    finish: str = ""
    planner: dict = {}
    source: dict = {}


class OperationLink(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = ""
    command: str = ""
    status: int = -1
    paw: str = ""
    ability: dict = {}
    finish: str = ""
    output: str = ""


class Planner(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = ""
    name: str = ""
    description: str = ""


class Source(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = ""
    name: str = ""
    facts: list[dict] = []


# --- Request models ---

class CreateAbilityRequest(BaseModel):
    ability_id: str
    name: str
    description: str = ""
    tactic: str
    technique_id: str
    technique_name: str
    executors: list[dict]


class CreateAdversaryRequest(BaseModel):
    adversary_id: str
    name: str
    description: str = ""
    atomic_ordering: list[str]
    tags: list[str] = []


class CreateOperationRequest(BaseModel):
    name: str
    adversary: dict
    planner: dict
    source: dict
    group: str = ""
    auto_close: bool = False
    autonomous: int = 1
