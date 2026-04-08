"""Tests para modelos Pydantic de la API de Caldera."""

import pytest
from pydantic import ValidationError

from powercaldera.api.models import (
    Ability,
    Adversary,
    Agent,
    CreateAbilityRequest,
    CreateAdversaryRequest,
    CreateOperationRequest,
    Executor,
    Operation,
    OperationLink,
    Planner,
    Source,
)


# --- Executor ---

class TestExecutor:
    def test_parse_completo(self, sample_executor_json):
        ex = Executor.model_validate(sample_executor_json)
        assert ex.name == "psh"
        assert ex.platform == "windows"
        assert ex.command == "whoami"
        assert ex.payloads == []

    def test_ignora_campos_extra(self, sample_executor_json):
        """Caldera envía campos extra que nuestro modelo no define."""
        ex = Executor.model_validate(sample_executor_json)
        assert not hasattr(ex, "code")
        assert not hasattr(ex, "language")

    def test_defaults_vacios(self):
        ex = Executor.model_validate({})
        assert ex.name == ""
        assert ex.platform == ""
        assert ex.command == ""
        assert ex.payloads == []


# --- Ability ---

class TestAbility:
    def test_parse_respuesta_api_real(self, sample_ability_json):
        ab = Ability.model_validate(sample_ability_json)
        assert ab.ability_id == "abc-123-def"
        assert ab.name == "Test Ability"
        assert ab.tactic == "discovery"
        assert ab.technique_id == "T1082"
        assert len(ab.executors) == 1
        assert ab.executors[0].name == "psh"

    def test_ignora_campos_extra_api(self, sample_ability_json):
        ab = Ability.model_validate(sample_ability_json)
        assert not hasattr(ab, "access")
        assert not hasattr(ab, "buckets")
        assert not hasattr(ab, "requirements")
        assert not hasattr(ab, "singleton")

    def test_executors_vacio(self):
        ab = Ability.model_validate({
            "ability_id": "x", "name": "x", "tactic": "discovery",
            "technique_id": "T1", "technique_name": "x", "executors": [],
        })
        assert ab.executors == []

    def test_campos_opcionales_faltantes(self):
        ab = Ability.model_validate({"ability_id": "x", "name": "x"})
        assert ab.description == ""
        assert ab.plugin == ""
        assert ab.executors == []


# --- Adversary ---

class TestAdversary:
    def test_parse_completo(self, sample_adversary_json):
        adv = Adversary.model_validate(sample_adversary_json)
        assert adv.adversary_id == "adv-001"
        assert adv.name == "Test Adversary"
        assert len(adv.atomic_ordering) == 2
        assert adv.tags == ["test", "discovery"]

    def test_ignora_campos_extra(self, sample_adversary_json):
        adv = Adversary.model_validate(sample_adversary_json)
        assert not hasattr(adv, "objective")

    def test_listas_vacias(self):
        adv = Adversary.model_validate({"adversary_id": "x", "name": "x"})
        assert adv.atomic_ordering == []
        assert adv.tags == []


# --- Agent ---

class TestAgent:
    def test_parse_completo(self, sample_agent_json):
        agent = Agent.model_validate(sample_agent_json)
        assert agent.paw == "abcdef"
        assert agent.host == "WORKSTATION-01"
        assert agent.platform == "windows"
        assert agent.trusted is True
        assert agent.group == "red"

    def test_ignora_campos_extra(self, sample_agent_json):
        agent = Agent.model_validate(sample_agent_json)
        assert not hasattr(agent, "contact")
        assert not hasattr(agent, "architecture")
        assert not hasattr(agent, "pid")

    def test_trusted_false(self):
        agent = Agent.model_validate({"paw": "x", "trusted": False})
        assert agent.trusted is False

    def test_defaults(self):
        agent = Agent.model_validate({})
        assert agent.paw == ""
        assert agent.trusted is False
        assert agent.executors == []


# --- Operation ---

class TestOperation:
    def test_parse_completo(self, sample_operation_json):
        op = Operation.model_validate(sample_operation_json)
        assert op.id == "op-001-uuid"
        assert op.name == "Test Operation"
        assert op.state == "running"
        assert op.adversary is not None
        assert op.adversary.name == "Test Adversary"

    def test_adversary_none(self):
        op = Operation.model_validate({
            "id": "x", "name": "x", "state": "running", "adversary": None,
        })
        assert op.adversary is None

    def test_ignora_campos_extra(self, sample_operation_json):
        op = Operation.model_validate(sample_operation_json)
        assert not hasattr(op, "chain")
        assert not hasattr(op, "autonomous")

    def test_defaults(self):
        op = Operation.model_validate({})
        assert op.start == ""
        assert op.finish == ""
        assert op.host_group == []


# --- OperationLink ---

class TestOperationLink:
    def test_parse_completo(self, sample_operation_link_json):
        link = OperationLink.model_validate(sample_operation_link_json)
        assert link.id == "link-001"
        assert link.status == 0
        assert link.paw == "abcdef"
        assert link.ability["name"] == "Test Ability"

    def test_status_pendiente(self):
        link = OperationLink.model_validate({"id": "x", "status": -1})
        assert link.status == -1

    def test_ability_vacio(self):
        link = OperationLink.model_validate({"id": "x", "ability": {}})
        assert link.ability == {}


# --- Planner / Source ---

class TestPlanner:
    def test_parse(self, sample_planner_json):
        p = Planner.model_validate(sample_planner_json)
        assert p.id == "atomic"
        assert p.name == "atomic"


class TestSource:
    def test_parse(self, sample_source_json):
        s = Source.model_validate(sample_source_json)
        assert s.id == "basic"
        assert len(s.facts) == 1


# --- Request Models ---

class TestRequestModels:
    def test_create_ability_dump(self):
        req = CreateAbilityRequest(
            ability_id="test-id",
            name="Test",
            tactic="discovery",
            technique_id="T1082",
            technique_name="System Info",
            executors=[{"name": "psh", "platform": "windows", "command": "whoami"}],
        )
        d = req.model_dump()
        assert d["ability_id"] == "test-id"
        assert d["tactic"] == "discovery"
        assert len(d["executors"]) == 1

    def test_create_ability_campo_requerido_faltante(self):
        with pytest.raises(ValidationError):
            CreateAbilityRequest(
                ability_id="test-id",
                # name faltante
                tactic="discovery",
                technique_id="T1082",
                technique_name="System Info",
                executors=[],
            )

    def test_create_adversary_dump(self):
        req = CreateAdversaryRequest(
            adversary_id="adv-id",
            name="Test Adv",
            atomic_ordering=["ab1", "ab2"],
            tags=["test"],
        )
        d = req.model_dump()
        assert d["atomic_ordering"] == ["ab1", "ab2"]
        assert d["tags"] == ["test"]

    def test_create_operation_dump(self):
        req = CreateOperationRequest(
            name="Op Test",
            adversary={"adversary_id": "adv-1"},
            planner={"id": "atomic"},
            source={"id": "basic"},
        )
        d = req.model_dump()
        assert d["name"] == "Op Test"
        assert d["adversary"]["adversary_id"] == "adv-1"
