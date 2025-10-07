# Repository Guidelines

## Project Structure & Module Organization
- Primary app code lives under `app/` with the Streamlit UI (`Inicio.py`), FastAPI endpoints (`api_endpoints.py`), and shared domains such as `rag_core`, `ingestion`, and `agents`.
- Configuration defaults and embedding presets reside in `config/`; keep `.env` and Docker Compose files in sync when updating providers.
- Pytest suites live in `tests/`, grouped by domain (api, client, converter, regression) with reusable fixtures under `tests/fixtures/`.
- Utilities and docs are centralized: `scripts/` for automation (e.g., `evaluate_responses.py`), `docs/` for architecture notes, and `docker/` plus top-level Compose files for local services.

## Build, Test, and Development Commands
- `make test` — run the full pytest suite exactly as CI.
- `make test-converter` — target ingestion/converter regressions before shipping data updates.
- `make eval` — compute BLEU/ROUGE on sample sets after prompt or embedding changes.
- `make regression-agents` — verify agent latency and response quality.
- `docker compose up -d` — launch UI, API, Chroma, and Ollama; pair with `scripts/open_rag.sh` or `.bat` to open the interface.

## Coding Style & Naming Conventions
- Target Python 3.11 with 4-space indentation, PEP 8 alignment, and practical type hints; consult `app/stubs/` when SDKs are missing locally.
- Modules follow `snake_case`, classes use `PascalCase`, and reuse helpers from `app/common/` or `app/components/` before adding new utilities.
- Run `pyright` (basic mode) prior to commits to catch typing drift.

## Testing Guidelines
- Place new tests under the appropriate `tests/<domain>/test_*.py` module and share builders in `tests/fixtures/`.
- Mock external services; tag slow scenarios with `@pytest.mark.slow`.
- Execute `make test` (or targeted `pytest tests/<domain>`) before submitting changes.

## Commit & Pull Request Guidelines
- Write short, imperative commit subjects without trailing punctuation; reference related issues or configs when relevant.
- PR descriptions should summarize the affected area, list commands executed (e.g., `make test`), and attach UI screenshots when applicable.
- Request review from domain owners (e.g., `app/pages`, `tests/agents`) and ensure all checks pass prior to merge.

## Configuration & Environment Tips
- Copy `.env.example` to `.env`, then set `CHROMA_HOST`, `EMBEDDINGS_*`, and other secrets before local runs.
- After changing embedding providers or Python dependencies, rebuild with `docker compose build --no-cache ui api` to refresh service images.
