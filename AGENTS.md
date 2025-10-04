# Repository Guidelines

## Project Structure & Module Organization
- `app/` hosts the Streamlit UI (`Inicio.py`), FastAPI API (`api_endpoints.py`), and shared domains such as `rag_core`, `ingestion`, and `agents`.
- `config/` centralizes embedding presets and environment defaults; mirror updates in `.env` and Docker Compose files.
- `tests/` tracks production boundaries (api, client, converter, regression) with fixtures under `tests/fixtures/`.
- `scripts/` aggregates evaluation utilities (`evaluate_responses.py`, `eval_embeddings.py`) plus setup helpers; `docs/` captures architecture notes; `docker/` and top-level Compose files define the Ollama, Chroma, UI, and API services.

## Build, Test & Development Commands
- `make test`  Run the complete pytest suite enforced by CI.
- `make test-converter`  Exercise converter-specific checks before shipping ingestion updates.
- `make eval`  Compute BLEU/ROUGE over sample datasets after tuning prompts or embeddings.
- `make regression-agents`  Validate latency and quality for agent flows.
- `docker compose up -d`  Launch UI, API, Chroma, and Ollama locally; pair with `open_rag.sh` (or `.bat`) after adjusting paths.

## Coding Style & Naming Conventions
- Target Python 3.11 with 4-space indentation, PEP 8 compliance, and practical type hints; consult `app/stubs/` for missing SDKs.
- Keep modules `snake_case`, classes `PascalCase`, and reuse helpers in `app/common/` or widgets in `app/components/` before authoring new utilities.
- Run `pyright` in basic mode pre-commit to catch typing drift.

## Testing Guidelines
- Add pytest modules under `tests/<domain>/test_*.py`; co-locate data builders in `tests/fixtures/`.
- Guard external services with mocks, and flag long-running flows using `@pytest.mark.slow`.
- Execute `make test` (or targeted `pytest tests/<domain>`) before raising a PR.

## Commit & Pull Request Guidelines
- Compose short, imperative commit subjects without trailing punctuation; reference relevant issues and call out configuration changes.
- PRs should summarize the affected area, list executed commands (e.g., `make test`), and include screenshots for UI deltas.
- Request review from domain owners (`app/pages`, `tests/agents`, etc.) and wait for passing checks prior to merge.

## Configuration & Environment Tips
- Copy `.env.example` to `.env`, then set `CHROMA_HOST`, `EMBEDDINGS_*`, and other integration secrets before running locally.
- After modifying embedding providers or dependencies, rebuild with `docker compose build --no-cache ui api` to refresh images.
