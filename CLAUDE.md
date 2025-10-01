# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Anclora AI RAG is a Retrieval-Augmented Generation system built with Python 3.11, utilizing open-source LLMs (Llama3-7b, Phi3-4b) via Ollama. The system enables users to upload documents and perform RAG-based queries against them. It features both a Streamlit UI (port 8080) and FastAPI REST endpoints (port 8081), with ChromaDB for vector storage and multi-agent architecture for document processing.

## Development Commands

### Docker Operations
```bash
# Start full stack (CPU mode)
docker compose up -d

# Start with GPU support
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

# Rebuild services after dependency changes
docker compose build --no-cache ui api

# Pull LLM model (find container ID first with 'docker ps')
docker exec <CONTAINER_ID> ollama pull llama3
docker exec <CONTAINER_ID> ollama pull phi3
```

### Testing
```bash
# Run full test suite
pytest
# or
make test

# Run specific test domains
make test-converter          # Converter tests only
pytest tests/regression      # Regression suite
pytest -m slow              # Long-running tests

# Evaluation and regression
make eval                    # BLEU/ROUGE evaluation
make regression-agents       # Agent latency/quality checks
```

### Local Development (without Docker)
```bash
# Create and activate virtual environment
python -m venv venv_rag --python=python3.11
.\activate_venv.bat          # Windows
source venv_rag/bin/activate # Linux/Mac

# Install dependencies
pip install -r app/requirements.txt

# Set environment variables for ChromaDB connection
export CHROMA_HOST=localhost
export CHROMA_PORT=8000

# Run Streamlit UI
streamlit run app/Inicio.py --server.port 8501

# Run FastAPI
uvicorn app.api_endpoints:app --reload --port 8081
```

### Startup Scripts
- `open_rag.bat` (Windows) / `open_rag.sh` (Linux/Mac): Automated stack startup. Update project path in script before use.
- `run_app.py` / `run_app.bat`: Run Streamlit directly (kills existing processes on port 8501 first)

## Architecture

### Multi-Agent System
The codebase uses a domain-based agent architecture coordinated by `app/agents/orchestrator/service.py`:

- **DocumentAgent** (`app/agents/document_agent/`): Handles text documents (PDF, DOCX, TXT)
- **CodeAgent** (`app/agents/code_agent/`): Processes code files and repositories
- **MediaAgent** (`app/agents/media_agent/`): Audio/video transcription and analysis
- **ArchiveAgent** (`app/agents/archive_agent/`): ZIP/archive file extraction and routing
- **SmartConverterAgent** / **ContentAnalyzerAgent**: Experimental agents for content transformation

Each agent inherits from `BaseFileIngestor` (`app/agents/base.py`) and provides both ingestion and query capabilities.

### RAG Pipeline
1. **Document Ingestion** (`app/common/ingest_file.py`): Routes uploads to appropriate agent ingestor
2. **Embeddings** (`app/common/embeddings_manager.py`): Domain-specific embedding models configurable per agent type (documents, code, multimedia)
3. **Vector Storage** (`app/common/chroma_utils.py`): ChromaDB operations with unified client from `app/common/constants.py`
4. **Retrieval & Generation** (`app/common/langchain_module.py`): LangChain-based RAG with Ollama LLM

### Key Modules
- `app/Inicio.py`: Streamlit UI entry point with chat interface
- `app/api_endpoints.py`: FastAPI REST API with UTF-8 response handling
- `app/pages/Archivos.py`: File management page
- `app/common/assistant_prompt.py`: LLM prompt template (customizable per deployment)
- `app/common/config.py`: Configuration management
- `app/common/translations.py`: i18n support (Spanish/English)

### Security & Privacy
- `app/security/advanced_security.py`: Rate limiting, IP quarantine, anomaly detection
- `app/common/privacy.py`: GDPR compliance with document deletion audit trails
- `app/common/security_scan.py`: File safety validation before conversion
- API authentication via Bearer tokens (`ANCLORA_API_TOKEN`, `ANCLORA_API_TOKENS`, or JWT with `ANCLORA_JWT_SECRET`)

## Configuration

### Environment Variables
Critical variables in `.env` (copy from `.env.example`):
- `MODEL`: LLM model name (e.g., `llama3`, `phi3`)
- `EMBEDDINGS_MODEL_NAME`: Default embedding model
- `EMBEDDINGS_MODEL_<DOMAIN>`: Domain-specific overrides (e.g., `EMBEDDINGS_MODEL_CODE`, `EMBEDDINGS_MODEL_MULTIMEDIA`)
- `CHROMA_HOST` / `CHROMA_PORT`: ChromaDB connection (default: `chroma:8000` in Docker, `localhost:8000` for local dev)
- `ANCLORA_API_TOKENS`: Comma-separated API tokens for authentication
- `LLAMA_CLOUD_API_KEY`: For LlamaParse (complex document processing)

### Embeddings Configuration
Domain-specific embedding models can be configured via environment variables or a YAML file (`EMBEDDINGS_CONFIG_FILE`). Evaluate models with:
```bash
python scripts/eval_embeddings.py --models sentence-transformers/all-mpnet-base-v2 intfloat/multilingual-e5-large
```

### Docker Services
- `ollama`: LLM service (port 11434)
- `chroma`: Vector DB (port 8000)
- `ui`: Streamlit interface (port 8501, metrics on 9000)
- `api`: FastAPI service (port 8081, metrics on 9001)
- `prometheus`: Metrics collection (port 9090)
- `grafana`: Dashboards (port 3000)

## Testing Strategy

### Test Organization
- `tests/agents/`: Agent-specific tests
- `tests/api/`: API endpoint tests
- `tests/pages/`: UI component tests
- `tests/regression/`: Response quality regression suite
- `tests/fixtures/`: Shared test data

### Markers
- `@pytest.mark.slow`: Long-running tests (excluded from fast CI runs)

### Fixtures
Located in `tests/fixtures/` and `tests/conftest.py`. Include sample documents and mocked agent responses.

## Code Style

- **Target**: Python 3.11, PEP 8 compliance
- **Type Hints**: Use where practical; run `pyright` for type checking
- **Imports**: Modules use snake_case, classes use PascalCase
- **Indentation**: 4 spaces

## Important Implementation Notes

### Character Encoding
The API uses `UTF8JSONResponse` (extends `JSONResponse` with `ensure_ascii=False`) to preserve multilingual characters (Spanish ñ, á, etc.) in responses. Always use this for API responses involving user content.

### ChromaDB Client
Import the unified client from `app/common/constants.py`:
```python
from common.constants import CHROMA_CLIENT, CHROMA_COLLECTIONS
```
Do not instantiate separate ChromaDB clients; this ensures collection consistency.

### Document Normalization
All text processing goes through NFC normalization via `app/common/text_normalization.py` to ensure consistent Unicode representation.

### Agent Registration
New agents must be registered in the orchestrator (`app/agents/orchestrator/service.py`) and added to the routing logic in `app/common/ingest_file.py`.

### Privacy Compliance
Document deletion uses `PrivacyManager.forget_document()` which:
1. Removes vectors from all ChromaDB collections
2. Creates audit trail
3. Returns `ForgetSummary` with removed collections/files

## Common Pitfalls

1. **ChromaDB Connection**: When running locally, set `CHROMA_HOST=localhost` and `CHROMA_PORT=8000`. Inside Docker, use `CHROMA_HOST=chroma`.
2. **API Tokens**: If getting 401 errors, ensure `.env` has valid tokens loaded. Scripts load `.env` automatically.
3. **Embeddings Changes**: After changing `EMBEDDINGS_MODEL_*` or related dependencies, rebuild with `docker compose build --no-cache ui api`.
4. **LangChain Imports**: The codebase has compatibility shims for missing LangChain modules. Check `app/common/langchain_module.py` for fallback implementations.
5. **GPU Access**: To enable GPU, combine compose files: `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d`

## Useful Paths

- **Prompts**: `app/common/assistant_prompt.py`
- **Translations**: `app/common/translations.py` (add new i18n strings here)
- **Document Loaders**: `app/agents/*/ingestor.py` (routing logic per file type)
- **API Schema**: Auto-generated at `http://localhost:8081/docs` when API is running
- **Logs**: Docker logs via `docker compose logs -f <service_name>`

## Additional Documentation

- `README.md`: Complete setup and usage guide
- `AGENTS.md`: Legacy agent architecture notes
- `docs/backlog.md`: Roadmap and prioritized features
- `docs/integration-guide.md`: API integration examples
- `docs/legal/`: Terms of service and privacy policy
