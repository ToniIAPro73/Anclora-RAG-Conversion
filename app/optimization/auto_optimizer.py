"""Sistema de auto-optimización del RAG basado en métricas en tiempo real."""

from __future__ import annotations

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

from analytics.predictive_analyzer import PredictiveAnalyzer, PredictiveInsight
from common.observability import record_rag_response


class OptimizationLevel(Enum):
    """Niveles de optimización."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class OptimizationAction:
    """Acción de optimización a ejecutar."""
    
    action_id: str
    action_type: str  # "config_change", "resource_scaling", "model_switch"
    description: str
    target_component: str
    parameters: Dict[str, Any]
    expected_improvement: float
    risk_level: str  # "low", "medium", "high"
    rollback_plan: Dict[str, Any]
    timestamp: datetime


@dataclass
class OptimizationResult:
    """Resultado de una optimización aplicada."""
    
    action_id: str
    success: bool
    improvement_achieved: float
    side_effects: List[str]
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    execution_time: float
    timestamp: datetime


class AutoOptimizer:
    """Sistema de auto-optimización inteligente."""

    def __init__(self, optimization_level: OptimizationLevel = OptimizationLevel.MODERATE):
        self.optimization_level = optimization_level
        self.predictive_analyzer = PredictiveAnalyzer()
        self.optimization_history: List[OptimizationResult] = []
        self.active_optimizations: Dict[str, OptimizationAction] = {}
        self.current_config: Dict[str, Any] = self._load_default_config()
        self.metrics_baseline: Dict[str, float] = {}
        self.optimization_thread: Optional[threading.Thread] = None
        self.running = False
        self.optimization_callbacks: Dict[str, Callable] = {}

    def start_auto_optimization(self, interval_minutes: int = 30) -> None:
        """Inicia el proceso de auto-optimización."""
        
        if self.running:
            return
        
        self.running = True
        self.optimization_thread = threading.Thread(
            target=self._optimization_loop,
            args=(interval_minutes,),
            daemon=True
        )
        self.optimization_thread.start()

    def stop_auto_optimization(self) -> None:
        """Detiene el proceso de auto-optimización."""
        
        self.running = False
        if self.optimization_thread:
            self.optimization_thread.join(timeout=5)

    def register_optimization_callback(self, component: str, callback: Callable) -> None:
        """Registra callback para aplicar optimizaciones a componentes específicos."""
        
        self.optimization_callbacks[component] = callback

    def force_optimization_cycle(self) -> List[OptimizationResult]:
        """Fuerza un ciclo de optimización inmediato."""
        
        return self._execute_optimization_cycle()

    def get_optimization_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del optimizador."""
        
        return {
            "running": self.running,
            "optimization_level": self.optimization_level.value,
            "active_optimizations": len(self.active_optimizations),
            "total_optimizations": len(self.optimization_history),
            "last_optimization": self.optimization_history[-1].timestamp if self.optimization_history else None,
            "current_config": self.current_config,
            "metrics_baseline": self.metrics_baseline
        }

    def _optimization_loop(self, interval_minutes: int) -> None:
        """Loop principal de optimización."""
        
        while self.running:
            try:
                self._execute_optimization_cycle()
                time.sleep(interval_minutes * 60)
            except Exception as e:
                print(f"Error in optimization loop: {e}")
                time.sleep(60)  # Esperar 1 minuto antes de reintentar

    def _execute_optimization_cycle(self) -> List[OptimizationResult]:
        """Ejecuta un ciclo completo de optimización."""
        
        results = []
        
        # 1. Recopilar métricas actuales
        current_metrics = self._collect_current_metrics()
        
        # 2. Generar insights predictivos
        insights = self.predictive_analyzer.generate_predictive_insights()
        
        # 3. Identificar oportunidades de optimización
        optimization_actions = self._identify_optimization_opportunities(insights, current_metrics)
        
        # 4. Priorizar y filtrar acciones
        prioritized_actions = self._prioritize_actions(optimization_actions)
        
        # 5. Ejecutar optimizaciones
        for action in prioritized_actions:
            result = self._execute_optimization_action(action)
            results.append(result)
            
            # Parar si hay fallos críticos
            if not result.success and action.risk_level == "high":
                break
        
        # 6. Actualizar baseline de métricas
        self._update_metrics_baseline(current_metrics)
        
        return results

    def _collect_current_metrics(self) -> Dict[str, float]:
        """Recopila métricas actuales del sistema."""
        
        # En implementación real, esto se conectaría con Prometheus
        # Por ahora, simulamos métricas
        
        metrics = {
            "avg_response_time": 3.2,
            "query_success_rate": 0.95,
            "context_relevance_score": 0.78,
            "user_satisfaction": 0.82,
            "system_cpu_usage": 0.65,
            "memory_usage": 0.70,
            "cache_hit_rate": 0.85,
            "embedding_quality_score": 0.88
        }
        
        return metrics

    def _identify_optimization_opportunities(self, insights: List[PredictiveInsight], 
                                          metrics: Dict[str, float]) -> List[OptimizationAction]:
        """Identifica oportunidades de optimización basadas en insights."""
        
        actions = []
        
        # Optimizaciones basadas en insights
        for insight in insights:
            if insight.confidence_score > 0.7:
                actions.extend(self._create_actions_from_insight(insight))
        
        # Optimizaciones basadas en métricas
        actions.extend(self._create_actions_from_metrics(metrics))
        
        # Optimizaciones proactivas
        actions.extend(self._create_proactive_actions())
        
        return actions

    def _create_actions_from_insight(self, insight: PredictiveInsight) -> List[OptimizationAction]:
        """Crea acciones de optimización basadas en un insight."""
        
        actions = []
        
        if insight.insight_type == "performance" and "tiempo de respuesta" in insight.description:
            actions.append(OptimizationAction(
                action_id=f"perf_opt_{int(time.time())}",
                action_type="config_change",
                description="Optimizar configuración para reducir tiempo de respuesta",
                target_component="rag_pipeline",
                parameters={
                    "chunk_size": 1000,
                    "context_docs": 4,
                    "embedding_cache_size": 2000
                },
                expected_improvement=0.3,
                risk_level="low",
                rollback_plan={"restore_config": self.current_config.copy()},
                timestamp=datetime.now()
            ))
        
        elif insight.insight_type == "usage" and "pico de uso" in insight.description:
            actions.append(OptimizationAction(
                action_id=f"scale_opt_{int(time.time())}",
                action_type="resource_scaling",
                description="Escalar recursos durante horas pico",
                target_component="compute_resources",
                parameters={
                    "scale_factor": 1.5,
                    "peak_hours": insight.recommended_actions
                },
                expected_improvement=0.25,
                risk_level="medium",
                rollback_plan={"scale_factor": 1.0},
                timestamp=datetime.now()
            ))
        
        return actions

    def _create_actions_from_metrics(self, metrics: Dict[str, float]) -> List[OptimizationAction]:
        """Crea acciones basadas en métricas actuales."""
        
        actions = []
        
        # Optimización de tiempo de respuesta
        if metrics.get("avg_response_time", 0) > 4.0:
            actions.append(OptimizationAction(
                action_id=f"response_time_opt_{int(time.time())}",
                action_type="config_change",
                description="Reducir tiempo de respuesta ajustando parámetros",
                target_component="rag_pipeline",
                parameters={
                    "max_context_docs": 3,
                    "embedding_batch_size": 32
                },
                expected_improvement=0.4,
                risk_level="low",
                rollback_plan={"restore_previous_config": True},
                timestamp=datetime.now()
            ))
        
        # Optimización de relevancia
        if metrics.get("context_relevance_score", 0) < 0.75:
            actions.append(OptimizationAction(
                action_id=f"relevance_opt_{int(time.time())}",
                action_type="model_switch",
                description="Cambiar a modelo de embeddings más preciso",
                target_component="embedding_model",
                parameters={
                    "model_name": "sentence-transformers/all-mpnet-base-v2",
                    "dimension": 768
                },
                expected_improvement=0.2,
                risk_level="medium",
                rollback_plan={"previous_model": "current_model"},
                timestamp=datetime.now()
            ))
        
        return actions

    def _create_proactive_actions(self) -> List[OptimizationAction]:
        """Crea acciones proactivas de optimización."""
        
        actions = []
        
        # Limpieza de caché proactiva
        if len(self.optimization_history) % 10 == 0:  # Cada 10 optimizaciones
            actions.append(OptimizationAction(
                action_id=f"cache_cleanup_{int(time.time())}",
                action_type="maintenance",
                description="Limpieza proactiva de caché",
                target_component="cache_system",
                parameters={"cleanup_threshold": 0.8},
                expected_improvement=0.1,
                risk_level="low",
                rollback_plan={},
                timestamp=datetime.now()
            ))
        
        return actions

    def _prioritize_actions(self, actions: List[OptimizationAction]) -> List[OptimizationAction]:
        """Prioriza acciones de optimización."""
        
        # Filtrar por nivel de optimización
        filtered_actions = []
        for action in actions:
            if self._should_execute_action(action):
                filtered_actions.append(action)
        
        # Ordenar por impacto esperado y riesgo
        def priority_score(action: OptimizationAction) -> float:
            risk_penalty = {"low": 0, "medium": 0.1, "high": 0.3}
            return action.expected_improvement - risk_penalty.get(action.risk_level, 0)
        
        return sorted(filtered_actions, key=priority_score, reverse=True)[:3]  # Top 3

    def _should_execute_action(self, action: OptimizationAction) -> bool:
        """Determina si una acción debe ejecutarse según el nivel de optimización."""
        
        if self.optimization_level == OptimizationLevel.CONSERVATIVE:
            return action.risk_level == "low" and action.expected_improvement > 0.2
        elif self.optimization_level == OptimizationLevel.MODERATE:
            return action.risk_level in ["low", "medium"] and action.expected_improvement > 0.1
        else:  # AGGRESSIVE
            return action.expected_improvement > 0.05

    def _execute_optimization_action(self, action: OptimizationAction) -> OptimizationResult:
        """Ejecuta una acción de optimización."""
        
        start_time = time.time()
        metrics_before = self._collect_current_metrics()
        
        try:
            # Ejecutar la acción
            success = self._apply_optimization(action)
            
            # Esperar un momento para que los cambios tomen efecto
            time.sleep(5)
            
            # Medir métricas después
            metrics_after = self._collect_current_metrics()
            
            # Calcular mejora real
            improvement = self._calculate_improvement(metrics_before, metrics_after)
            
            execution_time = time.time() - start_time
            
            result = OptimizationResult(
                action_id=action.action_id,
                success=success,
                improvement_achieved=improvement,
                side_effects=[],
                metrics_before=metrics_before,
                metrics_after=metrics_after,
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
            # Rollback si la mejora es negativa
            if improvement < -0.05:  # Empeoramiento significativo
                self._rollback_optimization(action)
                result.side_effects.append("Rollback executed due to performance degradation")
            
            self.optimization_history.append(result)
            return result
            
        except Exception as e:
            # Rollback en caso de error
            self._rollback_optimization(action)
            
            return OptimizationResult(
                action_id=action.action_id,
                success=False,
                improvement_achieved=-1.0,
                side_effects=[f"Error: {str(e)}"],
                metrics_before=metrics_before,
                metrics_after=metrics_before,
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )

    def _apply_optimization(self, action: OptimizationAction) -> bool:
        """Aplica una optimización específica."""
        
        if action.target_component in self.optimization_callbacks:
            callback = self.optimization_callbacks[action.target_component]
            return callback(action.parameters)
        
        # Aplicación por defecto
        if action.action_type == "config_change":
            self.current_config.update(action.parameters)
            return True
        elif action.action_type == "resource_scaling":
            # Simular escalado de recursos
            return True
        elif action.action_type == "model_switch":
            # Simular cambio de modelo
            return True
        
        return False

    def _calculate_improvement(self, before: Dict[str, float], after: Dict[str, float]) -> float:
        """Calcula la mejora general basada en métricas."""
        
        improvements = []
        
        # Métricas donde mayor es mejor
        positive_metrics = ["query_success_rate", "context_relevance_score", "user_satisfaction", "cache_hit_rate"]
        
        # Métricas donde menor es mejor
        negative_metrics = ["avg_response_time", "system_cpu_usage", "memory_usage"]
        
        for metric in positive_metrics:
            if metric in before and metric in after:
                improvement = (after[metric] - before[metric]) / before[metric]
                improvements.append(improvement)
        
        for metric in negative_metrics:
            if metric in before and metric in after:
                improvement = (before[metric] - after[metric]) / before[metric]
                improvements.append(improvement)
        
        return sum(improvements) / len(improvements) if improvements else 0.0

    def _rollback_optimization(self, action: OptimizationAction) -> None:
        """Ejecuta rollback de una optimización."""
        
        rollback_plan = action.rollback_plan
        
        if "restore_config" in rollback_plan:
            self.current_config = rollback_plan["restore_config"]
        elif "restore_previous_config" in rollback_plan:
            # Restaurar configuración anterior
            pass
        
        # Aplicar rollback específico del componente
        if action.target_component in self.optimization_callbacks:
            callback = self.optimization_callbacks[action.target_component]
            callback(rollback_plan)

    def _update_metrics_baseline(self, current_metrics: Dict[str, float]) -> None:
        """Actualiza el baseline de métricas."""
        
        if not self.metrics_baseline:
            self.metrics_baseline = current_metrics.copy()
        else:
            # Promedio móvil para suavizar cambios
            alpha = 0.1
            for metric, value in current_metrics.items():
                if metric in self.metrics_baseline:
                    self.metrics_baseline[metric] = (
                        alpha * value + (1 - alpha) * self.metrics_baseline[metric]
                    )
                else:
                    self.metrics_baseline[metric] = value

    def _load_default_config(self) -> Dict[str, Any]:
        """Carga configuración por defecto."""
        
        return {
            "chunk_size": 1200,
            "chunk_overlap": 200,
            "max_context_docs": 5,
            "embedding_model": "sentence-transformers/all-mpnet-base-v2",
            "temperature": 0.7,
            "max_tokens": 1000
        }
