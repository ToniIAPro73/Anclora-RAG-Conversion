"""Base utilities for file ingestion agents."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Tuple, Type

from common.text_normalization import Document


LoaderConfig = Tuple[Type[object], Dict[str, object]]


@dataclass
class BaseFileIngestor:
    """Base class shared by domain specific ingestors."""

    domain: str
    collection_name: str
    loader_mapping: Mapping[str, LoaderConfig]

    def supports_extension(self, extension: str) -> bool:
        """Return ``True`` if *extension* can be processed by this ingestor."""

        return extension in self.loader_mapping

    @property
    def extensions(self) -> Iterable[str]:
        """Iterable view of supported file extensions."""

        return self.loader_mapping.keys()

    def load(self, file_path: str, extension: str) -> List[Document]:
        """Load ``Document`` instances from *file_path* using the proper loader."""

        if extension not in self.loader_mapping:
            raise ValueError(f"Extension '{extension}' not supported by {self.domain} ingestor")

        loader_class, loader_kwargs = self.loader_mapping[extension]
        loader = loader_class(file_path, **loader_kwargs)
        return loader.load()


__all__ = ["BaseFileIngestor", "LoaderConfig"]
