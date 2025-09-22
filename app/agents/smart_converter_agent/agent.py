"""Agente de conversión inteligente con optimización automática."""

from __future__ import annotations

import time
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

from app.agents.base import AgentResponse, AgentTask, BaseAgent
from app.rag_core.conversion_advisor import ConversionAdvisor, FormatRecommendation
from common.observability import record_agent_invocation


@dataclass
class ConversionResult:
    """Resultado de una conversión inteligente."""
    
    success: bool
    original_file: str
    converted_file: Optional[str]
    format_used: str
    optimization_applied: List[str]
    quality_score: float
    file_size_reduction: float
    processing_time: float
    warnings: List[str]
    metadata: Dict[str, Any]


class SmartConverterAgent(BaseAgent):
    """Agente que realiza conversiones inteligentes con optimización automática."""

    def __init__(self) -> None:
        super().__init__(name="smart_converter_agent")
        self.conversion_advisor = ConversionAdvisor()

    def can_handle(self, task: AgentTask) -> bool:
        """Maneja tareas de conversión inteligente."""
        return task.task_type in [
            "smart_conversion", 
            "format_optimization", 
            "batch_conversion",
            "conversion_analysis"
        ]

    def handle(self, task: AgentTask) -> AgentResponse:
        """Ejecuta conversión inteligente."""
        
        start_time = time.perf_counter()
        
        try:
            file_path = task.get("file_path")
            target_format = task.get("target_format")
            intended_use = task.get("intended_use", "general")
            optimization_level = task.get("optimization_level", "medium")
            batch_mode = task.get("batch_mode", False)
            
            if not file_path:
                return AgentResponse(
                    success=False,
                    error="file_path_required"
                )
            
            if batch_mode:
                result = self._handle_batch_conversion(file_path, target_format, intended_use, optimization_level)
            else:
                result = self._handle_single_conversion(file_path, target_format, intended_use, optimization_level)
            
            duration = time.perf_counter() - start_time
            record_agent_invocation(
                self.name,
                task.task_type,
                "success" if result.success else "error",
                duration_seconds=duration
            )
            
            return AgentResponse(
                success=result.success,
                data=result.__dict__
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
                error=f"conversion_failed: {str(e)}"
            )

    def _handle_single_conversion(self, file_path: str, target_format: Optional[str], 
                                intended_use: str, optimization_level: str) -> ConversionResult:
        """Maneja conversión de un solo archivo."""
        
        start_time = time.perf_counter()
        original_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        # Obtener recomendación inteligente
        source_format = Path(file_path).suffix.lower()
        recommendation = self.conversion_advisor.recommend(
            source_format=source_format,
            intended_use=intended_use,
            metadata=self._analyze_file_metadata(file_path)
        )
        
        # Usar formato recomendado si no se especifica uno
        final_format = target_format or recommendation.recommended_format
        
        # Aplicar optimizaciones
        optimizations = self._determine_optimizations(recommendation, optimization_level)
        
        # Realizar conversión
        converted_file = self._execute_conversion(file_path, final_format, optimizations)
        
        # Calcular métricas
        processing_time = time.perf_counter() - start_time
        new_size = os.path.getsize(converted_file) if converted_file and os.path.exists(converted_file) else original_size
        size_reduction = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0
        quality_score = self._calculate_quality_score(file_path, converted_file, recommendation)
        
        return ConversionResult(
            success=converted_file is not None,
            original_file=file_path,
            converted_file=converted_file,
            format_used=final_format,
            optimization_applied=optimizations,
            quality_score=quality_score,
            file_size_reduction=size_reduction,
            processing_time=processing_time,
            warnings=recommendation.warnings,
            metadata={
                "recommendation": recommendation.to_dict(),
                "original_size_bytes": original_size,
                "converted_size_bytes": new_size,
                "optimization_level": optimization_level
            }
        )

    def _handle_batch_conversion(self, directory_path: str, target_format: Optional[str], 
                               intended_use: str, optimization_level: str) -> ConversionResult:
        """Maneja conversión por lotes."""
        
        start_time = time.perf_counter()
        
        # Encontrar archivos para convertir
        files_to_convert = self._find_convertible_files(directory_path)
        
        converted_files = []
        total_original_size = 0
        total_converted_size = 0
        all_optimizations = []
        all_warnings = []
        
        for file_path in files_to_convert:
            try:
                result = self._handle_single_conversion(file_path, target_format, intended_use, optimization_level)
                if result.success:
                    converted_files.append(result.converted_file)
                    total_original_size += result.metadata.get("original_size_bytes", 0)
                    total_converted_size += result.metadata.get("converted_size_bytes", 0)
                    all_optimizations.extend(result.optimization_applied)
                    all_warnings.extend(result.warnings)
            except Exception as e:
                all_warnings.append(f"Error converting {file_path}: {str(e)}")
        
        processing_time = time.perf_counter() - start_time
        size_reduction = ((total_original_size - total_converted_size) / total_original_size * 100) if total_original_size > 0 else 0
        
        return ConversionResult(
            success=len(converted_files) > 0,
            original_file=directory_path,
            converted_file=f"{len(converted_files)} files converted",
            format_used=target_format or "auto-detected",
            optimization_applied=list(set(all_optimizations)),
            quality_score=0.8,  # Score promedio para lotes
            file_size_reduction=size_reduction,
            processing_time=processing_time,
            warnings=all_warnings,
            metadata={
                "batch_mode": True,
                "files_processed": len(files_to_convert),
                "files_converted": len(converted_files),
                "total_original_size_bytes": total_original_size,
                "total_converted_size_bytes": total_converted_size
            }
        )

    def _analyze_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Analiza metadatos del archivo para optimizar conversión."""
        
        metadata = {}
        
        try:
            file_stats = os.stat(file_path)
            metadata.update({
                "file_size_bytes": file_stats.st_size,
                "file_size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                "creation_time": file_stats.st_ctime,
                "modification_time": file_stats.st_mtime
            })
            
            # Determinar tipo de contenido dominante basado en extensión
            extension = Path(file_path).suffix.lower()
            if extension in [".pdf", ".doc", ".docx", ".txt"]:
                metadata["dominant_content"] = "text"
            elif extension in [".jpg", ".png", ".gif", ".bmp"]:
                metadata["dominant_content"] = "image"
            elif extension in [".mp4", ".avi", ".mov"]:
                metadata["dominant_content"] = "video"
            elif extension in [".mp3", ".wav", ".flac"]:
                metadata["dominant_content"] = "audio"
            else:
                metadata["dominant_content"] = "mixed"
            
            # Determinar si es archivo grande
            metadata["is_large_file"] = file_stats.st_size > 50 * 1024 * 1024  # 50MB
            
        except Exception as e:
            metadata["analysis_error"] = str(e)
        
        return metadata

    def _determine_optimizations(self, recommendation: FormatRecommendation, optimization_level: str) -> List[str]:
        """Determina qué optimizaciones aplicar."""
        
        optimizations = []
        
        # Optimizaciones básicas
        if optimization_level in ["medium", "high"]:
            optimizations.extend([
                "metadata_cleanup",
                "compression_optimization"
            ])
        
        # Optimizaciones avanzadas
        if optimization_level == "high":
            optimizations.extend([
                "image_compression",
                "font_subsetting",
                "structure_optimization"
            ])
        
        # Optimizaciones específicas del formato
        if recommendation.recommended_format == "pdf":
            optimizations.extend([
                "pdf_linearization",
                "duplicate_removal"
            ])
        
        return optimizations

    def _execute_conversion(self, source_file: str, target_format: str, optimizations: List[str]) -> Optional[str]:
        """Ejecuta la conversión real del archivo."""
        
        # Esta es una implementación simulada
        # En un entorno real, aquí se integrarían herramientas como:
        # - LibreOffice para documentos
        # - ImageMagick para imágenes
        # - FFmpeg para multimedia
        # - Pandoc para conversiones de texto
        
        try:
            source_path = Path(source_file)
            target_path = source_path.with_suffix(f".{target_format}")
            
            # Simular conversión
            if self._simulate_conversion(source_file, str(target_path), optimizations):
                return str(target_path)
            
        except Exception as e:
            print(f"Conversion error: {e}")
        
        return None

    def _simulate_conversion(self, source: str, target: str, optimizations: List[str]) -> bool:
        """Simula una conversión exitosa."""
        
        # En implementación real, aquí iría la lógica de conversión
        # Por ahora, simulamos que la conversión es exitosa
        
        try:
            # Crear archivo de destino simulado
            with open(target, 'w') as f:
                f.write(f"Converted from {source} with optimizations: {', '.join(optimizations)}")
            return True
        except Exception:
            return False

    def _calculate_quality_score(self, original_file: str, converted_file: Optional[str], 
                                recommendation: FormatRecommendation) -> float:
        """Calcula un score de calidad de la conversión."""
        
        if not converted_file or not os.path.exists(converted_file):
            return 0.0
        
        # Factores de calidad
        base_score = 0.7
        
        # Bonus por seguir recomendaciones
        if recommendation.confidence == "alta":
            base_score += 0.2
        elif recommendation.confidence == "media":
            base_score += 0.1
        
        # Penalty por warnings
        if recommendation.warnings:
            base_score -= len(recommendation.warnings) * 0.05
        
        return min(1.0, max(0.0, base_score))

    def _find_convertible_files(self, directory: str) -> List[str]:
        """Encuentra archivos convertibles en un directorio."""
        
        convertible_extensions = {
            ".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff",
            ".mp4", ".avi", ".mov", ".wmv", ".flv",
            ".mp3", ".wav", ".flac", ".aac"
        }
        
        files = []
        try:
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if Path(filename).suffix.lower() in convertible_extensions:
                        files.append(os.path.join(root, filename))
        except Exception as e:
            print(f"Error scanning directory: {e}")
        
        return files
