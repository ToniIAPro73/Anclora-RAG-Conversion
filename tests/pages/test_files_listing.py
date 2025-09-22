"""Tests for the Archivos page data helpers."""
from __future__ import annotations

import importlib
import os
import sys
import types
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import pytest


def _install_langchain_stubs(monkeypatch) -> None:
    """Provide minimal stand-ins for optional langchain dependencies."""

    if "langchain_core.documents" in sys.modules:  # pragma: no cover - respect real modules
        return

    langchain_core = types.ModuleType("langchain_core")

    documents_module = types.ModuleType("langchain_core.documents")
    documents_module.Document = object  # type: ignore[attr-defined]

    embeddings_module = types.ModuleType("langchain_core.embeddings")
    embeddings_module.Embeddings = object  # type: ignore[attr-defined]

    utils_module = types.ModuleType("langchain_core.utils")

    def _xor_args(*_args, **_kwargs):  # type: ignore[override]
        def _decorator(func):
            return func

        return _decorator

    utils_module.xor_args = _xor_args  # type: ignore[attr-defined]

    vectorstores_module = types.ModuleType("langchain_core.vectorstores")
    vectorstores_module.VectorStore = object  # type: ignore[attr-defined]

    langchain_core.documents = documents_module  # type: ignore[attr-defined]
    langchain_core.embeddings = embeddings_module  # type: ignore[attr-defined]
    langchain_core.utils = utils_module  # type: ignore[attr-defined]
    langchain_core.vectorstores = vectorstores_module  # type: ignore[attr-defined]

    community_module = sys.modules.get("langchain_community", types.ModuleType("langchain_community"))
    vectorstores_pkg = sys.modules.get(
        "langchain_community.vectorstores", types.ModuleType("langchain_community.vectorstores")
    )
    utils_submodule = types.ModuleType("langchain_community.vectorstores.utils")

    def _maximal_marginal_relevance(*_args, **_kwargs):  # type: ignore[override]
        return []

    utils_submodule.maximal_marginal_relevance = _maximal_marginal_relevance  # type: ignore[attr-defined]
    vectorstores_pkg.utils = utils_submodule  # type: ignore[attr-defined]
    community_module.vectorstores = vectorstores_pkg  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "langchain_core", langchain_core)
    monkeypatch.setitem(sys.modules, "langchain_core.documents", documents_module)
    monkeypatch.setitem(sys.modules, "langchain_core.embeddings", embeddings_module)
    monkeypatch.setitem(sys.modules, "langchain_core.utils", utils_module)
    monkeypatch.setitem(sys.modules, "langchain_core.vectorstores", vectorstores_module)
    monkeypatch.setitem(sys.modules, "langchain_community", community_module)
    monkeypatch.setitem(sys.modules, "langchain_community.vectorstores", vectorstores_pkg)
    monkeypatch.setitem(
        sys.modules, "langchain_community.vectorstores.utils", utils_submodule
    )


@dataclass
class _FakeCollection:
    """Minimal double mimicking a Chroma collection."""

    metadatas: List[Optional[Dict[str, str]]]
    requested_includes: List[Optional[Iterable[str]]] = None

    def __post_init__(self) -> None:  # pragma: no cover - simple initialiser
        if self.requested_includes is None:
            self.requested_includes = []

    class _MetadataResponse:
        def __init__(self, metadatas: List[Optional[Dict[str, str]]]):
            self._metadatas = metadatas

        def get(self, key: str, default=None):  # pragma: no cover - trivial
            if key != "metadatas":
                raise AssertionError(f"Unexpected key requested: {key}")
            return self._metadatas

    def get(self, include: Optional[Iterable[str]] = None):
        self.requested_includes.append(list(include) if include is not None else None)
        if include != ["metadatas"]:
            raise AssertionError(f"Expected include=['metadatas'], received: {include}")
        return self._MetadataResponse(self.metadatas)


class _FakeChromaClient:
    def __init__(self, collections: Dict[str, _FakeCollection]):
        self._collections = collections

    def get_or_create_collection(self, name: str) -> _FakeCollection:
        return self._collections[name]


@dataclass(frozen=True)
class _CollectionConfig:
    domain: str
    description: str = ""


def _expected_records(
    metadata: Dict[str, List[Optional[Dict[str, str]]]],
    configs: Dict[str, _CollectionConfig],
) -> set[tuple[str, str, str]]:
    expected: set[tuple[str, str, str]] = set()
    for collection_name, metadatas in metadata.items():
        config = configs[collection_name]
        for entry in metadatas:
            if not entry:
                continue
            file_name = entry.get("uploaded_file_name")
            if not file_name:
                source = entry.get("source")
                if source:
                    file_name = os.path.basename(source)
            if not file_name:
                continue
            domain = entry.get("domain") or config.domain
            collection = entry.get("collection") or collection_name
            expected.add((file_name, domain, collection))
    return expected


def test_get_unique_sources_df_uses_metadata_only(monkeypatch, request: pytest.FixtureRequest):
    """Large collections should be summarised using metadata only."""

    _install_langchain_stubs(monkeypatch)
    module_name = "app.common.chroma_db_settings"
    monkeypatch.delitem(sys.modules, module_name, raising=False)
    chroma_module = importlib.import_module(module_name)
    request.addfinalizer(lambda: sys.modules.pop(module_name, None))

    common_pkg = sys.modules.get("common")
    created_common_pkg = common_pkg is None
    if created_common_pkg:
        common_pkg = types.ModuleType("common")
        sys.modules["common"] = common_pkg

        def _remove_common_pkg() -> None:  # pragma: no cover - cleanup helper
            sys.modules.pop("common", None)

        request.addfinalizer(_remove_common_pkg)

    def _restore_common_attr(attr_name: str, original: object) -> None:  # pragma: no cover - cleanup helper
        if original is None:
            common_pkg.__dict__.pop(attr_name, None)
        else:
            setattr(common_pkg, attr_name, original)

    previous_attr = getattr(common_pkg, "chroma_db_settings", None)
    setattr(common_pkg, "chroma_db_settings", chroma_module)
    request.addfinalizer(lambda attr="chroma_db_settings", original=previous_attr: _restore_common_attr(attr, original))
    sys.modules["common.chroma_db_settings"] = chroma_module
    request.addfinalizer(lambda: sys.modules.pop("common.chroma_db_settings", None))

    ingest_module_name = "app.common.ingest_file"
    monkeypatch.delitem(sys.modules, ingest_module_name, raising=False)
    ingest_module = importlib.import_module(ingest_module_name)
    request.addfinalizer(lambda: sys.modules.pop(ingest_module_name, None))
    sys.modules["common.ingest_file"] = ingest_module
    previous_ingest_attr = getattr(common_pkg, "ingest_file", None)
    setattr(common_pkg, "ingest_file", ingest_module)
    request.addfinalizer(lambda: sys.modules.pop("common.ingest_file", None))
    request.addfinalizer(lambda attr="ingest_file", original=previous_ingest_attr: _restore_common_attr(attr, original))
    get_unique_sources = ingest_module.get_unique_sources_df
    assert get_unique_sources is chroma_module.get_unique_sources_df

    configs = {
        "alpha_docs": _CollectionConfig(domain="documents", description="Alpha"),
        "beta_code": _CollectionConfig(domain="code", description="Beta"),
    }
    monkeypatch.setattr(chroma_module, "CHROMA_COLLECTIONS", configs, raising=True)

    alpha_metadatas = [
        {"uploaded_file_name": f"alpha_{index}.pdf", "domain": "documents"}
        for index in range(150)
    ]
    alpha_metadatas.extend(
        [
            {"uploaded_file_name": "shared.txt", "collection": "alpha_docs"},
            {"uploaded_file_name": "alpha_1.pdf"},  # duplicate to verify dedupe
            {},
        ]
    )

    beta_metadatas = [
        {"uploaded_file_name": f"beta_{index}.md"} for index in range(80)
    ]
    beta_metadatas.extend(
        [
            {"source": "/opt/records/fallback.log"},
            {"uploaded_file_name": "shared.txt", "collection": "custom_beta"},
            None,
        ]
    )

    fake_collections = {
        "alpha_docs": _FakeCollection(alpha_metadatas),
        "beta_code": _FakeCollection(beta_metadatas),
    }

    client = _FakeChromaClient(fake_collections)

    df = get_unique_sources(client)

    assert list(df.columns) == ["uploaded_file_name", "domain", "collection"]
    assert len(df) == len(_expected_records({
        "alpha_docs": alpha_metadatas,
        "beta_code": beta_metadatas,
    }, configs))
    assert len(df) > 150  # Ensure we handle large collections without truncation

    # Ensure only metadata was requested from every collection
    for fake_collection in fake_collections.values():
        assert fake_collection.requested_includes == [["metadatas"]]

    expected = _expected_records({
        "alpha_docs": alpha_metadatas,
        "beta_code": beta_metadatas,
    }, configs)
    observed = {
        tuple(row)
        for row in df[["uploaded_file_name", "domain", "collection"]].itertuples(index=False, name=None)
    }
    assert observed == expected

    # Spot-check that fallbacks worked correctly
    assert "fallback.log" in df["uploaded_file_name"].values
    assert (df["collection"] == "custom_beta").sum() == 1
