"""Cliente async para la API REST v2 de MITRE Caldera."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .models import (
    Ability,
    Adversary,
    Agent,
    CreateAbilityRequest,
    CreateAdversaryRequest,
    CreateOperationRequest,
    Operation,
    OperationLink,
    Planner,
    Source,
)

logger = logging.getLogger(__name__)


class CalderaAPIError(Exception):
    """API error wrapper; sanitize display text to avoid UI markup injection."""

    def __init__(self, status_code: int, detail: str = ""):
        self.status_code = status_code
        # Store raw detail but sanitize for display.
        self.detail = detail
        safe_detail = detail.replace("[", "(").replace("]", ")")
        super().__init__(f"HTTP {status_code}: {safe_detail}")


class CalderaClient:
    def __init__(self, base_url: str, api_key: str):
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"KEY": api_key} if api_key else {},
            timeout=15.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> CalderaClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    def _check(self, resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            logger.error("API %d %s %s: %s", resp.status_code, resp.request.method, resp.request.url.path, resp.text[:300])
            raise CalderaAPIError(resp.status_code, resp.text[:500])

    # --- Health ---

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/api/v2/health")
            if resp.status_code == 200:
                logger.debug("Health check OK (200)")
                return True
            logger.debug("Health check /health returned %d, trying /agents fallback", resp.status_code)
            resp2 = await self._client.get("/api/v2/agents")
            result = resp2.status_code < 400
            logger.debug("Health check fallback /agents: %d → %s", resp2.status_code, result)
            return result
        except Exception as e:
            logger.warning("Health check failed: %s", e)
            return False

    # --- Agents ---

    async def list_agents(self) -> list[Agent]:
        resp = await self._client.get("/api/v2/agents")
        self._check(resp)
        result = [Agent.model_validate(a) for a in resp.json()]
        logger.debug("GET /api/v2/agents → %d items", len(result))
        return result

    # --- Abilities ---

    async def list_abilities(self) -> list[Ability]:
        resp = await self._client.get("/api/v2/abilities")
        self._check(resp)
        result = [Ability.model_validate(a) for a in resp.json()]
        logger.debug("GET /api/v2/abilities → %d items", len(result))
        return result

    async def create_ability(self, req: CreateAbilityRequest) -> Ability:
        resp = await self._client.post("/api/v2/abilities", json=req.model_dump())
        self._check(resp)
        result = Ability.model_validate(resp.json())
        logger.info("Created ability '%s' (%s)", result.name, result.ability_id)
        return result

    async def delete_ability(self, ability_id: str) -> None:
        resp = await self._client.delete(f"/api/v2/abilities/{ability_id}")
        self._check(resp)
        logger.info("Deleted ability %s", ability_id)

    # --- Adversaries ---

    async def list_adversaries(self) -> list[Adversary]:
        resp = await self._client.get("/api/v2/adversaries")
        self._check(resp)
        result = [Adversary.model_validate(a) for a in resp.json()]
        logger.debug("GET /api/v2/adversaries → %d items", len(result))
        return result

    async def create_adversary(self, req: CreateAdversaryRequest) -> Adversary:
        resp = await self._client.post("/api/v2/adversaries", json=req.model_dump())
        self._check(resp)
        result = Adversary.model_validate(resp.json())
        logger.info("Created adversary '%s' (%s)", result.name, result.adversary_id)
        return result

    async def delete_adversary(self, adversary_id: str) -> None:
        resp = await self._client.delete(f"/api/v2/adversaries/{adversary_id}")
        self._check(resp)
        logger.info("Deleted adversary %s", adversary_id)

    # --- Operations ---

    async def list_operations(self) -> list[Operation]:
        resp = await self._client.get("/api/v2/operations")
        self._check(resp)
        result = [Operation.model_validate(o) for o in resp.json()]
        logger.debug("GET /api/v2/operations → %d items", len(result))
        return result

    async def create_operation(self, req: CreateOperationRequest) -> Operation:
        resp = await self._client.post("/api/v2/operations", json=req.model_dump())
        self._check(resp)
        result = Operation.model_validate(resp.json())
        logger.info("Created operation '%s' (%s)", result.name, result.id)
        return result

    async def get_operation(self, op_id: str) -> Operation:
        resp = await self._client.get(f"/api/v2/operations/{op_id}")
        self._check(resp)
        return Operation.model_validate(resp.json())

    async def update_operation_state(self, op_id: str, state: str) -> None:
        resp = await self._client.patch(
            f"/api/v2/operations/{op_id}", json={"state": state}
        )
        self._check(resp)
        logger.info("Operation %s state → %s", op_id[:8], state)

    async def get_operation_links(self, op_id: str) -> list[OperationLink]:
        resp = await self._client.get(f"/api/v2/operations/{op_id}/links")
        self._check(resp)
        result = [OperationLink.model_validate(l) for l in resp.json()]
        logger.debug("GET /api/v2/operations/%s/links → %d items", op_id[:8], len(result))
        return result

    async def get_link_result(self, op_id: str, link_id: str) -> str:
        resp = await self._client.get(
            f"/api/v2/operations/{op_id}/links/{link_id}/result"
        )
        self._check(resp)
        return resp.text

    async def get_operation_report(self, op_id: str) -> dict[str, Any]:
        resp = await self._client.post(f"/api/v2/operations/{op_id}/report")
        self._check(resp)
        return resp.json()

    # --- Planners & Sources ---

    async def list_planners(self) -> list[Planner]:
        resp = await self._client.get("/api/v2/planners")
        self._check(resp)
        result = [Planner.model_validate(p) for p in resp.json()]
        logger.debug("GET /api/v2/planners → %d items", len(result))
        return result

    async def list_sources(self) -> list[Source]:
        resp = await self._client.get("/api/v2/sources")
        self._check(resp)
        result = [Source.model_validate(s) for s in resp.json()]
        logger.debug("GET /api/v2/sources → %d items", len(result))
        return result
