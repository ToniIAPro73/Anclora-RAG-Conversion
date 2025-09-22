"""Unit tests for the embeddings manager."""

from types import SimpleNamespace

import pytest

from app.common.embeddings_manager import EmbeddingsConfig, EmbeddingsManager


def _factory(*, model_name: str):
    return SimpleNamespace(model_name=model_name)


def test_manager_returns_default_model_for_unknown_domain() -> None:
    """The manager should fall back to the default model when domain is unknown."""

    manager = EmbeddingsManager(
        EmbeddingsConfig(default_model="sentence-transformers/all-MiniLM-L6-v2"),
        embedding_factory=_factory,
    )

    default_instance = manager.get_embeddings()
    assert default_instance.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert manager.get_embeddings("unknown") is default_instance


def test_manager_uses_domain_override() -> None:
    """Domain specific configuration must return the configured model."""

    config = EmbeddingsConfig(
        default_model="all-MiniLM-L6-v2",
        domain_models={"code": "sentence-transformers/all-mpnet-base-v2"},
    )
    manager = EmbeddingsManager(config=config, embedding_factory=_factory)

    assert manager.get_embeddings("code").model_name == "sentence-transformers/all-mpnet-base-v2"
    assert manager.get_embeddings("documents").model_name == "all-MiniLM-L6-v2"


def test_manager_reuses_instances_for_same_model() -> None:
    """Domains referencing the same model should share the cached instance."""

    config = EmbeddingsConfig(
        default_model="all-MiniLM-L6-v2",
        domain_models={
            "documents": "all-MiniLM-L6-v2",
            "multimedia": "all-MiniLM-L6-v2",
            "code": "sentence-transformers/all-mpnet-base-v2",
        },
    )

    creations: list[str] = []

    def _tracking_factory(*, model_name: str):
        creations.append(model_name)
        return SimpleNamespace(model_name=model_name)

    manager = EmbeddingsManager(config=config, embedding_factory=_tracking_factory)

    documents_instance = manager.get_embeddings("documents")
    multimedia_instance = manager.get_embeddings("multimedia")
    code_instance = manager.get_embeddings("code")

    assert documents_instance is multimedia_instance
    assert documents_instance is not code_instance
    assert creations.count("all-MiniLM-L6-v2") == 1
    assert creations.count("sentence-transformers/all-mpnet-base-v2") == 1


def test_config_reads_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configuration helpers must respect environment variables."""

    monkeypatch.setenv("EMBEDDINGS_MODEL_NAME", "intfloat/e5-base")
    monkeypatch.setenv("EMBEDDINGS_MODEL_CODE", "sentence-transformers/all-mpnet-base-v2")

    config = EmbeddingsConfig.from_sources()

    assert config.default_model == "intfloat/e5-base"
    assert config.model_for_domain("code") == "sentence-transformers/all-mpnet-base-v2"
    assert config.model_for_domain("documents") == "intfloat/e5-base"


def test_config_reads_yaml_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The configuration should merge YAML settings with environment overrides."""

    config_file = tmp_path / "embeddings.yaml"
    config_file.write_text(
        "default_model: sentence-transformers/all-MiniLM-L6-v2\n"
        "domains:\n"
        "  documents: sentence-transformers/all-mpnet-base-v2\n"
        "  multimedia: intfloat/multilingual-e5-base\n"
    )

    monkeypatch.setenv("EMBEDDINGS_CONFIG_FILE", str(config_file))
    monkeypatch.setenv("EMBEDDINGS_MODEL_MULTIMEDIA", "intfloat/multilingual-e5-large")

    config = EmbeddingsConfig.from_sources()

    assert config.default_model == "sentence-transformers/all-MiniLM-L6-v2"
    assert config.model_for_domain("documents") == "sentence-transformers/all-mpnet-base-v2"
    assert config.model_for_domain("multimedia") == "intfloat/multilingual-e5-large"
    assert config.model_for_domain("code") == "sentence-transformers/all-MiniLM-L6-v2"
