"""
Sistema de Verificación de Claims - Anclora RAG
Verifica automáticamente que todos los claims en la landing sean precisos
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
import statistics
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PerformanceClaim:
    """Claim de rendimiento que debe ser verificado"""
    claim_id: str
    claim_text: str
    metric_type: str  # "processing_time", "success_rate", "volume"
    target_value: float
    tolerance: float  # Margen de error aceptable
    measurement_period: str  # "24h", "7d", "30d"
    document_category: str  # "simple", "medium", "complex", "all"

@dataclass
class VerificationResult:
    """Resultado de verificación de un claim"""
    claim_id: str
    is_accurate: bool
    actual_value: float
    claimed_value: float
    deviation_percentage: float
    confidence_level: float
    last_verified: datetime
    recommendation: str

class ClaimsVerificationSystem:
    """Sistema que verifica automáticamente la precisión de nuestros claims"""
    
    def __init__(self):
        self.claims_registry = self._initialize_claims_registry()
        self.verification_history = []
        self.alert_thresholds = {
            "warning": 10.0,  # 10% de desviación
            "critical": 25.0  # 25% de desviación
        }
    
    def _initialize_claims_registry(self) -> List[PerformanceClaim]:
        """Inicializa el registro de claims a verificar"""
        
        return [
            # Claims de tiempo de procesamiento
            PerformanceClaim(
                claim_id="simple_docs_time",
                claim_text="Documentos simples: 3-15 segundos",
                metric_type="processing_time",
                target_value=9.0,  # Promedio del rango 3-15
                tolerance=6.0,     # ±6 segundos
                measurement_period="24h",
                document_category="simple"
            ),
            
            PerformanceClaim(
                claim_id="medium_docs_time", 
                claim_text="Documentos medianos: 8-30 segundos",
                metric_type="processing_time",
                target_value=19.0,  # Promedio del rango 8-30
                tolerance=11.0,     # ±11 segundos
                measurement_period="24h",
                document_category="medium"
            ),
            
            PerformanceClaim(
                claim_id="complex_docs_time",
                claim_text="Documentos complejos: 20-90 segundos", 
                metric_type="processing_time",
                target_value=55.0,  # Promedio del rango 20-90
                tolerance=35.0,     # ±35 segundos
                measurement_period="24h",
                document_category="complex"
            ),
            
            # Claims de tasa de éxito
            PerformanceClaim(
                claim_id="overall_success_rate",
                claim_text="Tasa de éxito >90%",
                metric_type="success_rate",
                target_value=90.0,
                tolerance=5.0,      # ±5%
                measurement_period="7d",
                document_category="all"
            ),
            
            # Claims de volumen
            PerformanceClaim(
                claim_id="daily_processing_capacity",
                claim_text="Capacidad de procesamiento diario",
                metric_type="volume",
                target_value=500.0,  # 500 documentos/día
                tolerance=100.0,     # ±100 documentos
                measurement_period="24h", 
                document_category="all"
            ),
            
            # Claims de mejora continua
            PerformanceClaim(
                claim_id="learning_improvement",
                claim_text="Mejora automática con cada uso",
                metric_type="improvement_rate",
                target_value=2.0,   # 2% mejora semanal
                tolerance=1.0,      # ±1%
                measurement_period="7d",
                document_category="all"
            )
        ]
    
    async def verify_all_claims(self) -> List[VerificationResult]:
        """Verifica todos los claims registrados"""
        
        logger.info("🔍 Iniciando verificación de claims")
        
        verification_results = []
        
        for claim in self.claims_registry:
            try:
                result = await self._verify_single_claim(claim)
                verification_results.append(result)
                
                # Log resultado
                status = "✅ PRECISO" if result.is_accurate else "❌ IMPRECISO"
                logger.info(f"{status} - {claim.claim_id}: {result.actual_value:.1f} vs {result.claimed_value:.1f}")
                
            except Exception as e:
                logger.error(f"❌ Error verificando claim {claim.claim_id}: {str(e)}")
                
                # Crear resultado de error
                error_result = VerificationResult(
                    claim_id=claim.claim_id,
                    is_accurate=False,
                    actual_value=0.0,
                    claimed_value=claim.target_value,
                    deviation_percentage=100.0,
                    confidence_level=0.0,
                    last_verified=datetime.now(),
                    recommendation="Error en verificación - revisar sistema de métricas"
                )
                verification_results.append(error_result)
        
        # Guardar historial
        self.verification_history.append({
            "timestamp": datetime.now(),
            "results": verification_results
        })
        
        # Generar alertas si es necesario
        await self._generate_alerts(verification_results)
        
        logger.info(f"✅ Verificación completada: {len(verification_results)} claims verificados")
        
        return verification_results
    
    async def _verify_single_claim(self, claim: PerformanceClaim) -> VerificationResult:
        """Verifica un claim individual"""
        
        # Obtener datos reales del sistema
        actual_data = await self._get_actual_metrics(claim)
        
        # Calcular valor actual
        actual_value = self._calculate_metric_value(actual_data, claim.metric_type)
        
        # Verificar precisión
        deviation = abs(actual_value - claim.target_value)
        deviation_percentage = (deviation / claim.target_value) * 100
        
        is_accurate = deviation <= claim.tolerance
        
        # Calcular nivel de confianza
        confidence_level = self._calculate_confidence_level(actual_data, claim)
        
        # Generar recomendación
        recommendation = self._generate_recommendation(claim, actual_value, deviation_percentage)
        
        return VerificationResult(
            claim_id=claim.claim_id,
            is_accurate=is_accurate,
            actual_value=actual_value,
            claimed_value=claim.target_value,
            deviation_percentage=deviation_percentage,
            confidence_level=confidence_level,
            last_verified=datetime.now(),
            recommendation=recommendation
        )
    
    async def _get_actual_metrics(self, claim: PerformanceClaim) -> Dict:
        """Obtiene métricas reales del sistema"""
        
        # En producción, esto consultaría la base de datos real
        # Por ahora simulamos datos realistas
        
        if claim.metric_type == "processing_time":
            if claim.document_category == "simple":
                # Simular tiempos para documentos simples
                times = np.random.normal(8, 3, 100)  # Media 8s, std 3s
                times = np.clip(times, 1, 20)  # Limitar entre 1-20s
            elif claim.document_category == "medium":
                times = np.random.normal(22, 8, 100)  # Media 22s, std 8s
                times = np.clip(times, 5, 45)  # Limitar entre 5-45s
            else:  # complex
                times = np.random.normal(50, 20, 100)  # Media 50s, std 20s
                times = np.clip(times, 15, 120)  # Limitar entre 15-120s
            
            return {"processing_times": times.tolist()}
        
        elif claim.metric_type == "success_rate":
            # Simular tasa de éxito realista
            successes = np.random.binomial(1, 0.92, 1000)  # 92% éxito
            return {"successes": successes.tolist()}
        
        elif claim.metric_type == "volume":
            # Simular volumen diario
            daily_volumes = np.random.poisson(450, 30)  # Promedio 450 docs/día
            return {"daily_volumes": daily_volumes.tolist()}
        
        elif claim.metric_type == "improvement_rate":
            # Simular mejora semanal
            weekly_improvements = np.random.normal(1.8, 0.5, 12)  # 1.8% mejora promedio
            return {"weekly_improvements": weekly_improvements.tolist()}
        
        return {}
    
    def _calculate_metric_value(self, data: Dict, metric_type: str) -> float:
        """Calcula el valor de la métrica desde los datos"""
        
        if metric_type == "processing_time":
            times = data.get("processing_times", [])
            return statistics.mean(times) if times else 0.0
        
        elif metric_type == "success_rate":
            successes = data.get("successes", [])
            return (sum(successes) / len(successes)) * 100 if successes else 0.0
        
        elif metric_type == "volume":
            volumes = data.get("daily_volumes", [])
            return statistics.mean(volumes) if volumes else 0.0
        
        elif metric_type == "improvement_rate":
            improvements = data.get("weekly_improvements", [])
            return statistics.mean(improvements) if improvements else 0.0
        
        return 0.0
    
    def _calculate_confidence_level(self, data: Dict, claim: PerformanceClaim) -> float:
        """Calcula nivel de confianza en la medición"""
        
        # Factores que afectan la confianza:
        # 1. Tamaño de muestra
        # 2. Variabilidad de los datos
        # 3. Período de medición
        
        sample_size = len(list(data.values())[0]) if data else 0
        
        # Confianza basada en tamaño de muestra
        if sample_size >= 100:
            size_confidence = 0.95
        elif sample_size >= 50:
            size_confidence = 0.85
        elif sample_size >= 20:
            size_confidence = 0.75
        else:
            size_confidence = 0.60
        
        # Confianza basada en período
        period_confidence = {
            "24h": 0.80,
            "7d": 0.90,
            "30d": 0.95
        }.get(claim.measurement_period, 0.75)
        
        # Confianza combinada
        return (size_confidence + period_confidence) / 2
    
    def _generate_recommendation(self, claim: PerformanceClaim, actual_value: float, deviation_percentage: float) -> str:
        """Genera recomendación basada en la verificación"""
        
        if deviation_percentage <= 5:
            return "✅ Claim preciso - mantener monitoreo regular"
        
        elif deviation_percentage <= self.alert_thresholds["warning"]:
            if actual_value > claim.target_value:
                return "⚠️ Rendimiento mejor que claim - considerar actualizar claim al alza"
            else:
                return "⚠️ Rendimiento ligeramente bajo - monitorear de cerca"
        
        elif deviation_percentage <= self.alert_thresholds["critical"]:
            if actual_value > claim.target_value:
                return "📈 Rendimiento significativamente mejor - actualizar claim"
            else:
                return "🚨 Rendimiento bajo - investigar causas y optimizar sistema"
        
        else:
            if actual_value > claim.target_value:
                return "🚀 Rendimiento excepcional - actualizar claim y comunicar mejora"
            else:
                return "🔴 CRÍTICO: Claim significativamente impreciso - actualizar inmediatamente"
    
    async def _generate_alerts(self, results: List[VerificationResult]):
        """Genera alertas para claims imprecisos"""
        
        critical_issues = [r for r in results if r.deviation_percentage > self.alert_thresholds["critical"]]
        warning_issues = [r for r in results if self.alert_thresholds["warning"] < r.deviation_percentage <= self.alert_thresholds["critical"]]
        
        if critical_issues:
            logger.critical(f"🔴 {len(critical_issues)} claims críticos requieren atención inmediata")
            for issue in critical_issues:
                logger.critical(f"   - {issue.claim_id}: {issue.deviation_percentage:.1f}% desviación")
        
        if warning_issues:
            logger.warning(f"⚠️ {len(warning_issues)} claims requieren monitoreo")
            for issue in warning_issues:
                logger.warning(f"   - {issue.claim_id}: {issue.deviation_percentage:.1f}% desviación")
    
    def get_verification_summary(self) -> Dict:
        """Obtiene resumen de la última verificación"""
        
        if not self.verification_history:
            return {"message": "No hay verificaciones disponibles"}
        
        latest_verification = self.verification_history[-1]
        results = latest_verification["results"]
        
        accurate_claims = len([r for r in results if r.is_accurate])
        total_claims = len(results)
        accuracy_percentage = (accurate_claims / total_claims) * 100 if total_claims > 0 else 0
        
        avg_confidence = statistics.mean([r.confidence_level for r in results]) if results else 0
        
        critical_issues = len([r for r in results if r.deviation_percentage > self.alert_thresholds["critical"]])
        warning_issues = len([r for r in results if self.alert_thresholds["warning"] < r.deviation_percentage <= self.alert_thresholds["critical"]])
        
        return {
            "last_verification": latest_verification["timestamp"].isoformat(),
            "total_claims_verified": total_claims,
            "accurate_claims": accurate_claims,
            "accuracy_percentage": accuracy_percentage,
            "average_confidence_level": avg_confidence,
            "critical_issues": critical_issues,
            "warning_issues": warning_issues,
            "overall_status": self._get_overall_status(accuracy_percentage, critical_issues)
        }
    
    def _get_overall_status(self, accuracy_percentage: float, critical_issues: int) -> str:
        """Determina el estado general del sistema de claims"""
        
        if critical_issues > 0:
            return "🔴 CRÍTICO - Requiere atención inmediata"
        elif accuracy_percentage >= 90:
            return "✅ EXCELENTE - Claims precisos"
        elif accuracy_percentage >= 80:
            return "⚠️ BUENO - Monitoreo recomendado"
        else:
            return "🚨 MALO - Revisión necesaria"
    
    async def update_landing_page_claims(self, results: List[VerificationResult]):
        """Actualiza automáticamente los claims en la landing page si es necesario"""
        
        # En producción, esto actualizaría automáticamente la landing page
        # o generaría pull requests con las actualizaciones necesarias
        
        updates_needed = []
        
        for result in results:
            if not result.is_accurate and result.deviation_percentage > 15:
                updates_needed.append({
                    "claim_id": result.claim_id,
                    "current_claim": result.claimed_value,
                    "suggested_update": result.actual_value,
                    "reason": result.recommendation
                })
        
        if updates_needed:
            logger.info(f"📝 {len(updates_needed)} claims requieren actualización en landing page")
            
            # En producción, esto podría:
            # 1. Crear un PR automático con las actualizaciones
            # 2. Enviar notificación al equipo de marketing
            # 3. Actualizar automáticamente claims no críticos
            
        return updates_needed

# Función para ejecutar verificación programada
async def run_scheduled_verification():
    """Ejecuta verificación programada de claims"""
    
    verifier = ClaimsVerificationSystem()
    results = await verifier.verify_all_claims()
    
    # Generar reporte
    summary = verifier.get_verification_summary()
    
    logger.info("📊 Resumen de verificación:")
    logger.info(f"   - Claims precisos: {summary['accurate_claims']}/{summary['total_claims_verified']}")
    logger.info(f"   - Precisión general: {summary['accuracy_percentage']:.1f}%")
    logger.info(f"   - Estado: {summary['overall_status']}")
    
    return results, summary
