# CLAUDE.md — Ultimate Kids Curiosity Club

## Project Overview

An educational podcast platform that generates kids' educational content using LLMs. It produces scripts, audio, and distributes them as podcasts. The pipeline is driven by a CLI (`kids-podcast`) and an orchestrator that coordinates LLM calls, TTS, and audio processing.

## Tech Stack

- **Python 3.10+** (managed with `uv`)
- **Linting/Formatting**: `ruff` (88 char limit, double quotes)
- **Testing**: `pytest` with fixtures, `pytest-mock`
- **CLI**: `typer` + `rich`
- **Data models**: `pydantic` v2
- **Config**: `pydantic-settings` + `.env` + YAML/JSON data files
- **Web**: `fastapi` + `uvicorn`
- **Templates**: `jinja2`

## Repository Layout

```
src/              # Main package source
  api/            # FastAPI routes
  cli/            # Typer CLI entrypoints
  models/         # Pydantic data models
  modules/        # Pipeline step implementations (LLM, TTS, audio, etc.)
  orchestrator/   # Workflow coordination
  services/       # External service clients
  utils/          # Shared utilities
data/
  shows/          # Per-show YAML config (protagonist, world, concepts)
  fixtures/llm/   # Canned LLM responses for offline testing
  audio/          # Branding / music assets
docs/             # Architecture docs, work package specs, decisions
tests/            # pytest test suite (mirrors src/ layout)
website/          # Static site / Cloudflare deployment
scripts/          # One-off helper scripts
```

## Code Style

- **Typing**: Always use strict modern type hints — `list[str]`, `str | None`, `dict[str, Any]`
- **Paths**: `pathlib.Path` only. Never `os.path.join`.
- **Docstrings**: Google style.
- **Imports**: `ruff` handles organisation; run `ruff check --fix` before committing.
- **Secrets**: `.env` via `python-dotenv`. Never commit credentials.

```python
# Good
def load_config(path: Path) -> dict[str, Any]:
    """Load JSON config from path."""
    return json.loads(path.read_text())

# Bad — no type hints, no pathlib, bare open()
def load_config(path):
    f = open(path)
    return json.load(f)
```

## Development Workflow

```bash
# Install (editable + dev deps)
pip install -e ".[dev]"

# Or with uv
uv sync --all-extras

# Lint + format
ruff check --fix .
ruff format .

# Tests
pytest                  # all tests
pytest tests/unit/      # unit only
pytest -v -k "keyword"  # filtered

# Pre-commit (runs ruff automatically)
pre-commit run --all-files
```

## Testing Conventions

- Fixtures over setup/teardown.
- Use `data/fixtures/llm/` JSON files for mocking LLM responses — do **not** call real APIs in unit tests.
- `pytest-mock` (`mocker` fixture) for patching.
- Mark tests that require real API keys with `@pytest.mark.real_api` and skip by default.

## Shell Scripts

```bash
#!/bin/bash
set -euo pipefail
```

## Important Notes

- `kids-podcast` CLI is the main entrypoint (`src/cli/main.py`).
- Show configs live under `data/shows/<show_name>/` — each has `show.yaml`, `protagonist.yaml`, `world.yaml`, `concepts_covered.json`.
- Work packages are tracked in `docs/work_packages/` — check there before touching a module to understand its intended interface.
- Pre-commit runs `ruff` — commits will be blocked if lint fails. Fix before committing.
