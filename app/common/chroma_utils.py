"""Utility helpers to interact with Chroma collections."""
from __future__ import annotations

from typing import Sequence, Tuple
from uuid import uuid4

from langchain_core.documents import Document as LangChainDocument


def add_langchain_documents(
    client,
    collection_name: str,
    embeddings,
    documents: Sequence[LangChainDocument],
) -> Tuple[bool, int]:
    """Add `documents` into the Chroma collection named `collection_name`.

    Returns a tuple `(already_existed, added_count)`.
    """

    if not documents:
        return False, 0

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

    collection.add(ids=ids, documents=contents, embeddings=vectors, metadatas=metadatas)
    return existed, len(documents)


__all__ = ["add_langchain_documents"]
