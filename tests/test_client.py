"""Tests para CalderaClient con respuestas HTTP mockeadas."""

import pytest
import respx
from httpx import Response, ConnectError, Request

from powercaldera.api.client import CalderaClient, CalderaAPIError
from powercaldera.api.models import (
    Ability, Adversary, Agent, Operation, OperationLink, Planner, Source,
    CreateAbilityRequest, CreateAdversaryRequest, CreateOperationRequest,
)


BASE = "http://testserver"


# --- health_check ---

class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_200_returns_true(self):
        async with respx.mock(base_url=BASE) as mock:
            mock.get("/api/v2/health").mock(return_value=Response(200))
            client = CalderaClient(BASE, "key")
            assert await client.health_check() is True
            await client.close()

    @pytest.mark.asyncio
    async def test_health_endpoint_ausente_fallback_agents(self):
        """Si /health no existe (404), usa /agents como fallback."""
        async with respx.mock(base_url=BASE) as mock:
            mock.get("/api/v2/health").mock(return_value=Response(404))
            mock.get("/api/v2/agents").mock(return_value=Response(200, json=[]))
            client = CalderaClient(BASE, "key")
            assert await client.health_check() is True
            await client.close()

    @pytest.mark.asyncio
    async def test_health_500_fallback_agents_falla(self):
        """Si /health devuelve 500 y /agents también falla, devuelve False."""
        async with respx.mock(base_url=BASE) as mock:
            mock.get("/api/v2/health").mock(return_value=Response(500))
            mock.get("/api/v2/agents").mock(return_value=Response(500))
            client = CalderaClient(BASE, "key")
            assert await client.health_check() is False
            await client.close()

    @pytest.mark.asyncio
    async def test_health_connect_error_returns_false(self):
        async with respx.mock(base_url=BASE) as mock:
            mock.get("/api/v2/health").mock(
                side_effect=ConnectError("Connection refused", request=Request("GET", f"{BASE}/api/v2/health"))
            )
            client = CalderaClient(BASE, "key")
            assert await client.health_check() is False
            await client.close()


# --- list endpoints ---

class TestListAbilities:
    @pytest.mark.asyncio
    async def test_retorna_lista_modelos(self, sample_ability_json):
        async with respx.mock(base_url=BASE) as mock:
            mock.get("/api/v2/abilities").mock(
                return_value=Response(200, json=[sample_ability_json, sample_ability_json])
            )
            client = CalderaClient(BASE, "key")
            result = await client.list_abilities()
            assert len(result) == 2
            assert all(isinstance(a, Ability) for a in result)
            assert result[0].name == "Test Ability"
            await client.close()

    @pytest.mark.asyncio
    async def test_lista_vacia(self):
        async with respx.mock(base_url=BASE) as mock:
            mock.get("/api/v2/abilities").mock(return_value=Response(200, json=[]))
            client = CalderaClient(BASE, "key")
            result = await client.list_abilities()
            assert result == []
            await client.close()

    @pytest.mark.asyncio
    async def test_error_401(self):
        async with respx.mock(base_url=BASE) as mock:
            mock.get("/api/v2/abilities").mock(
                return_value=Response(401, text="Unauthorized")
            )
            client = CalderaClient(BASE, "key")
            with pytest.raises(CalderaAPIError) as exc_info:
                await client.list_abilities()
            assert exc_info.value.status_code == 401
            await client.close()


class TestListAgents:
    @pytest.mark.asyncio
    async def test_retorna_agentes(self, sample_agent_json):
        async with respx.mock(base_url=BASE) as mock:
            mock.get("/api/v2/agents").mock(
                return_value=Response(200, json=[sample_agent_json])
            )
            client = CalderaClient(BASE, "key")
            result = await client.list_agents()
            assert len(result) == 1
            assert isinstance(result[0], Agent)
            assert result[0].paw == "abcdef"
            await client.close()


class TestListAdversaries:
    @pytest.mark.asyncio
    async def test_retorna_adversarios(self, sample_adversary_json):
        async with respx.mock(base_url=BASE) as mock:
            mock.get("/api/v2/adversaries").mock(
                return_value=Response(200, json=[sample_adversary_json])
            )
            client = CalderaClient(BASE, "key")
            result = await client.list_adversaries()
            assert len(result) == 1
            assert isinstance(result[0], Adversary)
            await client.close()


class TestListOperations:
    @pytest.mark.asyncio
    async def test_retorna_operaciones(self, sample_operation_json):
        async with respx.mock(base_url=BASE) as mock:
            mock.get("/api/v2/operations").mock(
                return_value=Response(200, json=[sample_operation_json])
            )
            client = CalderaClient(BASE, "key")
            result = await client.list_operations()
            assert len(result) == 1
            assert isinstance(result[0], Operation)
            assert result[0].state == "running"
            await client.close()


# --- create endpoints ---

class TestCreateAbility:
    @pytest.mark.asyncio
    async def test_crea_ability_ok(self, sample_ability_json):
        async with respx.mock(base_url=BASE) as mock:
            mock.post("/api/v2/abilities").mock(
                return_value=Response(200, json=sample_ability_json)
            )
            client = CalderaClient(BASE, "key")
            req = CreateAbilityRequest(
                ability_id="abc-123-def",
                name="Test Ability",
                tactic="discovery",
                technique_id="T1082",
                technique_name="System Information Discovery",
                executors=[{"name": "psh", "platform": "windows", "command": "whoami"}],
            )
            result = await client.create_ability(req)
            assert isinstance(result, Ability)
            assert result.ability_id == "abc-123-def"
            await client.close()

    @pytest.mark.asyncio
    async def test_error_400(self):
        async with respx.mock(base_url=BASE) as mock:
            mock.post("/api/v2/abilities").mock(
                return_value=Response(400, text="Bad Request: missing fields")
            )
            client = CalderaClient(BASE, "key")
            req = CreateAbilityRequest(
                ability_id="x", name="x", tactic="x",
                technique_id="x", technique_name="x", executors=[],
            )
            with pytest.raises(CalderaAPIError) as exc_info:
                await client.create_ability(req)
            assert exc_info.value.status_code == 400
            await client.close()


class TestCreateAdversary:
    @pytest.mark.asyncio
    async def test_crea_adversario_ok(self, sample_adversary_json):
        async with respx.mock(base_url=BASE) as mock:
            mock.post("/api/v2/adversaries").mock(
                return_value=Response(200, json=sample_adversary_json)
            )
            client = CalderaClient(BASE, "key")
            req = CreateAdversaryRequest(
                adversary_id="adv-001",
                name="Test Adversary",
                atomic_ordering=["abc-123", "def-456"],
            )
            result = await client.create_adversary(req)
            assert isinstance(result, Adversary)
            await client.close()


class TestCreateOperation:
    @pytest.mark.asyncio
    async def test_crea_operacion_ok(self, sample_operation_json):
        async with respx.mock(base_url=BASE) as mock:
            mock.post("/api/v2/operations").mock(
                return_value=Response(200, json=sample_operation_json)
            )
            client = CalderaClient(BASE, "key")
            req = CreateOperationRequest(
                name="Test Op",
                adversary={"adversary_id": "adv-001"},
                planner={"id": "atomic"},
                source={"id": "basic"},
            )
            result = await client.create_operation(req)
            assert isinstance(result, Operation)
            assert result.name == "Test Operation"
            await client.close()


# --- delete endpoints ---

class TestDeleteAbility:
    @pytest.mark.asyncio
    async def test_delete_ok(self):
        async with respx.mock(base_url=BASE) as mock:
            mock.delete("/api/v2/abilities/abc-123").mock(
                return_value=Response(204)
            )
            client = CalderaClient(BASE, "key")
            await client.delete_ability("abc-123")  # no exception
            await client.close()

    @pytest.mark.asyncio
    async def test_delete_404(self):
        async with respx.mock(base_url=BASE) as mock:
            mock.delete("/api/v2/abilities/not-found").mock(
                return_value=Response(404, text="Not found")
            )
            client = CalderaClient(BASE, "key")
            with pytest.raises(CalderaAPIError) as exc_info:
                await client.delete_ability("not-found")
            assert exc_info.value.status_code == 404
            await client.close()


# --- operation control ---

class TestOperationControl:
    @pytest.mark.asyncio
    async def test_get_operation_links(self, sample_operation_link_json):
        async with respx.mock(base_url=BASE) as mock:
            mock.get("/api/v2/operations/op-1/links").mock(
                return_value=Response(200, json=[sample_operation_link_json])
            )
            client = CalderaClient(BASE, "key")
            links = await client.get_operation_links("op-1")
            assert len(links) == 1
            assert isinstance(links[0], OperationLink)
            assert links[0].status == 0
            await client.close()

    @pytest.mark.asyncio
    async def test_update_operation_state(self):
        async with respx.mock(base_url=BASE) as mock:
            mock.patch("/api/v2/operations/op-1").mock(
                return_value=Response(200, json={})
            )
            client = CalderaClient(BASE, "key")
            await client.update_operation_state("op-1", "paused")  # no exception
            await client.close()

    @pytest.mark.asyncio
    async def test_get_operation_report(self):
        report = {"steps": {"abc": [{"ability_id": "x", "status": 0}]}}
        async with respx.mock(base_url=BASE) as mock:
            mock.post("/api/v2/operations/op-1/report").mock(
                return_value=Response(200, json=report)
            )
            client = CalderaClient(BASE, "key")
            result = await client.get_operation_report("op-1")
            assert "steps" in result
            assert "abc" in result["steps"]
            await client.close()


# --- planners / sources ---

class TestPlannersSources:
    @pytest.mark.asyncio
    async def test_list_planners(self, sample_planner_json):
        async with respx.mock(base_url=BASE) as mock:
            mock.get("/api/v2/planners").mock(
                return_value=Response(200, json=[sample_planner_json])
            )
            client = CalderaClient(BASE, "key")
            result = await client.list_planners()
            assert len(result) == 1
            assert isinstance(result[0], Planner)
            await client.close()

    @pytest.mark.asyncio
    async def test_list_sources(self, sample_source_json):
        async with respx.mock(base_url=BASE) as mock:
            mock.get("/api/v2/sources").mock(
                return_value=Response(200, json=[sample_source_json])
            )
            client = CalderaClient(BASE, "key")
            result = await client.list_sources()
            assert len(result) == 1
            assert isinstance(result[0], Source)
            await client.close()
