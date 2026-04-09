# AGENTS.md

- Python 3.11+ Textual TUI for MITRE Caldera v2.
- Source of truth is `pyproject.toml`; no checked-in CI/workflows, Makefile, Taskfile, or formatter/lint config were found.
- Entry points: `powercaldera.__main__:main` via `powercaldera` and `python -m powercaldera`.
- Main boundaries: `powercaldera/app.py` = TUI app and mode switching; `powercaldera/api/*` = async `httpx` client + Pydantic API models; `powercaldera/templates/*` = template schema/loading/deploy; `powercaldera/screens/*` = views; `powercaldera/widgets/*` = shared UI pieces.
- Config precedence is CLI `--config/--server/--key/--log-level` > env `CALDERA_URL`, `CALDERA_API_KEY`, `CALDERA_LOG_LEVEL` > YAML `~/.powercaldera/config.yaml`.
- Copy `config.example.yaml` to `~/.powercaldera/config.yaml` for local setup.
- `refresh_interval` and `templates_dir` are parsed but not yet wired into visible UI/template-loading behavior.
- Logs go to `~/.powercaldera/powercaldera.log` with rotation (5 MB, 3 backups).
- Built-in templates are packaged as `powercaldera/templates/builtin/*.json` and loaded as package data.
- Template loading skips invalid JSON/validation failures when listing builtins; deploy creates abilities first, then the adversary, and rolls back created abilities on any failure.
- API/Pydantic models intentionally ignore Caldera's extra fields (`extra="ignore"`), so fixtures should include real Caldera shapes even if the model does not keep every field.
- Install test deps with `pip install -e ".[test]"`.
- Run tests with `pytest tests/ -v`; focused runs: `pytest tests/test_client.py -v`, `pytest tests/test_templates.py -v`, `pytest tests/test_config.py -v`, `pytest tests/test_models.py -v`.
- Pytest is configured with `asyncio_mode = auto`, so async tests run without extra markers/plugins beyond `pytest-asyncio`.
- HTTP tests use `respx`; do not depend on a live Caldera server for unit tests.
