import logging
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


def _create_chroma_client() -> chromadb.api.ClientAPI:
    """Create a ChromaDB client, falling back to an in-memory instance if remote access fails."""

    settings = Settings(allow_reset=True, anonymized_telemetry=False)

    try:
        return chromadb.HttpClient(
            host="host.docker.internal",
            port=8000,
            settings=settings,
        )
    except Exception as exc:  # pragma: no cover - defensive path
        logger.warning(
            "No fue posible conectar con el servicio remoto de ChromaDB (%s). Se usará un cliente en memoria.",
            exc,
        )
        local_settings = Settings(
            allow_reset=True,
            anonymized_telemetry=False,
            is_persistent=True,
        )
        return chromadb.PersistentClient(path=":memory:", settings=local_settings)


CHROMA_SETTINGS = _create_chroma_client()
