"""Fixtures compartidos para tests de powerCaldera."""

import pytest

from powercaldera.api.client import CalderaClient


# --- Sample API response shapes (como los devuelve Caldera v2) ---

@pytest.fixture
def sample_executor_json():
    return {
        "name": "psh",
        "platform": "windows",
        "command": "whoami",
        "payloads": [],
        "code": "",  # campo extra
        "language": "",  # campo extra
        "build_target": "",  # campo extra
        "variations": [],  # campo extra
    }


@pytest.fixture
def sample_ability_json(sample_executor_json):
    return {
        "ability_id": "abc-123-def",
        "name": "Test Ability",
        "description": "A test ability",
        "tactic": "discovery",
        "technique_id": "T1082",
        "technique_name": "System Information Discovery",
        "executors": [sample_executor_json],
        "plugin": "stockpile",
        # Campos extra que Caldera envía pero nuestro modelo ignora
        "access": {},
        "additional_info": {},
        "buckets": ["discovery"],
        "delete_payload": True,
        "privilege": "",
        "requirements": [],
        "singleton": False,
        "repeatable": False,
    }


@pytest.fixture
def sample_agent_json():
    return {
        "paw": "abcdef",
        "host": "WORKSTATION-01",
        "platform": "windows",
        "username": "DOMAIN\\user",
        "privilege": "Elevated",
        "last_seen": "2025-01-15T10:30:00Z",
        "trusted": True,
        "executors": ["psh", "cmd"],
        "group": "red",
        # Campos extra
        "contact": "HTTP",
        "architecture": "amd64",
        "pid": 1234,
        "ppid": 456,
        "location": "C:\\sandcat.exe",
        "server": "http://localhost:8888",
        "created": "2025-01-15T09:00:00Z",
    }


@pytest.fixture
def sample_adversary_json():
    return {
        "adversary_id": "adv-001",
        "name": "Test Adversary",
        "description": "A test adversary",
        "atomic_ordering": ["abc-123", "def-456"],
        "tags": ["test", "discovery"],
        "plugin": "stockpile",
        # Campos extra
        "objective": "default-objective-id",
        "has_repeatable_abilities": False,
    }


@pytest.fixture
def sample_operation_json():
    return {
        "id": "op-001-uuid",
        "name": "Test Operation",
        "state": "running",
        "adversary": {
            "adversary_id": "adv-001",
            "name": "Test Adversary",
            "description": "",
            "atomic_ordering": [],
            "tags": [],
        },
        "host_group": [{"paw": "abcdef", "group": "red"}],
        "start": "2025-01-15T10:00:00Z",
        "finish": "",
        "planner": {"id": "atomic", "name": "atomic"},
        "source": {"id": "basic", "name": "basic"},
        # Campos extra
        "chain": [],
        "rules": [],
        "autonomous": 1,
        "obfuscator": "plain-text",
        "jitter": "2/8",
        "visibility": 50,
    }


@pytest.fixture
def sample_operation_link_json():
    return {
        "id": "link-001",
        "command": "d2hvYW1p",  # base64 "whoami"
        "status": 0,
        "paw": "abcdef",
        "ability": {"ability_id": "abc-123", "name": "Test Ability"},
        "finish": "2025-01-15T10:05:00Z",
        "output": "dXNlcg==",  # base64 "user"
        # Campos extra
        "score": 1,
        "decide": "2025-01-15T10:04:00Z",
        "collect": "2025-01-15T10:04:30Z",
    }


@pytest.fixture
def sample_planner_json():
    return {
        "id": "atomic",
        "name": "atomic",
        "description": "Runs abilities in order",
        # Campos extra
        "module": "plugins.stockpile.app.atomic",
        "stopping_conditions": [],
    }


@pytest.fixture
def sample_source_json():
    return {
        "id": "basic",
        "name": "basic",
        "facts": [{"trait": "host.user.name", "value": "admin"}],
        # Campos extra
        "rules": [],
        "relationships": [],
        "adjustments": [],
    }


@pytest.fixture
def valid_template_json():
    return {
        "name": "Test Template",
        "description": "Template para testing",
        "tags": ["test"],
        "abilities": [
            {
                "name": "Test Discovery",
                "tactic": "discovery",
                "technique_id": "T1082",
                "technique_name": "System Information Discovery",
                "description": "Test",
                "platforms": {
                    "windows": {"psh": "systeminfo"},
                    "linux": {"sh": "uname -a"},
                },
            },
            {
                "name": "Test Collection",
                "tactic": "collection",
                "technique_id": "T1005",
                "technique_name": "Data from Local System",
                "description": "Collect data",
                "platforms": {
                    "windows": {"psh": "Get-ChildItem"},
                },
            },
        ],
    }


@pytest.fixture
async def caldera_client():
    client = CalderaClient("http://testserver", "testkey")
    yield client
    await client.close()
