"""Utility helpers to interact with Chroma collections."""
from __future__ import annotations

import logging
from typing import Sequence, Tuple
from uuid import uuid4

from langchain_core.documents import Document as LangChainDocument


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
    metadatas = [dict(doc.metadata or {}) for doc in documents]
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
