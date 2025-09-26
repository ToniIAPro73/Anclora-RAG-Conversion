"""
Adaptador principal para conversión de formatos NotebookLM → Anclora RAG
"""

import re
from typing import Dict, List, Tuple
from pathlib import Path
from datetime import datetime

from .format_detector import FormatDetector, SourceFormat
from .field_mapper import FieldMapper

class NotebookLMAdapter:
    def __init__(self):
        self.detector = FormatDetector()
        self.mapper = FieldMapper()
        self.log = []
    
    def convert_content(self, content: str, original_filename: str = "") -> Dict:
        """
        Convierte contenido de cualquier formato detectado a Anclora RAG
        
        Returns: Dict con resultado y metadata
        """
        # Detectar formato
        detection_result = self.detector.detect_format(content)
        
        if detection_result['format'] == SourceFormat.UNKNOWN:
            return {
                'success': False,
                'error': 'Formato no reconocido',
                'detection': detection_result
            }
        
        # Convertir según formato
        if detection_result['format'] == SourceFormat.NOTEBOOKLM:
            converted_content, stats = self._convert_notebooklm(content)
        elif detection_result['format'] == SourceFormat.ANCLORA:
            # Ya está en formato correcto
            converted_content = content
            stats = {'sources': self._count_anclora_sources(content)}
        else:
            return {
                'success': False,
                'error': f'Formato {detection_result["format"].value} no soportado aún',
                'detection': detection_result
            }
        
        return {
            'success': True,
            'content': converted_content,
            'stats': stats,
            'detection': detection_result,
            'metadata': {
                'original_format': detection_result['format'].value,
                'conversion_date': datetime.now().isoformat(),
                'original_filename': original_filename,
                'sources_converted': stats.get('sources_converted', 0)
            }
        }
    
    def _convert_notebooklm(self, content: str) -> Tuple[str, Dict]:
        """Conversión específica para formato NotebookLM"""
        output_lines = [
            "# Fuentes Bibliográficas Convertidas desde NotebookLM",
            f"## Conversión automática: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "## Instrucciones: Este documento fue convertido automáticamente",
            ""
        ]
        
        # Extraer bloques de fuentes
        source_blocks = self.mapper.extract_source_blocks(content)
        successful_conversions = 0
        
        for i, block in enumerate(source_blocks, 1):
            try:
                mapped_fields = self.mapper.map_fields(block, i)
                
                # Añadir al output
                output_lines.append(f"**ID:** [{mapped_fields['ID']}]")
                for key, value in mapped_fields.items():
                    if key != 'ID':
                        output_lines.append(f"**{key}:** {value}")
                output_lines.append("")
                
                successful_conversions += 1
                self.log.append(f"✓ Fuente {i} convertida exitosamente")
                
            except Exception as e:
                self.log.append(f"✗ Error en fuente {i}: {str(e)}")
                # Añadir bloque problematico para revisión manual
                output_lines.append(f"# ERROR en conversión automática - Fuente {i}")
                output_lines.append(f"# Bloque original:")
                output_lines.extend(block.split('\n'))
                output_lines.append("")
        
        stats = {
            'sources_total': len(source_blocks),
            'sources_converted': successful_conversions,
            'conversion_rate': (successful_conversions / len(source_blocks) * 100) if source_blocks else 0
        }
        
        return "\n".join(output_lines), stats
    
    def _count_anclora_sources(self, content: str) -> int:
        """Cuenta fuentes en formato Anclora"""
        return len(re.findall(r'\*\*ID:\*\*\s*\[SRC-\d+\]', content))
    
    def generate_report(self, result: Dict) -> str:
        """Genera reporte de conversión"""
        report_lines = [
            "# 📊 Reporte de Conversión - NotebookLM a Anclora RAG",
            f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Archivo original:** {result['metadata']['original_filename']}",
            f"**Formato detectado:** {result['detection']['format'].value}",
            f"**Confianza de detección:** {result['detection']['confidence']:.1f}%",
            "",
            "## 📈 Estadísticas",
            f"- **Total de fuentes detectadas:** {result['stats'].get('sources_total', 0)}",
            f"- **Fuentes convertidas exitosamente:** {result['stats'].get('sources_converted', 0)}",
            f"- **Tasa de éxito:** {result['stats'].get('conversion_rate', 0):.1f}%",
            "",
            "## 📝 Log de Conversión",
            ""
        ]
        
        report_lines.extend(self.log)
        
        # Añadir detalles de detección
        report_lines.extend([
            "",
            "## 🔍 Detalles de Detección",
            f"```json",
            f"{self._format_detection_details(result['detection'])}",
            f"```"
        ])
        
        return "\n".join(report_lines)
    
    def _format_detection_details(self, detection: Dict) -> str:
        """Formatea los detalles de detección para el reporte"""
        import json
        return json.dumps(detection, indent=2, ensure_ascii=False)
