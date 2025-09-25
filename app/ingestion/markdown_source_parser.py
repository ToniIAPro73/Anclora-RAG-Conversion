"""Markdown parser for bibliographic sources used by the ingestion flow."""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.common.logger import Logger


@dataclass
class BibliographicSource:
    """Structured representation of a bibliographic source."""

    id: str
    type: str
    title: str
    authors: Optional[str] = None
    publisher: Optional[str] = None
    year: Optional[str] = None
    url: Optional[str] = None
    citation: Optional[str] = None
    source_document: Optional[str] = None
    additional_content: Optional[str] = None


class MarkdownSourceParser:
    """Parse markdown documents containing structured bibliographic sources."""

    def __init__(self) -> None:
        self._logger = Logger(__name__)
        self._patterns = {
            "source_block": re.compile(r"\*\*ID:\*\*\s*\[([^\]]+)\](.*?)(?=\*\*ID:\*\*|\Z)", re.DOTALL | re.MULTILINE),
            "field": re.compile(r"\*\*([^:]+):\*\*\s*([^\n]+)", re.MULTILINE),
        }
        self._field_mapping = {
            "Type": "type",
            "Tipo": "type",
            "Title": "title",
            "Titulo": "title",
            "Author(s)": "authors",
            "Autor(es)": "authors",
            "Publisher/Origin": "publisher",
            "Editorial/Origen": "publisher",
            "Year": "year",
            "Anio": "year",
            "URL/DOI/Identifier": "url",
            "URL/DOI/Identificador": "url",
            "Citation": "citation",
            "Citacion": "citation",
            "Cita": "citation",
            "Source_Document": "source_document",
            "Documento_Fuente": "source_document",
        }

    async def parse_sources(self, content: str) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._parse_sources_sync, content)

    async def validate_source_format(self, content: str) -> Dict[str, Any]:
        return await asyncio.to_thread(self._validate_sources_sync, content)

    async def generate_template(self, language: str = "es") -> str:
        return await asyncio.to_thread(self._generate_template_sync, language)

    # ------------------------------------------------------------------
    def _parse_sources_sync(self, content: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        try:
            blocks = self._patterns["source_block"].findall(content)
            for source_id, block in blocks:
                parsed = self._parse_single_source(source_id, block)
                if parsed:
                    results.append(parsed)
            self._logger.info("Parseadas %s fuentes del documento", len(results))
        except Exception as exc:  # pragma: no cover - defensive path
            self._logger.error("Error parseando fuentes markdown: %s", exc)
        return results

    def _parse_single_source(self, source_id: str, block_content: str) -> Optional[Dict[str, Any]]:
        data: Dict[str, Any] = {
            "id": source_id.strip(),
            "type": "N/A",
            "title": "N/A",
            "authors": "N/A",
            "publisher": "N/A",
            "year": "N/A",
            "url": "N/A",
            "citation": "N/A",
            "source_document": "N/A",
            "additional_content": "",
        }
        fields = self._patterns["field"].findall(block_content)
        for field_name, field_value in fields:
            key = field_name.strip()
            value = field_value.strip()
            mapped = self._field_mapping.get(key)
            if mapped and value and value.lower() != "n/a":
                data[mapped] = value
        trailing = self._extract_additional(block_content)
        if trailing:
            data["additional_content"] = trailing
        if data["title"] == "N/A" and not data["id"]:
            self._logger.warning("Fuente sin titulo ni identificador valido: %s", source_id)
            return None
        data = self._process_fields(data)
        return data

    def _extract_additional(self, block_content: str) -> str:
        matches = list(self._patterns["field"].finditer(block_content))
        if not matches:
            return ""
        last = matches[-1]
        return block_content[last.end():].strip()

    def _process_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        authors = data.get("authors")
        if authors and authors != "N/A":
            parts = re.split(r"[,;]", authors)
            cleaned = [value.strip() for value in parts if value.strip()]
            if cleaned:
                data["authors"] = "; ".join(cleaned)
        year = data.get("year")
        if year and year != "N/A":
            match = re.search(r"\b(19|20)\d{2}\b", year)
            if match:
                data["year"] = match.group()
        url = data.get("url")
        if url and url != "N/A":
            data["url"] = self._normalise_url(url)
        if data.get("type") in {"N/A", "Documento", "Document"}:
            data["type"] = self._infer_source_type(data)
        return data

    def _normalise_url(self, url: str) -> str:
        candidate = url.strip()
        if candidate.startswith("10.") and not candidate.lower().startswith("http"):
            return f"https://doi.org/{candidate}"
        if candidate.lower().startswith("doi.org") and not candidate.lower().startswith("http"):
            return f"https://{candidate}"
        if candidate.startswith(("http://", "https://", "ftp://")):
            return candidate
        if "." in candidate:
            return f"https://{candidate}"
        return candidate

    def _infer_source_type(self, data: Dict[str, Any]) -> str:
        url = (data.get("url") or "").lower()
        title = (data.get("title") or "").lower()
        publisher = (data.get("publisher") or "").lower()
        if "doi.org" in url or "arxiv" in url:
            return "Articulo Academico"
        if any(value in publisher for value in ["press", "editorial", "publishing"]):
            return "Libro"
        if any(value in url for value in ["github", "gitlab", "bitbucket"]):
            return "Repositorio de Codigo"
        if any(value in title for value in ["package", "library", "framework", "api"]):
            return "Herramienta de Software"
        if "docs" in url or "documentation" in title:
            return "Documentacion"
        if any(value in publisher for value in ["conference", "symposium", "workshop"]):
            return "Conferencia"
        if url and not any(token in url for token in ["pdf", "doi", "arxiv"]):
            return "Sitio Web"
        return "Documento"

    def _validate_sources_sync(self, content: str) -> Dict[str, Any]:
        blocks = self._patterns["source_block"].findall(content)
        result = {"valid": True, "errors": [], "warnings": [], "source_count": len(blocks)}
        if not blocks:
            result["valid"] = False
            result["errors"].append("No se encontraron fuentes con el formato esperado.")
            return result
        for index, (source_id, block) in enumerate(blocks, start=1):
            if not re.match(r"^SRC-\w+$", source_id.strip()):
                result["warnings"].append(
                    f"Fuente {index}: el ID '{source_id}' no sigue el formato recomendado SRC-XXX"
                )
            fields = {name.strip() for name, _ in self._patterns["field"].findall(block)}
            if "Type" not in fields and "Tipo" not in fields:
                result["errors"].append(f"Fuente {source_id}: falta el campo **Type:** o **Tipo:**")
                result["valid"] = False
            if "Title" not in fields and "Titulo" not in fields:
                result["errors"].append(f"Fuente {source_id}: falta el campo **Title:** o **Titulo:**")
                result["valid"] = False
        if result["source_count"] > 100:
            result["warnings"].append(
                f"El documento contiene {result['source_count']} fuentes; el procesamiento podria tomar tiempo."
            )
        return result

    def _generate_template_sync(self, language: str) -> str:
        if language.lower() == "en":
            return self._template_en()
        return self._template_es()

    def _template_es(self) -> str:
        return (
            "# Plantilla de Fuentes Bibliograficas\n\n"
            "## Instrucciones\n"
            "Cada fuente debe seguir exactamente este formato:\n\n"
            "**ID:** [SRC-001]\n"
            "**Tipo:** [Tipo de fuente]\n"
            "**Titulo:** [Titulo del recurso]\n"
            "**Autor(es):** [Autores o N/A]\n"
            "**Editorial/Origen:** [Editorial o N/A]\n"
            "**Anio:** [Anio de publicacion o N/A]\n"
            "**URL/DOI/Identificador:** [Enlace, DOI o identificador]\n"
            "**Citacion:** [Referencia completa o N/A]\n"
            "**Documento_Fuente:** [Nombre del documento base]\n\n"
            "## Ejemplo\n\n"
            "**ID:** [SRC-001]\n"
            "**Tipo:** Articulo Academico\n"
            "**Titulo:** Deep Learning for Natural Language Processing\n"
            "**Autor(es):** Smith, J.; Johnson, K.\n"
            "**Editorial/Origen:** Journal of AI Research\n"
            "**Anio:** 2023\n"
            "**URL/DOI/Identificador:** https://doi.org/10.1234/jair.2023.001\n"
            "**Citacion:** Smith, J. y Johnson, K. (2023). Deep Learning for NLP. Journal of AI Research.\n"
            "**Documento_Fuente:** Bibliografia_Tesis.md\n"
        )

    def _template_en(self) -> str:
        return (
            "# Bibliographic Sources Template\n\n"
            "## Instructions\n"
            "Each source must follow exactly this format:\n\n"
            "**ID:** [SRC-001]\n"
            "**Type:** [Source type]\n"
            "**Title:** [Resource title]\n"
            "**Author(s):** [Authors or N/A]\n"
            "**Publisher/Origin:** [Publisher or N/A]\n"
            "**Year:** [Publication year or N/A]\n"
            "**URL/DOI/Identifier:** [Link, DOI or identifier]\n"
            "**Citation:** [Full citation or N/A]\n"
            "**Source_Document:** [Name of the source document]\n\n"
            "## Example\n\n"
            "**ID:** [SRC-001]\n"
            "**Type:** Academic Paper\n"
            "**Title:** Deep Learning for Natural Language Processing\n"
            "**Author(s):** Smith, J.; Johnson, K.\n"
            "**Publisher/Origin:** Journal of AI Research\n"
            "**Year:** 2023\n"
            "**URL/DOI/Identifier:** https://doi.org/10.1234/jair.2023.001\n"
            "**Citation:** Smith, J. and Johnson, K. (2023). Deep Learning for NLP. Journal of AI Research.\n"
            "**Source_Document:** Thesis_Bibliography.md\n"
        )


__all__ = ["MarkdownSourceParser", "BibliographicSource"]
