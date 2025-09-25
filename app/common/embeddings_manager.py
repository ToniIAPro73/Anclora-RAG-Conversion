"""Thread-safe management of sentence-transformer embeddings per domain."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, Mapping, Optional, TYPE_CHECKING

import os
import logging
import sys

import yaml

if TYPE_CHECKING:  # pragma: no cover - used for type checkers only
    from langchain_huggingface import HuggingFaceEmbeddings

HuggingFaceEmbeddings = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


_DEFAULT_MODEL = "all-MiniLM-L6-v2"
_CONFIG_ENV_VAR = "EMBEDDINGS_CONFIG_FILE"
_DEFAULT_MODEL_ENV_VAR = "EMBEDDINGS_MODEL_NAME"
_DOMAIN_ENV_PREFIX = "EMBEDDINGS_MODEL_"
_DEFAULT_DOMAIN_KEY = "__default__"


EmbeddingsFactory = Callable[..., Any]


def _normalise_domain(domain: Optional[str]) -> str:
    if domain is None:
        return _DEFAULT_DOMAIN_KEY
    trimmed = str(domain).strip().lower()
    return trimmed or _DEFAULT_DOMAIN_KEY


def _load_yaml_config(path: Path) -> tuple[Optional[str], Dict[str, str]]:
    if not path.exists():
        logger.warning("No se encontró el archivo de configuración de embeddings: %s", path)
        return None, {}

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except Exception as exc:  # pragma: no cover - defensive log path
        logger.warning("No fue posible leer %s: %s", path, exc)
        return None, {}

    default_model = data.get("default_model") if isinstance(data, dict) else None
    raw_domains = data.get("domains") if isinstance(data, dict) else None

    domains: Dict[str, str] = {}
    if isinstance(raw_domains, Mapping):
        for domain, model in raw_domains.items():
            if not model:
                continue
            domains[_normalise_domain(domain)] = str(model)

    return (str(default_model) if default_model else None), domains


def _load_domain_overrides_from_env() -> Dict[str, str]:
    overrides: Dict[str, str] = {}
    for key, value in os.environ.items():
        if not key.startswith(_DOMAIN_ENV_PREFIX):
            continue
        suffix = key[len(_DOMAIN_ENV_PREFIX) :]
        if suffix in {"NAME", "FILE"}:  # Preserve legacy variables such as EMBEDDINGS_MODEL_NAME
            continue
        if not value:
            continue
        overrides[_normalise_domain(suffix)] = value
    return overrides


@dataclass(frozen=True)
class EmbeddingsConfig:
    """Configuration describing which model to use per domain."""

    default_model: str = _DEFAULT_MODEL
    domain_models: Mapping[str, str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:  # pragma: no cover - dataclass normalisation
        raw_mapping: Mapping[str, str] | None = self.domain_models
        normalised: Dict[str, str] = {}
        if raw_mapping:
            for domain, model in raw_mapping.items():
                if not model:
                    continue
                normalised[_normalise_domain(domain)] = str(model)
        object.__setattr__(self, "domain_models", normalised)

    def model_for_domain(self, domain: Optional[str]) -> str:
        normalised = _normalise_domain(domain)
        if isinstance(self.domain_models, Mapping):
            model = self.domain_models.get(normalised)
            if model:
                return model
        return self.default_model

    @classmethod
    def from_sources(cls) -> "EmbeddingsConfig":
        config_path = os.environ.get(_CONFIG_ENV_VAR)
        default_model = os.environ.get(_DEFAULT_MODEL_ENV_VAR, _DEFAULT_MODEL)
        domains: Dict[str, str] = {}

        if config_path:
            yaml_default, yaml_domains = _load_yaml_config(Path(config_path))
            if yaml_default:
                default_model = yaml_default
            domains.update(yaml_domains)

        domains.update(_load_domain_overrides_from_env())

        model = str(default_model).strip() or _DEFAULT_MODEL
        return cls(default_model=model, domain_models=domains)


class EmbeddingsManager:
    """Centralised factory for embeddings cached per domain and model."""

    def __init__(
        self,
        config: Optional[EmbeddingsConfig] = None,
        *,
        embedding_factory: Optional[EmbeddingsFactory] = None,
    ) -> None:
        self._config = config or EmbeddingsConfig.from_sources()
        if embedding_factory is None:
            self._embedding_factory = self._load_default_factory()
        else:
            self._embedding_factory = embedding_factory
        self._domain_cache: Dict[str, Any] = {}
        self._model_cache: Dict[str, Any] = {}
        self._lock = Lock()

    @staticmethod
    def _load_default_factory() -> EmbeddingsFactory:
        def _factory(*, model_name: str):
            embedding_cls = globals().get("HuggingFaceEmbeddings")
            if embedding_cls is None or not callable(embedding_cls):
                langchain_module = sys.modules.get("app.common.langchain_module")
                embedding_cls = getattr(
                    langchain_module, "HuggingFaceEmbeddings", embedding_cls
                )
            if embedding_cls is None or not callable(embedding_cls):
                try:
                    from langchain_huggingface import HuggingFaceEmbeddings as _HF
                except ImportError:
                    from langchain_community.embeddings import HuggingFaceEmbeddings as _HF  # type: ignore[assignment]

                embedding_cls = _HF
                globals()["HuggingFaceEmbeddings"] = _HF

            return embedding_cls(model_name=model_name)

        return _factory

    def get_embeddings(self, domain: Optional[str] = None):
        key = _normalise_domain(domain)
        cached = self._domain_cache.get(key)
        if cached is not None:
            return cached

        with self._lock:
            cached = self._domain_cache.get(key)
            if cached is not None:
                return cached

            model_name = self._config.model_for_domain(domain)
            model_instance = self._model_cache.get(model_name)
            if model_instance is None:
                model_instance = self._embedding_factory(model_name=model_name)
                self._model_cache[model_name] = model_instance
                logger.info(
                    "Modelo de embeddings inicializado para '%s': %s",
                    key,
                    model_name,
                )
            else:
                logger.debug(
                    "Reutilizando embeddings previamente inicializados para '%s': %s",
                    key,
                    model_name,
                )

            self._domain_cache[key] = model_instance
            return model_instance

    def get_config(self) -> EmbeddingsConfig:
        return self._config


_DEFAULT_MANAGER: Optional[EmbeddingsManager] = None
_MANAGER_LOCK = Lock()


def get_embeddings_manager() -> EmbeddingsManager:
    global _DEFAULT_MANAGER
    if _DEFAULT_MANAGER is None:
        with _MANAGER_LOCK:
            if _DEFAULT_MANAGER is None:
                _DEFAULT_MANAGER = EmbeddingsManager()
    return _DEFAULT_MANAGER


def configure_default_manager(manager: Optional[EmbeddingsManager]) -> None:
    global _DEFAULT_MANAGER
    with _MANAGER_LOCK:
        _DEFAULT_MANAGER = manager


__all__ = [
    "EmbeddingsConfig",
    "EmbeddingsManager",
    "configure_default_manager",
    "get_embeddings_manager",
]

