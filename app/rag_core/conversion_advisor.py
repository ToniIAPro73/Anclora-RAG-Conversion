"""Conversion recommendations driven by contextual AI knowledge."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional


@dataclass(frozen=True)
class FormatRecommendation:
    """Detailed suggestion about the target format for a conversion operation."""

    recommended_format: str
    profile: str
    justification: str
    metadata_requirements: Dict[str, List[str]] = field(default_factory=dict)
    pre_conversion_checks: List[str] = field(default_factory=list)
    post_conversion_steps: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    confidence: str = "media"
    accepted_extensions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Return the recommendation as a serializable dictionary."""

        return {
            "recommended_format": self.recommended_format,
            "profile": self.profile,
            "justification": self.justification,
            "metadata_requirements": self.metadata_requirements,
            "pre_conversion_checks": self.pre_conversion_checks,
            "post_conversion_steps": self.post_conversion_steps,
            "warnings": self.warnings,
            "confidence": self.confidence,
            "accepted_extensions": self.accepted_extensions,
        }

    def matches_extension(self, extension: str) -> bool:
        """Return ``True`` when ``extension`` already complies with the advice."""

        normalized = extension.lower().lstrip(".")
        if not normalized:
            return False
        allowed = {self.recommended_format.lower(), *(ext.lower() for ext in self.accepted_extensions)}
        return normalized in allowed


class ConversionAdvisor:
    """Suggest the best target format for a conversion workflow."""

    _USE_CASE_ALIASES = {
        "archival": "archivado",
        "archive": "archivado",
        "preservacion": "archivado",
        "preservation": "archivado",
        "web": "web",
        "publicacion": "web",
        "accesibilidad": "accesibilidad",
        "accessibility": "accesibilidad",
        "inclusive": "accesibilidad",
    }

    def __init__(self, specialized_rules: Optional[Mapping[str, Iterable[Mapping[str, object]]]] = None) -> None:
        self._rules = self._build_rules(specialized_rules)

    @staticmethod
    def _build_rules(specialized_rules: Optional[Mapping[str, Iterable[Mapping[str, object]]]]) -> Dict[str, List[Mapping[str, object]]]:
        if specialized_rules is None:
            return {key: list(value) for key, value in _DEFAULT_KNOWLEDGE.items()}

        normalized: Dict[str, List[Mapping[str, object]]] = {}
        for key, value in specialized_rules.items():
            normalized[key.lower()] = list(value)
        if "general" not in normalized:
            normalized["general"] = list(_DEFAULT_KNOWLEDGE["general"])
        return normalized

    def recommend(
        self,
        source_format: str,
        intended_use: str,
        metadata: Optional[Mapping[str, object]] = None,
    ) -> FormatRecommendation:
        """Return the best format recommendation for ``source_format`` and ``intended_use``."""

        normalized_use = self._normalize_use_case(intended_use)
        candidate_rules = self._rules.get(normalized_use)
        if not candidate_rules:
            candidate_rules = self._rules.get("general", [])

        contextual_metadata: MutableMapping[str, object] = {
            "source_format": self._normalize_format(source_format)
        }
        if metadata:
            contextual_metadata.update(metadata)

        for rule in candidate_rules:
            if self._rule_matches(rule, contextual_metadata):
                plan = self._build_recommendation(rule)
                return self._augment_with_context(plan, normalized_use, contextual_metadata)

        fallback_rule = self._rules["general"][0]
        plan = self._build_recommendation(fallback_rule)
        return self._augment_with_context(plan, normalized_use, contextual_metadata)

    @classmethod
    def _normalize_use_case(cls, intended_use: str) -> str:
        normalized = (intended_use or "").strip().lower()
        return cls._USE_CASE_ALIASES.get(normalized, normalized or "general")

    @staticmethod
    def _normalize_format(source_format: str) -> str:
        if "/" in source_format:
            source_format = source_format.split("/", 1)[1]
        return source_format.lower().lstrip(".") or "bin"

    @staticmethod
    def _rule_matches(rule: Mapping[str, object], metadata: Mapping[str, object]) -> bool:
        conditions = rule.get("conditions", {})
        if not isinstance(conditions, Mapping):
            return True

        source_formats = conditions.get("source_formats")
        if source_formats and metadata.get("source_format") not in _as_lower_list(source_formats):
            return False

        dominant_content = conditions.get("dominant_content")
        if dominant_content:
            allowed = _as_lower_list(dominant_content)
            if str(metadata.get("dominant_content", "")).lower() not in allowed:
                return False

        min_resolution = conditions.get("min_resolution_dpi")
        if isinstance(min_resolution, int):
            if int(metadata.get("scan_resolution_dpi", 0)) < min_resolution:
                return False

        required_flags = conditions.get("requires_flags")
        if required_flags:
            for flag in required_flags:
                if not metadata.get(flag, False):
                    return False

        required_metadata = conditions.get("requires_metadata")
        if required_metadata:
            for field_name in required_metadata:
                value = metadata.get(field_name)
                if value in (None, "", [], {}):
                    return False

        return True

    @staticmethod
    def _build_recommendation(rule: Mapping[str, object]) -> FormatRecommendation:
        metadata_requirements = {
            key: list(value)
            for key, value in rule.get("metadata_requirements", {}).items()
        }
        return FormatRecommendation(
            recommended_format=str(rule.get("recommended_format", "pdf")),
            profile=str(rule.get("profile", "PDF/A-2b")),
            justification=str(rule.get("justification", "")),
            metadata_requirements=metadata_requirements,
            pre_conversion_checks=list(rule.get("pre_conversion_checks", [])),
            post_conversion_steps=list(rule.get("post_conversion_steps", [])),
            warnings=list(rule.get("warnings", [])),
            confidence=str(rule.get("confidence", "media")),
            accepted_extensions=list(rule.get("accepted_extensions", [])),
        )

    def _augment_with_context(
        self,
        plan: FormatRecommendation,
        use_case: str,
        metadata: Mapping[str, object],
    ) -> FormatRecommendation:
        contextual_warnings: List[str] = list(plan.warnings)

        if use_case == "archivado" and metadata.get("dominant_content") == "scans":
            if not metadata.get("has_ocr"):
                contextual_warnings.append(
                    "El máster se deriva de escaneos sin OCR; ejecute reconocimiento de texto antes de la ingesta final."
                )
        if use_case == "web" and int(metadata.get("page_count", 0)) > 40:
            contextual_warnings.append(
                "El contenido es extenso; genere una versión resumida o índices HTML secundarios para mejorar la navegación."
            )
        if use_case == "accesibilidad" and not metadata.get("has_alt_text", True):
            contextual_warnings.append(
                "Faltan descripciones alternativas para imágenes; añádalas antes de generar la versión accesible."
            )

        if contextual_warnings != plan.warnings:
            plan = replace(plan, warnings=contextual_warnings)
        return plan


def _as_lower_list(values: object) -> List[str]:
    if isinstance(values, str):
        return [values.lower()]
    return [str(value).lower() for value in values]  # type: ignore[arg-type]


_DEFAULT_KNOWLEDGE: Dict[str, List[Mapping[str, object]]] = {
    "archivado": [
        {
            "conditions": {
                "dominant_content": ["scans", "image"],
                "min_resolution_dpi": 300,
            },
            "recommended_format": "tiff",
            "profile": "TIFF 6.0 sin compresión (ISO 12234-2)",
            "justification": (
                "Las copias maestras digitales con predominio de imagen deben preservarse en TIFF sin pérdidas para"
                " mantener la fidelidad tonal y cumplir las recomendaciones de la Biblioteca del Congreso."
            ),
            "metadata_requirements": {
                "administrativa": [
                    "Registrar la política de retención y el identificador de preservación (PREMIS).",
                    "Documentar resolución de escaneo, bit depth y calibración de color.",
                ],
                "descriptiva": [
                    "Agregar título, creador y fecha siguiendo Dublin Core.",
                    "Indicar idioma original en dc:language y notas sobre el proceso de digitalización.",
                ],
            },
            "pre_conversion_checks": [
                "Verificar que los escaneos estén a 300 ppp o superior.",
                "Confirmar el perfil de color sRGB o Adobe RGB embebido.",
            ],
            "post_conversion_steps": [
                "Generar checksum SHA-256 y almacenarlo en el repositorio de preservación.",
                "Registrar evento PREMIS de creación de máster archivístico.",
            ],
            "warnings": [
                "Conserve los archivos TIFF en almacenamiento WORM o con replicación geográfica.",
            ],
            "confidence": "alta",
            "accepted_extensions": ["tif", "tiff"],
        },
        {
            "conditions": {
                "dominant_content": ["text", "structured"],
                "requires_metadata": ["retention_policy_years"],
            },
            "recommended_format": "pdf",
            "profile": "PDF/A-2b (ISO 19005-2)",
            "justification": (
                "PDF/A-2b garantiza la autosuficiencia del documento textual conservando tipografías, capas y"
                " estructura de lectura para auditorías futuras."
            ),
            "metadata_requirements": {
                "descriptiva": [
                    "Completar Dublin Core (título, creador, asunto, descripción).",
                    "Registrar idioma principal y palabras clave sectoriales.",
                ],
                "administrativa": [
                    "Definir política de retención y clasificación records-management.",
                    "Incluir checksum, versión de PDF/A y responsable de aprobación.",
                ],
            },
            "pre_conversion_checks": [
                "Resolver fuentes incrustadas y convertir colores a sRGB.",
                "Normalizar tablas y marcadores para lectura estructurada.",
            ],
            "post_conversion_steps": [
                "Validar conformidad PDF/A con veraPDF u otra herramienta certificada.",
                "Actualizar catálogo con identificador persistente (Handle o DOI interno).",
            ],
            "confidence": "alta",
            "accepted_extensions": ["pdf"],
        },
    ],
    "web": [
        {
            "conditions": {
                "requires_flags": ["requires_responsive"],
            },
            "recommended_format": "html",
            "profile": "HTML5 semántico con CSS responsivo",
            "justification": (
                "La publicación web requiere HTML5 para soportar navegación responsiva, SEO y despliegue omnicanal"
                " según las guías de la W3C."
            ),
            "metadata_requirements": {
                "descriptiva": [
                    "Declarar metadatos Open Graph y JSON-LD para mejorar el SEO.",
                    "Mantener títulos jerárquicos (h1-h3) alineados con el mapa de contenidos.",
                ],
                "tecnica": [
                    "Optimizar imágenes en formatos WebP/AVIF con `srcset` responsive.",
                    "Incluir manifiesto web y configuración PWA cuando aplique.",
                ],
            },
            "pre_conversion_checks": [
                "Identificar fragmentos reutilizables y definir componentes.",
                "Normalizar enlaces internos y referencias externas a HTTPS.",
            ],
            "post_conversion_steps": [
                "Habilitar lazy-loading para imágenes y videos.",
                "Configurar pruebas de Lighthouse con objetivo >= 90 en performance y accesibilidad.",
            ],
            "warnings": [
                "Recuerde purgar la CDN tras publicar cambios significativos.",
            ],
            "confidence": "alta",
            "accepted_extensions": ["html", "htm"],
        },
        {
            "conditions": {
                "source_formats": ["ppt", "pptx"],
            },
            "recommended_format": "html",
            "profile": "HTML5 con componentes interactivos",
            "justification": (
                "Las presentaciones se benefician de exportar a HTML con navegación slide-by-slide y controles"
                " accesibles para navegadores modernos."
            ),
            "metadata_requirements": {
                "descriptiva": [
                    "Sincronizar títulos de diapositivas con etiquetas `<section>`.",
                ],
                "tecnica": [
                    "Convertir animaciones a transiciones CSS o video incrustado comprimido.",
                ],
            },
            "pre_conversion_checks": [
                "Evaluar compatibilidad de fuentes y reemplazos web-safe.",
            ],
            "post_conversion_steps": [
                "Publicar versión AMP opcional para artículos derivados de presentaciones.",
            ],
            "confidence": "media",
            "accepted_extensions": ["html"],
        },
    ],
    "accesibilidad": [
        {
            "conditions": {
                "dominant_content": ["longform", "report", "ebook"],
                "requires_flags": ["needs_screen_reader"],
            },
            "recommended_format": "epub",
            "profile": "EPUB 3.2 con WCAG 2.1 AA",
            "justification": (
                "EPUB 3.2 soporta navegación estructural, descripciones alternativas y medios sincronizados"
                " conforme a WCAG 2.1, ideal para lectores de pantalla."
            ),
            "metadata_requirements": {
                "descriptiva": [
                    "Completar schema.org `accessMode`, `accessModeSufficient` y `accessibilitySummary`.",
                    "Asignar roles ARIA a encabezados, listas y tablas en el manifiesto EPUB.",
                ],
                "tecnica": [
                    "Incluir Media Overlays para narración sincronizada cuando exista audio.",
                    "Declarar idioma por sección para contenido multilingüe.",
                ],
            },
            "pre_conversion_checks": [
                "Validar estilo lógico de encabezados y orden de lectura.",
                "Comprobar contraste de color y subtítulos en multimedia.",
            ],
            "post_conversion_steps": [
                "Validar con Ace by DAISY y epubcheck para asegurar conformidad.",
                "Publicar changelog de accesibilidad para revisores QA.",
            ],
            "warnings": [
                "Revise que todas las fórmulas estén marcadas con MathML accesible.",
            ],
            "confidence": "alta",
            "accepted_extensions": ["epub"],
        },
        {
            "recommended_format": "pdf",
            "profile": "PDF/UA-1 etiquetado",
            "justification": (
                "Para documentos cortos, un PDF etiquetado conforme a PDF/UA mantiene compatibilidad amplia con lectores"
                " tradicionales y asistentes de voz."
            ),
            "metadata_requirements": {
                "descriptiva": [
                    "Declarar idioma en el diccionario de documentos y proporcionar etiquetas de estructura.",
                ],
                "tecnica": [
                    "Incluir etiquetas de tabla (TH/TD) y referencias de marcadores accesibles.",
                ],
            },
            "pre_conversion_checks": [
                "Asegurar orden lógico de etiquetas y lectura de formularios.",
            ],
            "post_conversion_steps": [
                "Ejecutar PAC 2024 o herramienta similar para certificar conformidad PDF/UA.",
            ],
            "confidence": "media",
            "accepted_extensions": ["pdf"],
        },
    ],
    "general": [
        {
            "recommended_format": "pdf",
            "profile": "PDF/A-2u",
            "justification": (
                "Ante falta de contexto, PDF/A-2u ofrece un equilibrio entre preservación y accesibilidad al exigir"
                " texto Unicode y recursos embebidos."
            ),
            "metadata_requirements": {
                "descriptiva": [
                    "Registrar título, autor y fecha en Dublin Core básico.",
                ],
            },
            "pre_conversion_checks": [
                "Comprobar integridad del archivo fuente y ausencia de enlaces rotos.",
            ],
            "post_conversion_steps": [
                "Generar checksum y almacenarlo junto con los metadatos descriptivos.",
            ],
            "confidence": "media",
            "accepted_extensions": ["pdf"],
        }
    ],
}
