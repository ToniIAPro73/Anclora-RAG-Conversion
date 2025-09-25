"""Utility helpers to interact with Chroma collections."""
from __future__ import annotations

import dataclasses
import datetime as _dt
import enum
import logging
from pathlib import Path, PurePath
from typing import Any, Mapping, Sequence, Tuple
from uuid import uuid4

from langchain_core.documents import Document as LangChainDocument

logger = logging.getLogger(__name__)


def _make_metadata_serializable(value: Any, *, _path: str = "metadata") -> Any:
    """Return a JSON-serialisable representation of ``value``.

    The conversion is applied recursively to mappings and sequences, normalising
    common complex types (dataclasses, enums, paths, datetimes, callables) and
    falling back to ``str`` for values that remain non-serialisable. Whenever a
    value needs to be replaced by its string representation, the operation is
    logged at ``DEBUG`` level to aid troubleshooting.
    """

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if dataclasses.is_dataclass(value):
        return _make_metadata_serializable(dataclasses.asdict(value), _path=_path)

    if isinstance(value, enum.Enum):
        return _make_metadata_serializable(value.value, _path=_path)

    if isinstance(value, (Path, PurePath)):
        return str(value)

    if isinstance(value, (_dt.datetime, _dt.date, _dt.time)):
        return value.isoformat()

    if isinstance(value, Mapping):
        serialised = {}
        for key, item in value.items():
            key_str = key if isinstance(key, str) else str(key)
            if key_str != key:
                logger.debug("Metadata key %r converted to string %r", key, key_str)
            serialised[key_str] = _make_metadata_serializable(item, _path=f"{_path}.{key_str}")
        return serialised

    if isinstance(value, (list, tuple, set)):
        return [
            _make_metadata_serializable(item, _path=f"{_path}[{index}]")
            for index, item in enumerate(value)
        ]

    if callable(value):
        replacement = getattr(value, "__qualname__", getattr(value, "__name__", repr(value)))
        logger.debug("Metadata callable at %s replaced with %r", _path, replacement)
        return replacement

    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            replacement = value.hex()
            logger.debug("Metadata bytes at %s replaced with hex string", _path)
            return replacement

    replacement = str(value)
    logger.debug("Metadata value at %s (%s) replaced with %r", _path, type(value).__name__, replacement)
    return replacement


logger = logging.getLogger(__name__)


def add_langchain_documents(
    client,
    collection_name: str,
    embeddings,
    documents: Sequence[LangChainDocument],
    *,
    batch_size: int = 50,
) -> Tuple[bool, int]:
    """Add `documents` into the Chroma collection named `collection_name`.

    Returns a tuple `(already_existed, added_count)`.
    """

    if not documents:
        return False, 0

    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")

    contents = [doc.page_content for doc in documents]
    metadatas = [
        _make_metadata_serializable(dict(doc.metadata or {})) for doc in documents
    ]
    vectors = embeddings.embed_documents(contents)
    ids = [f"{collection_name}-{index}-{uuid4().hex}" for index in range(len(documents))]

    collection = client.get_or_create_collection(collection_name)
    try:
        existed = collection.count() > 0
    except Exception:
        try:
            existed = bool(collection.get(include=["ids"]).get("ids"))
        except Exception:
            existed = False

    total_added = 0
    total_batches = (len(documents) + batch_size - 1) // batch_size
    for batch_index in range(total_batches):
        start = batch_index * batch_size
        end = start + batch_size
        batch_ids = ids[start:end]
        batch_contents = contents[start:end]
        batch_vectors = vectors[start:end]
        batch_metadatas = metadatas[start:end]

        logger.info(
            "Añadiendo lote %s/%s a la colección '%s' (%s documentos)",
            batch_index + 1,
            total_batches,
            collection_name,
            len(batch_ids),
        )
        collection.add(
            ids=batch_ids,
            documents=batch_contents,
            embeddings=batch_vectors,
            metadatas=batch_metadatas,
        )
        total_added += len(batch_ids)

    return existed, total_added


__all__ = ["add_langchain_documents"]
