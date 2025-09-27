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
            "source_block": re.compile(r"^\*\s+ID:\s*([^\s]+).*?(?=\*\s+ID:|\*\s+[A-Z]|$)", re.MULTILINE | re.DOTALL),
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
        # Fix encoding issues in the content
        content = self._fix_encoding_issues(content)
        return await asyncio.to_thread(self._parse_sources_sync, content)

    async def validate_source_format(self, content: str) -> Dict[str, Any]:
        # Fix encoding issues in the content
        content = self._fix_encoding_issues(content)
        return await asyncio.to_thread(self._validate_sources_sync, content)

    async def generate_template(self, language: str = "es") -> str:
        return await asyncio.to_thread(self._generate_template_sync, language)

    def _fix_encoding_issues(self, content: str) -> str:
        """Fix common encoding issues with accented characters."""
        # Check if content has corrupted characters
        corrupted_count = content.count('�')
        if corrupted_count > 0:
            self._logger.info("Found %s corrupted characters in content", corrupted_count)

        # Comprehensive mapping of corrupted Spanish characters and words
        fixes = {
            # Most common patterns from the file
            'Acad�mico': 'Académico',
            'Acad�mica': 'Académica',
            'JCDL�17': "JCDL'17",
            'JCDL�18': "JCDL'18",
            'JCDL�19': "JCDL'19",
            'JCDL�20': "JCDL'20",
            'JCDL�21': "JCDL'21",
            'JCDL�22': "JCDL'22",
            'JCDL�23': "JCDL'23",
            'JCDL�24': "JCDL'24",
            't�cnico': 'técnico',
            'tecnol�gica': 'tecnológica',
            'sol�ci�n': 'solución',
            'p�blico': 'público',
            'espa�ol': 'español',
            'peri�dico': 'periódico',
            'hist�rico': 'histórico',
            'pol�tico': 'político',
            'econ�mico': 'económico',
            'aut�ntico': 'auténtico',
            'anal�tico': 'analítico',
            'matem�tico': 'matemático',
            'f�sico': 'físico',
            'qu�mico': 'químico',
            'biol�gico': 'biológico',
            'psicol�gico': 'psicológico',
            'sociol�gico': 'sociológico',
            'filos�fico': 'filosófico',
            'geogr�fico': 'geográfico',
            'demogr�fico': 'demográfico',
            'fotogr�fico': 'fotográfico',
            'tel�fono': 'teléfono',

            # Single character replacements
            '�': 'á',
            '�': 'é',
            '�': 'í',
            '�': 'ó',
            '�': 'ú',
            '�': 'ñ',
            '�': 'ü',

            # Common Spanish words with encoding issues
            'investigaci�n': 'investigación',
            'aplicaci�n': 'aplicación',
            'metodolog�a': 'metodología',
            'documentaci�n': 'documentación',
            'informaci�n': 'información',
            'comunicaci�n': 'comunicación',
            'organizaci�n': 'organización',
            'administraci�n': 'administración',
            'evaluaci�n': 'evaluación',
            'presentaci�n': 'presentación',
            'implementaci�n': 'implementación',
            'configuraci�n': 'configuración',
            'optimizaci�n': 'optimización',
            'digitalizaci�n': 'digitalización',
            'automatizaci�n': 'automatización',
            'inteligencia': 'inteligencia',
            'autom�tico': 'automático',
            'algor�tmo': 'algoritmo',
            'algor�tmico': 'algorítmico',
            'heur�stico': 'heurístico',
            'estad�stico': 'estadístico',
            'matem�tico': 'matemático',
            'probabil�stico': 'probabilístico',
            'determin�stico': 'determinístico',
            'din�mico': 'dinámico',
            'est�tico': 'estático',
            'pr�ctico': 'práctico',
            'te�rico': 'teórico',
            'b�sico': 'básico',
            'avanzado': 'avanzado',
            'complejo': 'complejo',
            'simple': 'simple',
            'f�cil': 'fácil',
            'dif�cil': 'difícil',
            'r�pido': 'rápido',
            'lento': 'lento',
            'nuevo': 'nuevo',
            'viejo': 'viejo',
            'mejor': 'mejor',
            'peor': 'peor',
            'mayor': 'mayor',
            'menor': 'menor',
            'm�ximo': 'máximo',
            'm�nimo': 'mínimo',
            '�ptimo': 'óptimo',
            'p�gina': 'página',
            'cap�tulo': 'capítulo',
            'secci�n': 'sección',
            'apartado': 'apartado',
            'p�rrafo': 'párrafo',
            'l�nea': 'línea',
            'palabra': 'palabra',
            'car�cter': 'carácter',
            's�mbolo': 'símbolo',
            'n�mero': 'número',
            'c�digo': 'código',
            'programa': 'programa',
            'funci�n': 'función',
            'variable': 'variable',
            'constante': 'constante',
            'par�metro': 'parámetro',
            'argumento': 'argumento',
            'resultado': 'resultado',
            'entrada': 'entrada',
            'salida': 'salida',
            'proceso': 'proceso',
            'sistema': 'sistema',
            'm�dulo': 'módulo',
            'componente': 'componente',
            'elemento': 'elemento',
            'estructura': 'estructura',
            'formato': 'formato',
            'archivo': 'archivo',
            'directorio': 'directorio',
            'documento': 'documento',
            'p�gina': 'página',
            'hoja': 'hoja',
            'libro': 'libro',
            'revista': 'revista',
            'peri�dico': 'periódico',
            'art�culo': 'artículo',
            'ensayo': 'ensayo',
            'tesis': 'tesis',
            'trabajo': 'trabajo',
            'estudio': 'estudio',
            'an�lisis': 'análisis',
            's�ntesis': 'síntesis',
            'comparaci�n': 'comparación',
            'descripci�n': 'descripción',
            'explicaci�n': 'explicación',
            'definici�n': 'definición',
            'clasificaci�n': 'clasificación',
            'categor�a': 'categoría',
            'tipo': 'tipo',
            'clase': 'clase',
            'grupo': 'grupo',
            'conjunto': 'conjunto',
            'colecci�n': 'colección',
            'lista': 'lista',
            'array': 'array',
            'matriz': 'matriz',
            'vector': 'vector',
            'base': 'base',
            'dato': 'dato',
            'informaci�n': 'información',
            'conocimiento': 'conocimiento',
            'experiencia': 'experiencia',
            'habilidad': 'habilidad',
            'competencia': 'competencia',
            'capacidad': 'capacidad',
            'destreza': 'destreza',
            't�cnica': 'técnica',
            'm�todo': 'método',
            'procedimiento': 'procedimiento',
            'proceso': 'proceso',
            'algoritmo': 'algoritmo',
            'f�rmula': 'fórmula',
            'ecuaci�n': 'ecuación',
            'funci�n': 'función',
            'operaci�n': 'operación',
            'c�lculo': 'cálculo',
            'computaci�n': 'computación',
            'procesamiento': 'procesamiento',
            'paralelo': 'paralelo',
            'distribuido': 'distribuido',
            'centralizado': 'centralizado',
            'descentralizado': 'descentralizado',
            'conectado': 'conectado',
            'desconectado': 'desconectado',
            'online': 'online',
            'offline': 'offline',
            'local': 'local',
            'remoto': 'remoto',
            'servidor': 'servidor',
            'cliente': 'cliente',
            'usuario': 'usuario',
            'administrador': 'administrador',
            'desarrollador': 'desarrollador',
            'programador': 'programador',
            'ingeniero': 'ingeniero',
            'arquitecto': 'arquitecto',
            'analista': 'analista',
            'consultor': 'consultor',
            'especialista': 'especialista',
            'experto': 'experto',
            'profesional': 'profesional',
            't�cnico': 'técnico',
            'especializado': 'especializado',
            'certificado': 'certificado',
            'acreditado': 'acreditado',
            'autorizado': 'autorizado',
            'aprobado': 'aprobado',
            'validado': 'validado',
            'verificado': 'verificado',
            'comprobado': 'comprobado',
            'testado': 'testado',
            'probado': 'probado',
            'funcional': 'funcional',
            'operativo': 'operativo',
            'eficiente': 'eficiente',
            'eficaz': 'eficaz',
            'r�pido': 'rápido',
            'lento': 'lento',
            'potente': 'potente',
            'poderoso': 'poderoso',
            'capaz': 'capaz',
            'compatible': 'compatible',
            'est�ndar': 'estándar',
            'norma': 'norma',
            'regla': 'regla',
            'ley': 'ley',
            'normativa': 'normativa',
            'regulaci�n': 'regulación',
            'directiva': 'directiva',
            'pol�tica': 'política',
            'estrategia': 'estrategia',
            'plan': 'plan',
            'proyecto': 'proyecto',
            'programa': 'programa',
            'iniciativa': 'iniciativa',
            'objetivo': 'objetivo',
            'meta': 'meta',
            'prop�sito': 'propósito',
            'finalidad': 'finalidad',
            'funci�n': 'función',
            'utilidad': 'utilidad',
            'beneficio': 'beneficio',
            'ventaja': 'ventaja',
            'desventaja': 'desventaja',
            'problema': 'problema',
            'dificultad': 'dificultad',
            'obst�culo': 'obstáculo',
            'limitaci�n': 'limitación',
            'restricci�n': 'restricción',
            'impedimento': 'impedimento',
            'error': 'error',
            'fallo': 'fallo',
            'defecto': 'defecto',
            'bug': 'bug',
            'excepci�n': 'excepción',
            'soluci�n': 'solución',
            'respuesta': 'respuesta',
            'reacci�n': 'reacción',
            'comportamiento': 'comportamiento',
            'conducta': 'conducta',
            'actitud': 'actitud',
            'comunicaci�n': 'comunicación',
            'interacci�n': 'interacción',
            'relaci�n': 'relación',
            'conexi�n': 'conexión',
            'v�nculo': 'vínculo',
            'enlace': 'enlace',
            'referencia': 'referencia',
            'citaci�n': 'citación',
            'bibliograf�a': 'bibliografía',
            'fuente': 'fuente',
            'origen': 'origen',
            'procedencia': 'procedencia',
            'autor': 'autor',
            'escritor': 'escritor',
            'redactor': 'redactor',
            'colaborador': 'colaborador',
            'contribuidor': 'contribuidor',
            'participante': 'participante',
            'miembro': 'miembro',
            'socio': 'socio',
            'asociado': 'asociado',
            'afiliado': 'afiliado',
            'empresa': 'empresa',
            'compa��a': 'compañía',
            'organizaci�n': 'organización',
            'instituci�n': 'institución',
            'instituto': 'instituto',
            'centro': 'centro',
            'departamento': 'departamento',
            'secci�n': 'sección',
            'divisi�n': 'división',
            'unidad': 'unidad',
            'grupo': 'grupo',
            'equipo': 'equipo',
            'personal': 'personal',
            'staff': 'staff',
            'empleados': 'empleados',
            'trabajadores': 'trabajadores',
            'operarios': 'operarios',
            't�cnico': 'técnico',
            'especialista': 'especialista',
            'experto': 'experto',
            'profesor': 'profesor',
            'docente': 'docente',
            'educador': 'educador',
            'maestro': 'maestro',
            'investigador': 'investigador',
            'cient�fico': 'científico',
            'acad�mico': 'académico',
            'estudiante': 'estudiante',
            'alumno': 'alumno',
            'graduado': 'graduado',
            'postgraduado': 'postgraduado',
            'doctor': 'doctor',
            'licenciado': 'licenciado',
            'ingeniero': 'ingeniero',
            'arquitecto': 'arquitecto',
            'm�dico': 'médico',
            'abogado': 'abogado',
            'economista': 'economista',
            'contador': 'contador',
            'administrador': 'administrador',
            'gerente': 'gerente',
            'director': 'director',
            'jefe': 'jefe',
            'supervisor': 'supervisor',
            'coordinador': 'coordinador',
            'l�der': 'líder',
            'gu�a': 'guía',
            'tutor': 'tutor',
            'mentor': 'mentor',
            'consejero': 'consejero',
            'asesor': 'asesor',
            'consultor': 'consultor',
            'especialista': 'especialista',
            'experto': 'experto',
            'profesional': 'profesional',
            't�cnico': 'técnico',
            'especializado': 'especializado',
            'certificado': 'certificado',
            'acreditado': 'acreditado',
            'autorizado': 'autorizado',
            'aprobado': 'aprobado',
            'validado': 'validado',
            'verificado': 'verificado',
            'comprobado': 'comprobado',
            'testado': 'testado',
            'probado': 'probado',
            'funcional': 'funcional',
            'operativo': 'operativo',
            'eficiente': 'eficiente',
            'eficaz': 'eficaz',
            'r�pido': 'rápido',
            'lento': 'lento',
            'potente': 'potente',
            'poderoso': 'poderoso',
            'capaz': 'capaz',
            'compatible': 'compatible',
            'est�ndar': 'estándar',
            'norma': 'norma',
            'regla': 'regla',
            'ley': 'ley',
            'normativa': 'normativa',
            'regulaci�n': 'regulación',
            'directiva': 'directiva',
            'pol�tica': 'política',
            'estrategia': 'estrategia',
            'plan': 'plan',
            'proyecto': 'proyecto',
            'programa': 'programa',
            'iniciativa': 'iniciativa',
            'objetivo': 'objetivo',
            'meta': 'meta',
            'prop�sito': 'propósito',
            'finalidad': 'finalidad',
            'funci�n': 'función',
            'utilidad': 'utilidad',
            'beneficio': 'beneficio',
            'ventaja': 'ventaja',
            'desventaja': 'desventaja',
        }

        # Apply fixes
        for corrupted, correct in fixes.items():
            content = content.replace(corrupted, correct)

        return content

    # ------------------------------------------------------------------
    def _parse_sources_sync(self, content: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        try:
            # Split content into lines and find lines starting with "* ID:"
            lines = content.split('\n')
            source_lines = [line.strip() for line in lines if line.strip().startswith('* ID:')]

            for line in source_lines:
                # Parse the single line format
                parsed = self._parse_single_line_source(line)
                if parsed:
                    results.append(parsed)

            self._logger.info("Parseadas %s fuentes del documento", len(results))
        except Exception as exc:  # pragma: no cover - defensive path
            self._logger.error("Error parseando fuentes markdown: %s", exc)
        return results

    def _parse_single_line_source(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single line source in the format: * ID: SRC-001 Type: ..."""
        data: Dict[str, Any] = {
            "id": "N/A",
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

        # Fix encoding issues with accented characters
        line = self._fix_encoding_issues(line)

        # Extract ID
        id_match = re.search(r'ID:\s*([^\s]+)', line)
        if id_match:
            data["id"] = id_match.group(1).strip()

        # Split by field markers and extract content
        parts = re.split(r'\s+(Type:|Title:|Author\(s\):|Publisher/Origin:|Year:|URL/DOI/Identifier:|Citation:|Source_Document:)', line)

        current_field = None
        for i, part in enumerate(parts):
            if part in ['Type:', 'Title:', 'Author(s):', 'Publisher/Origin:', 'Year:', 'URL/DOI/Identifier:', 'Citation:', 'Source_Document:']:
                current_field = part.rstrip(':')
            elif current_field and i > 0:
                # Get the content for this field (until next field marker)
                field_content = part.strip()
                if field_content and field_content != '*':
                    # Fix encoding issues in field content
                    field_content = field_content.encode().decode('utf-8', errors='ignore')
                    if current_field == 'Type':
                        data["type"] = field_content
                    elif current_field == 'Title':
                        data["title"] = field_content
                    elif current_field == 'Author(s)':
                        data["authors"] = field_content
                    elif current_field == 'Publisher/Origin':
                        data["publisher"] = field_content
                    elif current_field == 'Year':
                        data["year"] = field_content
                    elif current_field == 'URL/DOI/Identifier':
                        data["url"] = field_content
                    elif current_field == 'Citation':
                        data["citation"] = field_content
                    elif current_field == 'Source_Document':
                        data["source_document"] = field_content

        if data["title"] == "N/A" and data["id"] == "N/A":
            return None

        data = self._process_fields(data)
        return data

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

        # Try new single-line format first (all fields in one line)
        single_line_pattern = r"ID:\s*([^\s]+)\s+Type:\s*([^\n]+?)\s+Title:\s*([^\n]+?)(?:\s+Author\(s\):\s*([^\n]+?))?(?:\s+Publisher/Origin:\s*([^\n]+?))?(?:\s+Year:\s*([^\n]+?))?(?:\s+URL/DOI/Identifier:\s*([^\n]+?))?(?:\s+Citation:\s*([^\n]+?))?(?:\s+Source_Document:\s*([^\n]+?))?"
        single_line_match = re.match(single_line_pattern, block_content.strip())

        if single_line_match:
            # Parse single-line format
            groups = single_line_match.groups()
            if len(groups) >= 3:
                data["id"] = groups[0].strip()
                data["type"] = groups[1].strip() if len(groups) > 1 else "N/A"
                data["title"] = groups[2].strip() if len(groups) > 2 else "N/A"
                data["authors"] = groups[3].strip() if len(groups) > 3 and groups[3] else "N/A"
                data["publisher"] = groups[4].strip() if len(groups) > 4 and groups[4] else "N/A"
                data["year"] = groups[5].strip() if len(groups) > 5 and groups[5] else "N/A"
                data["url"] = groups[6].strip() if len(groups) > 6 and groups[6] else "N/A"
                data["citation"] = groups[7].strip() if len(groups) > 7 and groups[7] else "N/A"
                data["source_document"] = groups[8].strip() if len(groups) > 8 and groups[8] else "N/A"
        else:
            # Fall back to original multi-line format
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
        # Count lines that start with "* ID:" to find sources
        lines = content.split('\n')
        source_lines = [line.strip() for line in lines if line.strip().startswith('* ID:')]

        result = {"valid": True, "errors": [], "warnings": [], "source_count": len(source_lines)}
        if not source_lines:
            result["valid"] = False
            result["errors"].append("No se encontraron fuentes con el formato esperado.")
            return result

        for index, line in enumerate(source_lines, start=1):
            # Extract source ID from the line
            id_match = re.search(r'ID:\s*([^\s]+)', line)
            if id_match:
                source_id = id_match.group(1).strip()
                if not re.match(r"^SRC-\w+$", source_id):
                    result["warnings"].append(
                        f"Fuente {index}: el ID '{source_id}' no sigue el formato recomendado SRC-XXX"
                    )

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
