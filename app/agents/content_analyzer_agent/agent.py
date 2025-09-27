"""Agente especializado en análisis inteligente de contenido y metadatos."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

import sys
import os

# Add the app directory to the path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(os.path.dirname(current_dir))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from agents.base import AgentResponse, AgentTask, BaseAgent
from common.observability import record_agent_invocation


@dataclass
class ContentAnalysis:
    """Resultado del análisis de contenido."""
    
    content_type: str  # "technical", "legal", "business", "academic", etc.
    complexity_score: float  # 0.0 - 1.0
    key_topics: List[str]
    language_detected: str
    readability_score: float
    sensitive_data_detected: bool
    recommended_processing: Dict[str, Any]
    metadata_enrichment: Dict[str, Any]


class ContentAnalyzerAgent(BaseAgent):
    """Agente que analiza contenido para optimizar procesamiento y conversión."""

    def __init__(self) -> None:
        super().__init__(name="content_analyzer_agent")

    def can_handle(self, task: AgentTask) -> bool:
        """Maneja tareas de análisis de contenido."""
        return task.task_type in ["content_analysis", "metadata_enrichment", "content_classification"]

    def handle(self, task: AgentTask) -> AgentResponse:
        """Ejecuta análisis inteligente del contenido."""
        
        start_time = time.perf_counter()
        
        try:
            content = task.get("content") or ""
            file_path = task.get("file_path")
            analysis_type = task.get("analysis_type") or "full"
            
            if not content and not file_path:
                return AgentResponse(
                    success=False, 
                    error="content_or_file_path_required"
                )
            
            # Realizar análisis
            analysis = self._analyze_content(content, file_path, analysis_type)
            
            duration = time.perf_counter() - start_time
            record_agent_invocation(
                self.name,
                task.task_type,
                "success",
                duration_seconds=duration,
                language=analysis.language_detected
            )
            
            return AgentResponse(
                success=True,
                data={
                    "analysis": asdict(analysis),
                    "processing_time": duration
                }
            )
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            record_agent_invocation(
                self.name,
                task.task_type,
                "error",
                duration_seconds=duration
            )
            
            return AgentResponse(
                success=False,
                error=f"analysis_failed: {str(e)}"
            )

    def _analyze_content(self, content: str, file_path: Optional[str], analysis_type: str) -> ContentAnalysis:
        """Realiza el análisis inteligente del contenido."""
        
        # Detectar tipo de contenido
        content_type = self._classify_content_type(content)
        
        # Calcular complejidad
        complexity_score = self._calculate_complexity(content)
        
        # Extraer temas clave
        key_topics = self._extract_key_topics(content)
        
        # Detectar idioma
        language_detected = self._detect_language(content)
        
        # Calcular legibilidad
        readability_score = self._calculate_readability(content)
        
        # Detectar datos sensibles
        sensitive_data_detected = self._detect_sensitive_data(content)
        
        # Recomendar procesamiento
        recommended_processing = self._recommend_processing(
            content_type, complexity_score, sensitive_data_detected
        )
        
        # Enriquecer metadatos
        metadata_enrichment = self._enrich_metadata(
            content, content_type, key_topics, language_detected
        )
        
        return ContentAnalysis(
            content_type=content_type,
            complexity_score=complexity_score,
            key_topics=key_topics,
            language_detected=language_detected,
            readability_score=readability_score,
            sensitive_data_detected=sensitive_data_detected,
            recommended_processing=recommended_processing,
            metadata_enrichment=metadata_enrichment
        )

    def _classify_content_type(self, content: str) -> str:
        """Clasifica el tipo de contenido basado en patrones."""
        
        # Patrones para diferentes tipos de contenido
        patterns = {
            "legal": ["contrato", "acuerdo", "términos", "condiciones", "legal", "jurídico"],
            "technical": ["código", "API", "función", "clase", "método", "algoritmo"],
            "business": ["estrategia", "negocio", "ventas", "marketing", "ROI"],
            "academic": ["investigación", "estudio", "análisis", "metodología", "conclusión"],
            "financial": ["presupuesto", "costos", "ingresos", "balance", "financiero"]
        }
        
        content_lower = content.lower()
        scores = {}
        
        for content_type, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            scores[content_type] = score
        
        return max(scores, key=lambda x: scores[x]) if scores else "general"

    def _calculate_complexity(self, content: str) -> float:
        """Calcula la complejidad del contenido."""
        
        # Factores de complejidad
        word_count = len(content.split())
        sentence_count = content.count('.') + content.count('!') + content.count('?')
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Palabras técnicas/complejas
        complex_words = sum(1 for word in content.split() if len(word) > 7)
        complexity_ratio = complex_words / max(word_count, 1)
        
        # Normalizar a 0-1
        complexity_score = min(1.0, (avg_sentence_length / 20) * 0.5 + complexity_ratio * 0.5)
        
        return round(complexity_score, 2)

    def _extract_key_topics(self, content: str) -> List[str]:
        """Extrae temas clave del contenido."""
        
        # Implementación básica - se puede mejorar con NLP avanzado
        words = content.lower().split()
        
        # Filtrar palabras comunes
        stop_words = {"el", "la", "de", "que", "y", "a", "en", "un", "es", "se", "no", "te", "lo", "le", "da", "su", "por", "son", "con", "para", "al", "una", "del", "las", "los", "como", "pero", "sus", "le", "ya", "o", "porque", "cuando", "muy", "sin", "sobre", "también", "me", "hasta", "donde", "quien", "desde", "todos", "durante", "todos", "muchos", "antes", "ser", "estar", "tener", "hacer"}
        
        # Contar frecuencias
        word_freq = {}
        for word in words:
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Obtener top 5 palabras más frecuentes
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return [word for word, freq in top_words]

    def _detect_language(self, content: str) -> str:
        """Detecta el idioma del contenido."""
        
        # Implementación básica - se puede mejorar con librerías especializadas
        spanish_indicators = ["el", "la", "de", "que", "y", "a", "en", "un", "es", "se", "no", "te", "lo", "le", "da", "su", "por", "son", "con", "para", "al", "una", "del", "las", "los", "como", "pero", "sus", "le", "ya", "o", "porque", "cuando", "muy", "sin", "sobre", "también", "me", "hasta", "donde", "quien", "desde", "todos", "durante"]
        english_indicators = ["the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with", "he", "as", "you", "do", "at", "this", "but", "his", "by", "from", "they", "she", "or", "an", "will", "my", "one", "all", "would", "there", "their"]
        
        content_lower = content.lower()
        spanish_count = sum(1 for word in spanish_indicators if word in content_lower)
        english_count = sum(1 for word in english_indicators if word in content_lower)
        
        return "es" if spanish_count > english_count else "en"

    def _calculate_readability(self, content: str) -> float:
        """Calcula la legibilidad del contenido."""
        
        words = content.split()
        sentences = content.count('.') + content.count('!') + content.count('?')
        
        if sentences == 0:
            return 0.5
        
        avg_sentence_length = len(words) / sentences
        
        # Fórmula simplificada de legibilidad
        readability = max(0.0, min(1.0, 1.0 - (avg_sentence_length - 15) / 30))
        
        return round(readability, 2)

    def _detect_sensitive_data(self, content: str) -> bool:
        """Detecta datos sensibles en el contenido."""
        
        sensitive_patterns = [
            "confidencial", "secreto", "privado", "restringido",
            "password", "contraseña", "token", "api_key",
            "dni", "nif", "passport", "pasaporte",
            "tarjeta", "credit", "card", "cuenta", "account"
        ]
        
        content_lower = content.lower()
        return any(pattern in content_lower for pattern in sensitive_patterns)

    def _recommend_processing(self, content_type: str, complexity_score: float, has_sensitive_data: bool) -> Dict[str, Any]:
        """Recomienda estrategias de procesamiento."""
        
        recommendations = {
            "chunking_strategy": "semantic" if complexity_score > 0.7 else "fixed",
            "chunk_size": 1000 if complexity_score > 0.6 else 1500,
            "overlap": 200 if complexity_score > 0.7 else 100,
            "embedding_model": "specialized" if content_type in ["legal", "technical"] else "general",
            "preprocessing": []
        }
        
        if has_sensitive_data:
            recommendations["preprocessing"].append("anonymization")
            recommendations["security_level"] = "high"
        
        if complexity_score > 0.8:
            recommendations["preprocessing"].append("summarization")
        
        return recommendations

    def _enrich_metadata(self, content: str, content_type: str, key_topics: List[str], language: str) -> Dict[str, Any]:
        """Enriquece metadatos basado en el análisis."""
        
        return {
            "content_classification": content_type,
            "key_topics": key_topics,
            "language": language,
            "word_count": len(content.split()),
            "estimated_reading_time": len(content.split()) // 200,  # minutos
            "content_density": "high" if len(content) > 5000 else "medium" if len(content) > 1000 else "low",
            "analysis_timestamp": time.time()
        }
