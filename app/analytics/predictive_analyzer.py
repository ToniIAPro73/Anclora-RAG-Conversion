"""Sistema de análisis predictivo para optimización del RAG."""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics

from common.observability import record_rag_response


@dataclass
class UsagePattern:
    """Patrón de uso identificado."""
    
    pattern_type: str  # "peak_hours", "content_preference", "query_complexity"
    description: str
    frequency: float
    confidence: float
    recommendations: List[str]
    metadata: Dict[str, Any]


@dataclass
class PredictiveInsight:
    """Insight predictivo del sistema."""
    
    insight_type: str
    title: str
    description: str
    impact_level: str  # "low", "medium", "high", "critical"
    recommended_actions: List[str]
    estimated_improvement: float
    confidence_score: float
    data_points: int
    timestamp: datetime


class PredictiveAnalyzer:
    """Analizador predictivo para optimización del sistema RAG."""

    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self.query_history: deque = deque(maxlen=max_history_size)
        self.performance_history: deque = deque(maxlen=max_history_size)
        self.usage_patterns: List[UsagePattern] = []
        self.last_analysis_time = datetime.now()

    def record_query(self, query: str, language: str, response_time: float, 
                    context_docs: int, user_satisfaction: Optional[float] = None) -> None:
        """Registra una consulta para análisis."""
        
        query_data = {
            "timestamp": datetime.now(),
            "query": query,
            "language": language,
            "response_time": response_time,
            "context_docs": context_docs,
            "user_satisfaction": user_satisfaction,
            "query_length": len(query),
            "query_complexity": self._calculate_query_complexity(query),
            "hour_of_day": datetime.now().hour,
            "day_of_week": datetime.now().weekday()
        }
        
        self.query_history.append(query_data)
        self._update_performance_metrics(query_data)

    def analyze_usage_patterns(self) -> List[UsagePattern]:
        """Analiza patrones de uso del sistema."""
        
        if len(self.query_history) < 50:  # Mínimo de datos necesarios
            return []

        patterns = []
        
        # Analizar patrones temporales
        patterns.extend(self._analyze_temporal_patterns())
        
        # Analizar patrones de contenido
        patterns.extend(self._analyze_content_patterns())
        
        # Analizar patrones de rendimiento
        patterns.extend(self._analyze_performance_patterns())
        
        # Analizar patrones de idioma
        patterns.extend(self._analyze_language_patterns())
        
        self.usage_patterns = patterns
        return patterns

    def generate_predictive_insights(self) -> List[PredictiveInsight]:
        """Genera insights predictivos basados en los patrones."""
        
        insights = []
        
        # Actualizar patrones si es necesario
        if datetime.now() - self.last_analysis_time > timedelta(hours=1):
            self.analyze_usage_patterns()
            self.last_analysis_time = datetime.now()
        
        # Generar insights de rendimiento
        insights.extend(self._generate_performance_insights())
        
        # Generar insights de uso
        insights.extend(self._generate_usage_insights())
        
        # Generar insights de optimización
        insights.extend(self._generate_optimization_insights())
        
        return sorted(insights, key=lambda x: x.confidence_score, reverse=True)

    def predict_optimal_configuration(self) -> Dict[str, Any]:
        """Predice la configuración óptima basada en patrones."""
        
        config = {
            "chunk_size": self._predict_optimal_chunk_size(),
            "context_docs": self._predict_optimal_context_docs(),
            "embedding_model": self._predict_optimal_embedding_model(),
            "response_language": self._predict_preferred_language(),
            "peak_hours": self._identify_peak_hours(),
            "maintenance_window": self._suggest_maintenance_window()
        }
        
        return config

    def _calculate_query_complexity(self, query: str) -> float:
        """Calcula la complejidad de una consulta."""
        
        # Factores de complejidad
        word_count = len(query.split())
        question_marks = query.count('?')
        technical_terms = sum(1 for word in query.split() if len(word) > 8)
        
        # Normalizar a 0-1
        complexity = min(1.0, (word_count / 50) * 0.4 + 
                        (question_marks / 3) * 0.3 + 
                        (technical_terms / word_count) * 0.3)
        
        return complexity

    def _update_performance_metrics(self, query_data: Dict[str, Any]) -> None:
        """Actualiza métricas de rendimiento."""
        
        perf_data = {
            "timestamp": query_data["timestamp"],
            "response_time": query_data["response_time"],
            "context_docs": query_data["context_docs"],
            "query_complexity": query_data["query_complexity"],
            "satisfaction": query_data.get("user_satisfaction")
        }
        
        self.performance_history.append(perf_data)

    def _analyze_temporal_patterns(self) -> List[UsagePattern]:
        """Analiza patrones temporales de uso."""
        
        patterns = []
        
        # Análisis por hora del día
        hourly_usage = defaultdict(int)
        for query in self.query_history:
            hourly_usage[query["hour_of_day"]] += 1
        
        if hourly_usage:
            peak_hour = max(hourly_usage, key=hourly_usage.get)
            peak_usage = hourly_usage[peak_hour]
            avg_usage = statistics.mean(hourly_usage.values())
            
            if peak_usage > avg_usage * 1.5:  # 50% más que el promedio
                patterns.append(UsagePattern(
                    pattern_type="peak_hours",
                    description=f"Pico de uso detectado a las {peak_hour}:00 horas",
                    frequency=peak_usage / sum(hourly_usage.values()),
                    confidence=0.8,
                    recommendations=[
                        "Optimizar recursos durante horas pico",
                        "Considerar pre-carga de contenido popular",
                        "Escalar automáticamente durante estas horas"
                    ],
                    metadata={"peak_hour": peak_hour, "peak_usage": peak_usage}
                ))
        
        return patterns

    def _analyze_content_patterns(self) -> List[UsagePattern]:
        """Analiza patrones de contenido consultado."""
        
        patterns = []
        
        # Análizar complejidad de consultas
        complexities = [q["query_complexity"] for q in self.query_history]
        if complexities:
            avg_complexity = statistics.mean(complexities)
            
            if avg_complexity > 0.7:
                patterns.append(UsagePattern(
                    pattern_type="high_complexity_queries",
                    description="Predominan consultas de alta complejidad",
                    frequency=sum(1 for c in complexities if c > 0.7) / len(complexities),
                    confidence=0.75,
                    recommendations=[
                        "Aumentar tamaño de contexto",
                        "Usar modelos más potentes",
                        "Implementar pre-procesamiento avanzado"
                    ],
                    metadata={"avg_complexity": avg_complexity}
                ))
        
        return patterns

    def _analyze_performance_patterns(self) -> List[UsagePattern]:
        """Analiza patrones de rendimiento."""
        
        patterns = []
        
        if len(self.performance_history) < 20:
            return patterns
        
        response_times = [p["response_time"] for p in self.performance_history]
        avg_response_time = statistics.mean(response_times)
        
        # Detectar degradación de rendimiento
        recent_times = response_times[-10:]  # Últimas 10 consultas
        older_times = response_times[-30:-10]  # 10 consultas anteriores
        
        if len(older_times) > 0:
            recent_avg = statistics.mean(recent_times)
            older_avg = statistics.mean(older_times)
            
            if recent_avg > older_avg * 1.3:  # 30% más lento
                patterns.append(UsagePattern(
                    pattern_type="performance_degradation",
                    description="Degradación de rendimiento detectada",
                    frequency=1.0,
                    confidence=0.85,
                    recommendations=[
                        "Revisar carga del sistema",
                        "Optimizar índices de búsqueda",
                        "Considerar limpieza de caché"
                    ],
                    metadata={
                        "recent_avg": recent_avg,
                        "older_avg": older_avg,
                        "degradation_pct": ((recent_avg - older_avg) / older_avg) * 100
                    }
                ))
        
        return patterns

    def _analyze_language_patterns(self) -> List[UsagePattern]:
        """Analiza patrones de idioma."""
        
        patterns = []
        
        language_usage = defaultdict(int)
        for query in self.query_history:
            language_usage[query["language"]] += 1
        
        if language_usage:
            total_queries = sum(language_usage.values())
            dominant_lang = max(language_usage, key=language_usage.get)
            dominant_pct = language_usage[dominant_lang] / total_queries
            
            if dominant_pct > 0.8:  # 80% o más en un idioma
                patterns.append(UsagePattern(
                    pattern_type="language_preference",
                    description=f"Preferencia marcada por idioma {dominant_lang}",
                    frequency=dominant_pct,
                    confidence=0.9,
                    recommendations=[
                        f"Optimizar modelos para idioma {dominant_lang}",
                        "Priorizar contenido en idioma dominante",
                        "Ajustar configuración de embeddings"
                    ],
                    metadata={"dominant_language": dominant_lang, "usage_pct": dominant_pct}
                ))
        
        return patterns

    def _generate_performance_insights(self) -> List[PredictiveInsight]:
        """Genera insights de rendimiento."""
        
        insights = []
        
        if len(self.performance_history) < 10:
            return insights
        
        response_times = [p["response_time"] for p in self.performance_history]
        avg_time = statistics.mean(response_times)
        
        if avg_time > 5.0:  # Más de 5 segundos promedio
            insights.append(PredictiveInsight(
                insight_type="performance",
                title="Tiempo de respuesta elevado",
                description=f"El tiempo promedio de respuesta es {avg_time:.2f}s, superior al objetivo de 3s",
                impact_level="high",
                recommended_actions=[
                    "Optimizar algoritmos de búsqueda",
                    "Aumentar recursos de cómputo",
                    "Revisar configuración de embeddings"
                ],
                estimated_improvement=0.4,
                confidence_score=0.85,
                data_points=len(response_times),
                timestamp=datetime.now()
            ))
        
        return insights

    def _generate_usage_insights(self) -> List[PredictiveInsight]:
        """Genera insights de uso."""
        
        insights = []
        
        for pattern in self.usage_patterns:
            if pattern.pattern_type == "peak_hours" and pattern.confidence > 0.7:
                insights.append(PredictiveInsight(
                    insight_type="usage",
                    title="Patrón de uso identificado",
                    description=pattern.description,
                    impact_level="medium",
                    recommended_actions=pattern.recommendations,
                    estimated_improvement=0.25,
                    confidence_score=pattern.confidence,
                    data_points=len(self.query_history),
                    timestamp=datetime.now()
                ))
        
        return insights

    def _generate_optimization_insights(self) -> List[PredictiveInsight]:
        """Genera insights de optimización."""
        
        insights = []
        
        # Analizar uso de documentos de contexto
        context_docs = [p["context_docs"] for p in self.performance_history if p["context_docs"]]
        if context_docs:
            avg_context = statistics.mean(context_docs)
            
            if avg_context < 3:
                insights.append(PredictiveInsight(
                    insight_type="optimization",
                    title="Bajo uso de contexto",
                    description=f"Promedio de {avg_context:.1f} documentos de contexto, podría mejorarse",
                    impact_level="medium",
                    recommended_actions=[
                        "Aumentar número de documentos recuperados",
                        "Mejorar algoritmo de ranking",
                        "Revisar calidad de embeddings"
                    ],
                    estimated_improvement=0.3,
                    confidence_score=0.7,
                    data_points=len(context_docs),
                    timestamp=datetime.now()
                ))
        
        return insights

    def _predict_optimal_chunk_size(self) -> int:
        """Predice el tamaño óptimo de chunk."""
        
        # Análisis basado en complejidad de consultas
        complexities = [q["query_complexity"] for q in self.query_history]
        if complexities:
            avg_complexity = statistics.mean(complexities)
            if avg_complexity > 0.7:
                return 1500  # Chunks más grandes para consultas complejas
            elif avg_complexity < 0.3:
                return 800   # Chunks más pequeños para consultas simples
        
        return 1200  # Valor por defecto

    def _predict_optimal_context_docs(self) -> int:
        """Predice el número óptimo de documentos de contexto."""
        
        # Basado en satisfacción del usuario y complejidad
        satisfactions = [p.get("satisfaction") for p in self.performance_history if p.get("satisfaction")]
        complexities = [q["query_complexity"] for q in self.query_history]
        
        if satisfactions and statistics.mean(satisfactions) < 0.7:
            return 7  # Más contexto si la satisfacción es baja
        elif complexities and statistics.mean(complexities) > 0.6:
            return 6  # Más contexto para consultas complejas
        
        return 5  # Valor por defecto

    def _predict_optimal_embedding_model(self) -> str:
        """Predice el modelo de embeddings óptimo."""
        
        # Basado en patrones de idioma y complejidad
        language_pattern = next((p for p in self.usage_patterns if p.pattern_type == "language_preference"), None)
        
        if language_pattern and language_pattern.metadata.get("dominant_language") == "es":
            return "multilingual-optimized"
        
        complexities = [q["query_complexity"] for q in self.query_history]
        if complexities and statistics.mean(complexities) > 0.7:
            return "high-performance"
        
        return "general-purpose"

    def _predict_preferred_language(self) -> str:
        """Predice el idioma preferido."""
        
        language_usage = defaultdict(int)
        for query in self.query_history:
            language_usage[query["language"]] += 1
        
        return max(language_usage, key=language_usage.get) if language_usage else "es"

    def _identify_peak_hours(self) -> List[int]:
        """Identifica las horas pico de uso."""
        
        hourly_usage = defaultdict(int)
        for query in self.query_history:
            hourly_usage[query["hour_of_day"]] += 1
        
        if not hourly_usage:
            return []
        
        avg_usage = statistics.mean(hourly_usage.values())
        peak_hours = [hour for hour, usage in hourly_usage.items() if usage > avg_usage * 1.3]
        
        return sorted(peak_hours)

    def _suggest_maintenance_window(self) -> Dict[str, int]:
        """Sugiere ventana de mantenimiento."""
        
        hourly_usage = defaultdict(int)
        for query in self.query_history:
            hourly_usage[query["hour_of_day"]] += 1
        
        if not hourly_usage:
            return {"start_hour": 2, "end_hour": 5}  # Ventana por defecto
        
        # Encontrar la hora con menor uso
        min_hour = min(hourly_usage, key=hourly_usage.get)
        
        return {
            "start_hour": min_hour,
            "end_hour": (min_hour + 3) % 24  # Ventana de 3 horas
        }
