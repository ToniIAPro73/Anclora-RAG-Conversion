"""
Orquestador Híbrido Anclora RAG
Combina velocidad de API directa con flexibilidad de N8N
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass

# Importar optimizador de velocidad
try:
    from optimization.speed_optimizations import SpeedOptimizer, OptimizationLevel
except ImportError:
    SpeedOptimizer = None
    OptimizationLevel = None

logger = logging.getLogger(__name__)

class ProcessingMode(Enum):
    FAST_PATH = "fast_path"      # Documentos simples, patrones conocidos
    COMPLEX_PATH = "complex_path" # Documentos complejos, requieren N8N
    LEARNING_PATH = "learning_path" # Nuevos tipos, aprendizaje activo

class ProcessingPriority(Enum):
    REALTIME = "realtime"        # < 10s respuesta
    STANDARD = "standard"        # < 30s respuesta  
    BATCH = "batch"             # < 5min respuesta

@dataclass
class ConversionRequest:
    request_id: str
    user_id: str
    document_data: Dict
    priority: ProcessingPriority
    callback_url: Optional[str] = None
    metadata: Optional[Dict] = None

@dataclass
class ConversionResult:
    request_id: str
    success: bool
    processing_mode: ProcessingMode
    processing_time: float
    result_data: Dict
    learning_applied: bool
    optimizations_used: List[str]
    errors: List[str] = None

class HybridOrchestrator:
    """Orquestador híbrido que combina velocidad y flexibilidad"""
    
    def __init__(self):
        self.n8n_webhook_url = "http://localhost:5678/webhook/process-document"
        self.learning_system = None  # Se inicializa lazy
        self.fast_path_cache = {}

        # Inicializar optimizador de velocidad
        self.speed_optimizer = SpeedOptimizer() if SpeedOptimizer else None

        self.processing_stats = {
            "fast_path_count": 0,
            "complex_path_count": 0,
            "learning_path_count": 0,
            "total_time_saved": 0.0,
            "ultra_fast_count": 0,  # Nuevas métricas
            "cache_hit_count": 0
        }
    
    async def process_conversion(self, request: ConversionRequest) -> ConversionResult:
        """Punto de entrada principal para conversiones"""
        
        start_time = datetime.now()
        logger.info(f"🚀 Iniciando conversión {request.request_id}")
        
        try:
            # 1. Determinar modo de procesamiento óptimo
            processing_mode = await self._determine_processing_mode(request)
            logger.info(f"📊 Modo seleccionado: {processing_mode.value}")
            
            # 2. Ejecutar según el modo determinado
            if processing_mode == ProcessingMode.FAST_PATH:
                result = await self._execute_fast_path(request)
            elif processing_mode == ProcessingMode.COMPLEX_PATH:
                result = await self._execute_complex_path(request)
            else:  # LEARNING_PATH
                result = await self._execute_learning_path(request)
            
            # 3. Calcular tiempo total
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 4. Crear resultado final
            conversion_result = ConversionResult(
                request_id=request.request_id,
                success=result.get('success', False),
                processing_mode=processing_mode,
                processing_time=processing_time,
                result_data=result,
                learning_applied=result.get('learning_applied', False),
                optimizations_used=result.get('optimizations_used', []),
                errors=result.get('errors', [])
            )
            
            # 5. Actualizar estadísticas
            await self._update_processing_stats(conversion_result)
            
            # 6. Callback asíncrono si se especificó
            if request.callback_url:
                asyncio.create_task(self._send_callback(request.callback_url, conversion_result))
            
            logger.info(f"✅ Conversión completada en {processing_time:.2f}s")
            return conversion_result
            
        except Exception as e:
            logger.error(f"❌ Error en conversión {request.request_id}: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ConversionResult(
                request_id=request.request_id,
                success=False,
                processing_mode=ProcessingMode.COMPLEX_PATH,  # Default fallback
                processing_time=processing_time,
                result_data={"error": str(e)},
                learning_applied=False,
                optimizations_used=[],
                errors=[str(e)]
            )
    
    async def _determine_processing_mode(self, request: ConversionRequest) -> ProcessingMode:
        """Determina el modo de procesamiento óptimo"""
        
        doc_data = request.document_data
        
        # Criterios para FAST_PATH (más agresivos para competir)
        fast_path_criteria = [
            doc_data.get('file_type') in ['pdf', 'txt', 'docx'],  # Formatos simples
            doc_data.get('file_size', 0) < 10 * 1024 * 1024,     # < 10MB (aumentado)
            not doc_data.get('has_images', False),                # Sin imágenes
            not doc_data.get('has_tables', False),                # Sin tablas
            doc_data.get('page_count', 1) < 50,                   # < 50 páginas (aumentado)
            request.priority == ProcessingPriority.REALTIME       # Prioridad alta
        ]

        # Si cumple la mayoría de criterios → FAST_PATH
        if sum(fast_path_criteria) >= 3:  # Umbral reducido para más fast paths
            # Verificar si tenemos patrón conocido
            pattern_key = self._generate_pattern_key(doc_data)
            if pattern_key in self.fast_path_cache:
                logger.info("⚡ Fast path: Patrón conocido encontrado")
                return ProcessingMode.FAST_PATH
        
        # Criterios para LEARNING_PATH
        learning_criteria = [
            doc_data.get('file_type') not in ['pdf', 'txt', 'docx', 'pptx'],  # Formato nuevo
            doc_data.get('structural_complexity', 0) > 0.7,                    # Alta complejidad
            not await self._has_similar_conversions(doc_data)                  # Sin conversiones similares
        ]
        
        if any(learning_criteria):
            logger.info("🧠 Learning path: Documento requiere aprendizaje")
            return ProcessingMode.LEARNING_PATH
        
        # Por defecto → COMPLEX_PATH (N8N orchestration)
        logger.info("🔄 Complex path: Procesamiento estándar con N8N")
        return ProcessingMode.COMPLEX_PATH
    
    async def _execute_fast_path(self, request: ConversionRequest) -> Dict:
        """Ejecución ultra-rápida para documentos simples con patrones conocidos"""

        logger.info("⚡ Ejecutando Fast Path Ultra-Optimizado")

        doc_data = request.document_data

        # Usar optimizador de velocidad si está disponible
        if self.speed_optimizer:
            try:
                # Determinar nivel de optimización según prioridad
                optimization_level = OptimizationLevel.ULTRA if request.priority == ProcessingPriority.REALTIME else OptimizationLevel.AGGRESSIVE

                # Procesar con optimizaciones avanzadas
                result = await self.speed_optimizer.optimize_document_processing(
                    doc_data,
                    self._fast_processing_function,
                    optimization_level
                )

                # Actualizar estadísticas
                if result.get('cache_hit'):
                    self.processing_stats['cache_hit_count'] += 1
                    self.processing_stats['ultra_fast_count'] += 1
                else:
                    self.processing_stats['fast_path_count'] += 1

                result.update({
                    'processing_mode': 'fast_path_optimized',
                    'learning_applied': True,
                    'optimizations_used': result.get('optimizations_used', []) + ['speed_optimizer']
                })

                return result

            except Exception as e:
                logger.error(f"❌ Error en speed optimizer: {str(e)}")
                # Fallback a método tradicional

        # Método tradicional como fallback
        pattern_key = self._generate_pattern_key(doc_data)
        cached_pattern = self.fast_path_cache.get(pattern_key)

        if not cached_pattern:
            logger.warning("⚠️ No hay patrón cached, fallback a complex path")
            return await self._execute_complex_path(request)

        try:
            # Ejecutar secuencia optimizada directamente
            result = await self._execute_cached_sequence(doc_data, cached_pattern)

            result.update({
                'success': True,
                'processing_mode': 'fast_path',
                'learning_applied': True,
                'optimizations_used': ['cached_pattern', 'direct_execution'],
                'pattern_confidence': cached_pattern.get('confidence', 0.8)
            })

            self.processing_stats['fast_path_count'] += 1
            return result

        except Exception as e:
            logger.error(f"❌ Error en fast path: {str(e)}")
            return await self._execute_complex_path(request)
    
    async def _execute_complex_path(self, request: ConversionRequest) -> Dict:
        """Ejecución a través de N8N para documentos complejos"""
        
        logger.info("🔄 Ejecutando Complex Path via N8N")
        
        try:
            # Preparar payload para N8N
            n8n_payload = {
                'request_id': request.request_id,
                'user_id': request.user_id,
                'document_data': request.document_data,
                'priority': request.priority.value,
                'processing_mode': 'complex_path',
                'timestamp': datetime.now().isoformat()
            }
            
            # Llamada asíncrona a N8N
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.n8n_webhook_url,
                    json=n8n_payload,
                    timeout=aiohttp.ClientTimeout(total=300)  # 5 min timeout
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # Procesar resultado de N8N
                        processed_result = await self._process_n8n_result(result, request)
                        
                        # Actualizar cache si es exitoso
                        if processed_result.get('success') and processed_result.get('cacheable', False):
                            await self._update_fast_path_cache(request.document_data, processed_result)
                        
                        self.processing_stats['complex_path_count'] += 1
                        return processed_result
                    
                    else:
                        raise Exception(f"N8N returned status {response.status}")
            
        except Exception as e:
            logger.error(f"❌ Error en complex path: {str(e)}")
            return {
                'success': False,
                'processing_mode': 'complex_path',
                'error': str(e),
                'fallback_attempted': True
            }
    
    async def _execute_learning_path(self, request: ConversionRequest) -> Dict:
        """Ejecución con aprendizaje activo para documentos nuevos"""
        
        logger.info("🧠 Ejecutando Learning Path")
        
        try:
            # 1. Ejecutar a través de N8N con logging extendido
            n8n_result = await self._execute_complex_path(request)
            
            # 2. Si es exitoso, registrar para aprendizaje
            if n8n_result.get('success'):
                await self._register_learning_experience(request, n8n_result)
                
                # 3. Intentar generar patrón inmediatamente si es prometedor
                if n8n_result.get('quality_score', 0) > 0.8:
                    await self._attempt_pattern_generation(request.document_data, n8n_result)
            
            # 4. Marcar como learning path
            n8n_result.update({
                'processing_mode': 'learning_path',
                'learning_applied': True,
                'optimizations_used': n8n_result.get('optimizations_used', []) + ['learning_registration']
            })
            
            self.processing_stats['learning_path_count'] += 1
            return n8n_result
            
        except Exception as e:
            logger.error(f"❌ Error en learning path: {str(e)}")
            return {
                'success': False,
                'processing_mode': 'learning_path',
                'error': str(e),
                'learning_attempted': True
            }
    
    async def _execute_cached_sequence(self, doc_data: Dict, cached_pattern: Dict) -> Dict:
        """Ejecuta secuencia de agentes desde cache"""
        
        agent_sequence = cached_pattern['agent_sequence']
        optimizations = cached_pattern.get('optimizations', {})
        
        result = {'processed_data': doc_data.copy()}
        
        for agent_name in agent_sequence:
            # Aplicar optimizaciones específicas del agente
            agent_config = optimizations.get(agent_name, {})
            
            # Simular ejecución de agente (en producción sería llamada real)
            agent_result = await self._execute_agent(agent_name, result['processed_data'], agent_config)
            result['processed_data'].update(agent_result)
        
        return result
    
    async def _execute_agent(self, agent_name: str, data: Dict, config: Dict) -> Dict:
        """Ejecuta un agente específico con configuración optimizada"""
        
        # Simulación - en producción sería llamada real a agentes
        await asyncio.sleep(0.1)  # Simular procesamiento
        
        return {
            f'{agent_name}_result': True,
            f'{agent_name}_optimization': config.get('optimization_applied', 'standard_processing')
        }
    
    def _generate_pattern_key(self, doc_data: Dict) -> str:
        """Genera clave para identificar patrones similares"""
        
        key_components = [
            doc_data.get('file_type', 'unknown'),
            'small' if doc_data.get('file_size', 0) < 1024*1024 else 'large',
            'simple' if not doc_data.get('has_images') and not doc_data.get('has_tables') else 'complex'
        ]
        
        return '_'.join(key_components)
    
    async def _has_similar_conversions(self, doc_data: Dict) -> bool:
        """Verifica si existen conversiones similares previas"""
        
        # En producción consultaría el learning system
        pattern_key = self._generate_pattern_key(doc_data)
        return pattern_key in self.fast_path_cache
    
    async def _process_n8n_result(self, n8n_result: Dict, request: ConversionRequest) -> Dict:
        """Procesa y enriquece resultado de N8N"""
        
        processed = n8n_result.copy()
        processed.update({
            'processing_mode': 'complex_path',
            'request_id': request.request_id,
            'cacheable': self._is_result_cacheable(n8n_result, request.document_data)
        })
        
        return processed
    
    def _is_result_cacheable(self, result: Dict, doc_data: Dict) -> bool:
        """Determina si el resultado puede ser cacheado para fast path"""
        
        return (
            result.get('success', False) and
            result.get('quality_score', 0) > 0.85 and
            doc_data.get('file_size', 0) < 5 * 1024 * 1024 and
            result.get('processing_time', 999) < 30
        )
    
    async def _update_fast_path_cache(self, doc_data: Dict, result: Dict) -> None:
        """Actualiza cache de fast path con nuevo patrón"""
        
        pattern_key = self._generate_pattern_key(doc_data)
        
        self.fast_path_cache[pattern_key] = {
            'agent_sequence': result.get('agent_sequence_used', []),
            'optimizations': result.get('optimizations_applied', {}),
            'confidence': result.get('quality_score', 0.8),
            'avg_processing_time': result.get('processing_time', 30),
            'usage_count': 1,
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"💾 Patrón cacheado: {pattern_key}")
    
    async def _register_learning_experience(self, request: ConversionRequest, result: Dict) -> None:
        """Registra experiencia para el sistema de aprendizaje"""
        
        # En producción llamaría al learning system
        logger.info(f"📚 Registrando experiencia de aprendizaje: {request.request_id}")
    
    async def _attempt_pattern_generation(self, doc_data: Dict, result: Dict) -> None:
        """Intenta generar patrón inmediatamente si es prometedor"""
        
        if result.get('quality_score', 0) > 0.9:
            await self._update_fast_path_cache(doc_data, result)
            logger.info("🚀 Patrón generado inmediatamente por alta calidad")
    
    async def _update_processing_stats(self, result: ConversionResult) -> None:
        """Actualiza estadísticas de procesamiento"""
        
        if result.processing_mode == ProcessingMode.FAST_PATH:
            # Calcular tiempo ahorrado vs complex path
            estimated_complex_time = 45.0  # Tiempo promedio complex path
            time_saved = max(0, estimated_complex_time - result.processing_time)
            self.processing_stats['total_time_saved'] += time_saved
    
    async def _send_callback(self, callback_url: str, result: ConversionResult) -> None:
        """Envía callback asíncrono con resultado"""
        
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(callback_url, json=result.__dict__)
            logger.info(f"📞 Callback enviado: {callback_url}")
        except Exception as e:
            logger.error(f"❌ Error enviando callback: {str(e)}")
    
    def get_processing_stats(self) -> Dict:
        """Obtiene estadísticas de procesamiento"""
        
        total_processed = sum([
            self.processing_stats['fast_path_count'],
            self.processing_stats['complex_path_count'], 
            self.processing_stats['learning_path_count']
        ])
        
        return {
            **self.processing_stats,
            'total_processed': total_processed,
            'fast_path_percentage': (self.processing_stats['fast_path_count'] / max(total_processed, 1)) * 100,
            'avg_time_saved_per_fast_path': (
                self.processing_stats['total_time_saved'] / 
                max(self.processing_stats['fast_path_count'], 1)
            )
        }

    async def _fast_processing_function(self, document_data: Dict) -> Dict:
        """Función de procesamiento rápido para el optimizador"""

        # Simular procesamiento ultra-rápido
        await asyncio.sleep(0.1)  # Procesamiento mínimo

        return {
            "success": True,
            "processed_content": "Ultra-fast processed content",
            "processing_method": "optimized_fast_path",
            "quality_score": 0.9
        }
