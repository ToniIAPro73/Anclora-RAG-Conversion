from __future__ import annotations

import asyncio

from app.ingestion.markdown_source_parser import MarkdownSourceParser


def test_markdown_parser_extracts_sources() -> None:
    parser = MarkdownSourceParser()
    markdown = """
**ID:** [SRC-001]
**Type:** Academic Paper
**Title:** Test Driven Development
**Author(s):** Kent Beck
**Publisher/Origin:** Addison Wesley
**Year:** 2003
**URL/DOI/Identifier:** https://example.com/tdd
**Citation:** Beck, K. (2003). Test Driven Development. Addison Wesley.
**Source_Document:** references.md

**ID:** [SRC-002]
**Tipo:** Herramienta de Software
**Titulo:** LangChain
**Autor(es):** Harrison Chase
**Editorial/Origen:** LangChain Inc.
**Anio:** 2024
**URL/DOI/Identificador:** github.com/langchain-ai/langchain
**Citacion:** N/A
**Documento_Fuente:** tools.md
"""

    sources = asyncio.run(parser.parse_sources(markdown))

    assert len(sources) == 2
    first = sources[0]
    assert first["id"] == "SRC-001"
    assert first["type"] == "Academic Paper" or first["type"] == "Articulo Academico"
    assert first["title"] == "Test Driven Development"


def test_markdown_parser_validation_flags_missing_fields() -> None:
    parser = MarkdownSourceParser()
    markdown = """
**ID:** [SRC-001]
**Title:** Missing Type Example
"""

    validation = asyncio.run(parser.validate_source_format(markdown))

    assert validation["valid"] is False
    assert validation["errors"]
