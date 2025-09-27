"""
Sistema de Aprendizaje Automático para Optimización de Conversiones
Anclora RAG - Conversion Learning System
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

class ConversionComplexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    CRITICAL = "critical"

class ConversionStatus(Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    RETRY_NEEDED = "retry_needed"

@dataclass
class ConversionPattern:
    """Patrón de conversión aprendido"""
    pattern_id: str
    document_characteristics: Dict
    agent_sequence: List[str]
    processing_time: float
    success_rate: float
    complexity: ConversionComplexity
    optimization_score: float
    usage_count: int
    last_used: datetime
    created_at: datetime

@dataclass
class ConversionExperience:
    """Experiencia individual de conversión"""
    conversion_id: str
    document_hash: str
    document_type: str
    file_size: int
    content_characteristics: Dict
    agent_sequence_used: List[str]
    processing_time: float
    status: ConversionStatus
    quality_score: float
    user_satisfaction: Optional[float]
    errors_encountered: List[str]
    optimizations_applied: List[str]
    timestamp: datetime

class ConversionLearningSystem:
    """Sistema principal de aprendizaje de conversiones"""
    
    def __init__(self, data_path: str = "data/learning"):
        self.data_path = data_path
        self.patterns_file = os.path.join(data_path, "conversion_patterns.pkl")
        self.experiences_file = os.path.join(data_path, "conversion_experiences.pkl")
        self.vectorizer_file = os.path.join(data_path, "content_vectorizer.pkl")
        
        # Crear directorio si no existe
        os.makedirs(data_path, exist_ok=True)
        
        # Cargar datos existentes
        self.patterns: Dict[str, ConversionPattern] = self._load_patterns()
        self.experiences: List[ConversionExperience] = self._load_experiences()
        self.content_vectorizer = self._load_or_create_vectorizer()
        
        # Configuración de aprendizaje
        self.min_pattern_usage = 3  # Mínimo uso para considerar patrón válido
        self.similarity_threshold = 0.8  # Umbral de similitud para matching
        self.learning_rate = 0.1  # Tasa de aprendizaje para optimización
        
    def record_conversion_experience(self, experience: ConversionExperience) -> None:
        """Registra una nueva experiencia de conversión"""
        self.experiences.append(experience)
        
        # Actualizar patrones existentes o crear nuevos
        self._update_or_create_pattern(experience)
        
        # Guardar datos
        self._save_experiences()
        self._save_patterns()
        
        print(f"✅ Experiencia registrada: {experience.conversion_id}")
    
    def predict_optimal_conversion_strategy(self, document_characteristics: Dict) -> Dict:
        """Predice la estrategia óptima para un documento"""
        
        # Buscar patrones similares
        similar_patterns = self._find_similar_patterns(document_characteristics)
        
        if not similar_patterns:
            return self._get_default_strategy(document_characteristics)
        
        # Seleccionar el mejor patrón basado en éxito y optimización
        best_pattern = max(similar_patterns, 
                          key=lambda p: p.success_rate * p.optimization_score)
        
        # Generar recomendación
        recommendation = {
            "recommended_agent_sequence": best_pattern.agent_sequence,
            "estimated_processing_time": best_pattern.processing_time,
            "confidence_score": best_pattern.success_rate,
            "complexity_level": best_pattern.complexity.value,
            "optimization_tips": self._get_optimization_tips(best_pattern),
            "similar_cases_count": best_pattern.usage_count,
            "pattern_id": best_pattern.pattern_id
        }
        
        return recommendation
    
    def _find_similar_patterns(self, doc_characteristics: Dict) -> List[ConversionPattern]:
        """Encuentra patrones similares basados en características del documento"""
        similar_patterns = []
        
        for pattern in self.patterns.values():
            similarity_score = self._calculate_similarity(
                doc_characteristics, 
                pattern.document_characteristics
            )
            
            if similarity_score >= self.similarity_threshold:
                similar_patterns.append(pattern)
        
        return similar_patterns
    
    def _calculate_similarity(self, doc1: Dict, doc2: Dict) -> float:
        """Calcula similitud entre características de documentos"""
        
        # Similitud por tipo de archivo
        type_similarity = 1.0 if doc1.get('file_type') == doc2.get('file_type') else 0.5
        
        # Similitud por tamaño (normalizada)
        size1 = doc1.get('file_size', 0)
        size2 = doc2.get('file_size', 0)
        size_similarity = 1.0 - abs(size1 - size2) / max(size1, size2, 1)
        
        # Similitud por contenido (usando TF-IDF si disponible)
        content_similarity = 0.8  # Default si no hay contenido para comparar
        
        if 'content_preview' in doc1 and 'content_preview' in doc2:
            try:
                vectors = self.content_vectorizer.transform([
                    doc1['content_preview'], 
                    doc2['content_preview']
                ])
                content_similarity = cosine_similarity(vectors)[0][1]
            except:
                pass
        
        # Similitud por complejidad estructural
        complexity1 = doc1.get('structural_complexity', 0.5)
        complexity2 = doc2.get('structural_complexity', 0.5)
        complexity_similarity = 1.0 - abs(complexity1 - complexity2)
        
        # Peso ponderado de similitudes
        total_similarity = (
            type_similarity * 0.3 +
            size_similarity * 0.2 +
            content_similarity * 0.4 +
            complexity_similarity * 0.1
        )
        
        return total_similarity
    
    def _update_or_create_pattern(self, experience: ConversionExperience) -> None:
        """Actualiza patrón existente o crea uno nuevo"""
        
        # Buscar patrón existente similar
        pattern_key = self._generate_pattern_key(experience)
        
        if pattern_key in self.patterns:
            # Actualizar patrón existente
            pattern = self.patterns[pattern_key]
            pattern.usage_count += 1
            pattern.last_used = experience.timestamp
            
            # Actualizar métricas con promedio ponderado
            alpha = self.learning_rate
            pattern.processing_time = (1 - alpha) * pattern.processing_time + alpha * experience.processing_time
            
            # Actualizar tasa de éxito
            if experience.status == ConversionStatus.SUCCESS:
                pattern.success_rate = (1 - alpha) * pattern.success_rate + alpha * 1.0
            else:
                pattern.success_rate = (1 - alpha) * pattern.success_rate + alpha * 0.0
            
            # Recalcular score de optimización
            pattern.optimization_score = self._calculate_optimization_score(pattern)
            
        else:
            # Crear nuevo patrón
            new_pattern = ConversionPattern(
                pattern_id=pattern_key,
                document_characteristics=experience.content_characteristics,
                agent_sequence=experience.agent_sequence_used,
                processing_time=experience.processing_time,
                success_rate=1.0 if experience.status == ConversionStatus.SUCCESS else 0.0,
                complexity=self._determine_complexity(experience),
                optimization_score=0.5,  # Score inicial neutral
                usage_count=1,
                last_used=experience.timestamp,
                created_at=experience.timestamp
            )
            
            new_pattern.optimization_score = self._calculate_optimization_score(new_pattern)
            self.patterns[pattern_key] = new_pattern
    
    def _generate_pattern_key(self, experience: ConversionExperience) -> str:
        """Genera clave única para el patrón basada en características"""
        key_data = {
            'file_type': experience.document_type,
            'size_range': self._get_size_range(experience.file_size),
            'agent_sequence': tuple(experience.agent_sequence_used),
            'complexity': self._determine_complexity(experience).value
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def _determine_complexity(self, experience: ConversionExperience) -> ConversionComplexity:
        """Determina la complejidad de la conversión"""
        
        # Factores de complejidad
        time_factor = experience.processing_time / 60  # Normalizar a minutos
        error_factor = len(experience.errors_encountered)
        agent_factor = len(experience.agent_sequence_used)
        
        complexity_score = time_factor + error_factor * 0.5 + agent_factor * 0.3
        
        if complexity_score < 1.0:
            return ConversionComplexity.SIMPLE
        elif complexity_score < 3.0:
            return ConversionComplexity.MEDIUM
        elif complexity_score < 6.0:
            return ConversionComplexity.COMPLEX
        else:
            return ConversionComplexity.CRITICAL
    
    def _calculate_optimization_score(self, pattern: ConversionPattern) -> float:
        """Calcula score de optimización del patrón"""
        
        # Factores positivos
        success_factor = pattern.success_rate
        usage_factor = min(pattern.usage_count / 10, 1.0)  # Normalizar uso
        recency_factor = self._calculate_recency_factor(pattern.last_used)
        
        # Factores negativos (penalizaciones)
        time_penalty = max(0, (pattern.processing_time - 30) / 120)  # Penalizar > 30s
        complexity_penalty = {
            ConversionComplexity.SIMPLE: 0,
            ConversionComplexity.MEDIUM: 0.1,
            ConversionComplexity.COMPLEX: 0.2,
            ConversionComplexity.CRITICAL: 0.3
        }[pattern.complexity]
        
        optimization_score = (
            success_factor * 0.4 +
            usage_factor * 0.3 +
            recency_factor * 0.2 +
            (1 - time_penalty) * 0.1 -
            complexity_penalty
        )
        
        return max(0.0, min(1.0, optimization_score))
    
    def _calculate_recency_factor(self, last_used: datetime) -> float:
        """Calcula factor de recencia (más reciente = mejor)"""
        days_ago = (datetime.now() - last_used).days
        return max(0.1, 1.0 - (days_ago / 30))  # Decae en 30 días
    
    def _get_size_range(self, file_size: int) -> str:
        """Categoriza tamaño de archivo"""
        if file_size < 1024 * 1024:  # < 1MB
            return "small"
        elif file_size < 100 * 1024 * 1024:  # < 100MB
            return "medium"
        elif file_size < 50 * 1024 * 1024:  # < 50MB
            return "large"
        else:
            return "xlarge"
    
    def _get_default_strategy(self, doc_characteristics: Dict) -> Dict:
        """Estrategia por defecto cuando no hay patrones similares"""
        return {
            "recommended_agent_sequence": ["document_analyzer", "content_extractor", "embedding_generator"],
            "estimated_processing_time": 45.0,
            "confidence_score": 0.7,
            "complexity_level": "medium",
            "optimization_tips": ["Primera conversión de este tipo", "Se aprenderá del resultado"],
            "similar_cases_count": 0,
            "pattern_id": "default"
        }
    
    def _get_optimization_tips(self, pattern: ConversionPattern) -> List[str]:
        """Genera tips de optimización basados en el patrón"""
        tips = []
        
        if pattern.processing_time > 60:
            tips.append("Considerar procesamiento en paralelo para documentos similares")
        
        if pattern.success_rate < 0.9:
            tips.append("Patrón con algunas fallas, monitorear de cerca")
        
        if pattern.complexity == ConversionComplexity.COMPLEX:
            tips.append("Documento complejo, asignar recursos adicionales")
        
        if pattern.usage_count > 10:
            tips.append("Patrón bien establecido, alta confiabilidad")
        
        return tips or ["Patrón estándar, proceder normalmente"]
    
    def get_learning_analytics(self) -> Dict:
        """Obtiene analytics del sistema de aprendizaje"""
        
        total_patterns = len(self.patterns)
        total_experiences = len(self.experiences)
        
        if not self.experiences:
            return {"message": "No hay datos de aprendizaje disponibles"}
        
        # Calcular métricas
        avg_processing_time = np.mean([exp.processing_time for exp in self.experiences])
        success_rate = len([exp for exp in self.experiences if exp.status == ConversionStatus.SUCCESS]) / total_experiences
        
        complexity_distribution = {}
        for pattern in self.patterns.values():
            complexity = pattern.complexity.value
            complexity_distribution[complexity] = complexity_distribution.get(complexity, 0) + 1
        
        return {
            "total_patterns_learned": total_patterns,
            "total_conversion_experiences": total_experiences,
            "average_processing_time": round(avg_processing_time, 2),
            "overall_success_rate": round(success_rate * 100, 2),
            "complexity_distribution": complexity_distribution,
            "most_used_patterns": self._get_top_patterns(5),
            "learning_efficiency": self._calculate_learning_efficiency()
        }
    
    def _get_top_patterns(self, limit: int) -> List[Dict]:
        """Obtiene los patrones más utilizados"""
        sorted_patterns = sorted(
            self.patterns.values(), 
            key=lambda p: p.usage_count, 
            reverse=True
        )
        
        return [
            {
                "pattern_id": p.pattern_id,
                "usage_count": p.usage_count,
                "success_rate": round(p.success_rate * 100, 2),
                "avg_processing_time": round(p.processing_time, 2),
                "complexity": p.complexity.value
            }
            for p in sorted_patterns[:limit]
        ]
    
    def _calculate_learning_efficiency(self) -> float:
        """Calcula eficiencia del aprendizaje"""
        if not self.experiences:
            return 0.0
        
        recent_experiences = [
            exp for exp in self.experiences 
            if (datetime.now() - exp.timestamp).days <= 7
        ]
        
        if not recent_experiences:
            return 0.0
        
        recent_success_rate = len([
            exp for exp in recent_experiences 
            if exp.status == ConversionStatus.SUCCESS
        ]) / len(recent_experiences)
        
        return round(recent_success_rate * 100, 2)
    
    def _load_patterns(self) -> Dict[str, ConversionPattern]:
        """Carga patrones desde archivo"""
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        return {}
    
    def _save_patterns(self) -> None:
        """Guarda patrones en archivo"""
        with open(self.patterns_file, 'wb') as f:
            pickle.dump(self.patterns, f)
    
    def _load_experiences(self) -> List[ConversionExperience]:
        """Carga experiencias desde archivo"""
        if os.path.exists(self.experiences_file):
            try:
                with open(self.experiences_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        return []
    
    def _save_experiences(self) -> None:
        """Guarda experiencias en archivo"""
        with open(self.experiences_file, 'wb') as f:
            pickle.dump(self.experiences, f)
    
    def _load_or_create_vectorizer(self):
        """Carga o crea vectorizador TF-IDF"""
        if os.path.exists(self.vectorizer_file):
            try:
                with open(self.vectorizer_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        
        # Crear nuevo vectorizador
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        return vectorizer

# Integración con el sistema principal
class SmartAgentOrchestrator:
    """Orquestador de agentes mejorado con aprendizaje automático"""

    def __init__(self):
        self.learning_system = ConversionLearningSystem()
        self.agents = {
            "document_analyzer": self._document_analyzer,
            "content_extractor": self._content_extractor,
            "embedding_generator": self._embedding_generator,
            "format_converter": self._format_converter,
            "quality_validator": self._quality_validator
        }

    async def process_document_with_learning(self, document_data: Dict) -> Dict:
        """Procesa documento usando aprendizaje automático"""

        start_time = datetime.now()

        # 1. Analizar características del documento
        doc_characteristics = await self._analyze_document_characteristics(document_data)

        # 2. Obtener estrategia recomendada por el sistema de aprendizaje
        strategy = self.learning_system.predict_optimal_conversion_strategy(doc_characteristics)

        print(f"🧠 Estrategia recomendada: {strategy['recommended_agent_sequence']}")
        print(f"⏱️ Tiempo estimado: {strategy['estimated_processing_time']}s")
        print(f"🎯 Confianza: {strategy['confidence_score']*100:.1f}%")

        # 3. Ejecutar secuencia de agentes recomendada
        result = await self._execute_agent_sequence(
            document_data,
            strategy['recommended_agent_sequence']
        )

        # 4. Registrar experiencia para aprendizaje futuro
        processing_time = (datetime.now() - start_time).total_seconds()

        experience = ConversionExperience(
            conversion_id=f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            document_hash=self._calculate_document_hash(document_data),
            document_type=document_data.get('file_type', 'unknown'),
            file_size=document_data.get('file_size', 0),
            content_characteristics=doc_characteristics,
            agent_sequence_used=strategy['recommended_agent_sequence'],
            processing_time=processing_time,
            status=ConversionStatus.SUCCESS if result['success'] else ConversionStatus.FAILED,
            quality_score=result.get('quality_score', 0.8),
            user_satisfaction=None,  # Se actualizará con feedback del usuario
            errors_encountered=result.get('errors', []),
            optimizations_applied=result.get('optimizations', []),
            timestamp=datetime.now()
        )

        # Registrar experiencia para aprendizaje
        self.learning_system.record_conversion_experience(experience)

        # Agregar información de aprendizaje al resultado
        result['learning_info'] = {
            'pattern_used': strategy['pattern_id'],
            'confidence_score': strategy['confidence_score'],
            'estimated_vs_actual_time': {
                'estimated': strategy['estimated_processing_time'],
                'actual': processing_time,
                'accuracy': abs(strategy['estimated_processing_time'] - processing_time) / strategy['estimated_processing_time']
            }
        }

        return result

    async def _analyze_document_characteristics(self, document_data: Dict) -> Dict:
        """Analiza características del documento para el aprendizaje"""

        characteristics = {
            'file_type': document_data.get('file_type', 'unknown'),
            'file_size': document_data.get('file_size', 0),
            'has_images': document_data.get('has_images', False),
            'has_tables': document_data.get('has_tables', False),
            'page_count': document_data.get('page_count', 1),
            'language': document_data.get('language', 'unknown'),
            'structural_complexity': await self._calculate_structural_complexity(document_data),
            'content_preview': document_data.get('content_preview', '')[:500]  # Primeros 500 chars
        }

        return characteristics

    async def _calculate_structural_complexity(self, document_data: Dict) -> float:
        """Calcula complejidad estructural del documento"""

        complexity_score = 0.0

        # Factores de complejidad
        if document_data.get('has_images', False):
            complexity_score += 0.2

        if document_data.get('has_tables', False):
            complexity_score += 0.3

        page_count = document_data.get('page_count', 1)
        if page_count > 10:
            complexity_score += 0.2
        elif page_count > 50:
            complexity_score += 0.4

        file_size = document_data.get('file_size', 0)
        if file_size > 100 * 1024 * 1024:  # > 100MB
            complexity_score += 0.2

        # Normalizar entre 0 y 1
        return min(1.0, complexity_score)

    async def _execute_agent_sequence(self, document_data: Dict, agent_sequence: List[str]) -> Dict:
        """Ejecuta secuencia de agentes"""

        result = {
            'success': True,
            'errors': [],
            'optimizations': [],
            'quality_score': 0.8,
            'processed_data': document_data
        }

        for agent_name in agent_sequence:
            if agent_name in self.agents:
                try:
                    agent_result = await self.agents[agent_name](result['processed_data'])
                    result['processed_data'].update(agent_result)

                    if agent_result.get('optimization_applied'):
                        result['optimizations'].append(f"{agent_name}: {agent_result['optimization_applied']}")

                except Exception as e:
                    result['errors'].append(f"{agent_name}: {str(e)}")
                    result['success'] = False

        return result

    def _calculate_document_hash(self, document_data: Dict) -> str:
        """Calcula hash único del documento"""
        hash_data = {
            'file_name': document_data.get('file_name', ''),
            'file_size': document_data.get('file_size', 0),
            'file_type': document_data.get('file_type', '')
        }
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.md5(hash_string.encode()).hexdigest()

    # Métodos de agentes (simplificados para el ejemplo)
    async def _document_analyzer(self, data: Dict) -> Dict:
        return {"analysis_complete": True, "optimization_applied": "Fast analysis for known format"}

    async def _content_extractor(self, data: Dict) -> Dict:
        return {"content_extracted": True, "optimization_applied": "Optimized extraction pattern"}

    async def _embedding_generator(self, data: Dict) -> Dict:
        return {"embeddings_created": True, "optimization_applied": "Cached similar embeddings"}

    async def _format_converter(self, data: Dict) -> Dict:
        return {"format_converted": True, "optimization_applied": "Direct conversion path"}

    async def _quality_validator(self, data: Dict) -> Dict:
        return {"quality_validated": True, "optimization_applied": "Skip redundant checks"}
