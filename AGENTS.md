# Repository Guidelines

## Project Structure & Module Organization
- `app/` hosts the Streamlit UI (`Inicio.py`), FastAPI API (`api_endpoints.py`), and domain packages (`rag_core`, `ingestion`, `agents`, etc.).
- `config/` centralizes embeddings and environment presets; mirror changes in `.env` or Compose files.
- `tests/` mirrors production boundaries (api, client, converter, regression, etc.); fixtures live in `tests/fixtures/`.
- `scripts/` contains evaluation utilities (`evaluate_responses.py`, `eval_embeddings.py`) plus setup/testing helpers.
- `docker/` and top-level Compose files describe the Ollama, Chroma, UI, and API stack; use `docs/` for extended architecture notes.

## Build, Test & Development Commands
```bash
make test              # full pytest suite
make test-converter    # focused converter checks
make eval              # BLEU/ROUGE evaluation on sample datasets
make regression-agents # latency/quality regression harness
docker compose up -d   # start UI, API, Chroma, Ollama stack
```
Use `open_rag.sh` or `open_rag.bat` for scripted startups; update the project path before running.

## Coding Style & Naming Conventions
- Target Python 3.11, 4-space indentation, and type hints where practical; keep modules snake_case and classes PascalCase.
- Align with PEP 8; run `pyright` (basic mode) to keep types clean and respect `app/stubs` for missing SDKs.
- Prefer dependency-free helpers in `app/common/`; reuse `app/components/` widgets before adding new UI code.

## Testing Guidelines
- Write pytest files under `tests/<domain>/test_*.py`; co-locate fixtures in `tests/fixtures/`.
- Mark long-running flows with `@pytest.mark.slow`; default CI calls `make test`, so guard external calls with mocks.
- For embedding or agent regressions, extend the datasets in `tests/fixtures/sample_responses_*.json` and rerun `make eval`.

## Commit & Pull Request Guidelines
- Follow the existing log: short, imperative subjects (English or Spanish) without trailing punctuation (e.g., `Fix missing imports in chroma utils`).
- Reference relevant issues in the description and note configuration updates (`.env`, Compose) explicitly.
- PRs should describe the test surface (`make test`, targeted pytest markers) and include screenshots for UI-facing changes.
- Request review from an agent familiar with the touched area (`app/pages`, `tests/agents`, etc.) and wait for green status checks before merging.

## Configuration Tips
- Copy `.env.example` to `.env` and adjust service URLs (`CHROMA_HOST`, `EMBEDDINGS_*`) before running locally.
- After tweaking embeddings or dependency versions, rebuild services with `docker compose build --no-cache ui api`.
