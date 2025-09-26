"""
Detección automática de formatos de fuentes bibliográficas
"""

import re
from typing import Dict, List, Optional
from enum import Enum

class SourceFormat(Enum):
    ANCLORA = "anclora"
    NOTEBOOKLM = "notebooklm"
    BIBTEX = "bibtex"
    RIS = "ris"
    UNKNOWN = "unknown"

class FormatDetector:
    def __init__(self):
        self.patterns = {
            SourceFormat.ANCLORA: [
                re.compile(r'\*\*ID:\*\*\s*\[SRC-\d+\]', re.IGNORECASE),
                re.compile(r'\*\*Tipo:\*\*\s*\[.+\]', re.IGNORECASE),
                re.compile(r'\*\*Titulo:\*\*\s*\[.+\]', re.IGNORECASE)
            ],
            SourceFormat.NOTEBOOKLM: [
                re.compile(r'\d+\.\s+\*\*.+\*\*', re.IGNORECASE),
                re.compile(r'^- \*\*Source:\*\*', re.IGNORECASE),
                re.compile(r'^- \*\*Type:\*\*', re.IGNORECASE)
            ],
            SourceFormat.BIBTEX: [
                re.compile(r'@\w+\{[^,]+,', re.IGNORECASE),
                re.compile(r'title\s*=\s*\{[^}]+\}', re.IGNORECASE),
                re.compile(r'author\s*=\s*\{[^}]+\}', re.IGNORECASE)
            ]
        }
    
    def detect_format(self, content: str) -> Dict:
        """Detecta el formato y devuelve métricas de confianza"""
        scores = {format_type: 0 for format_type in SourceFormat}
        
        for format_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = pattern.findall(content)
                scores[format_type] += len(matches)
        
        # Calcular confianza
        total_matches = sum(scores.values())
        confidence = {
            format_type: (score / total_matches * 100) if total_matches > 0 else 0
            for format_type, score in scores.items()
        }
        
        # Determinar formato principal
        detected_format = max(scores.items(), key=lambda x: x[1])[0]
        
        return {
            'format': detected_format,
            'confidence': confidence[detected_format],
            'all_scores': scores,
            'details': self._get_format_details(content, detected_format)
        }
    
    def _get_format_details(self, content: str, format_type: SourceFormat) -> Dict:
        """Obtiene detalles específicos del formato detectado"""
        if format_type == SourceFormat.NOTEBOOKLM:
            return self._analyze_notebooklm_format(content)
        elif format_type == SourceFormat.ANCLORA:
            return self._analyze_anclora_format(content)
        return {}
    
    def _analyze_notebooklm_format(self, content: str) -> Dict:
        """Análisis profundo del formato NotebookLM"""
        lines = content.split('\n')
        source_count = len([l for l in lines if l.strip().startswith(('1.', '2.', '3.')) and '**' in l])
        
        return {
            'estimated_sources': source_count,
            'has_numbering': any(re.match(r'^\d+\.', l.strip()) for l in lines),
            'bold_patterns': len(re.findall(r'\*\*.+\*\*', content)),
            'field_diversity': self._count_field_variety(content)
        }
    
    def _analyze_anclora_format(self, content: str) -> Dict:
        """Análisis del formato Anclora"""
        return {
            'sources_count': len(re.findall(r'\*\*ID:\*\*\s*\[SRC-\d+\]', content)),
            'fields_per_source': self._avg_fields_per_source(content)
        }
    
    def _count_field_variety(self, content: str) -> int:
        """Cuenta la variedad de campos diferentes"""
        field_patterns = [
            r'(?i)(type|tipo):',
            r'(?i)(author|autor):',
            r'(?i)(publisher|editorial):',
            r'(?i)(year|año):',
            r'(?i)(url|doi):'
        ]
        return sum(1 for pattern in field_patterns if re.search(pattern, content))
    
    def _avg_fields_per_source(self, content: str) -> float:
        """Calcula campos promedio por fuente"""
        sources = re.findall(r'\*\*ID:\*\*\s*\[SRC-\d+\](.*?)(?=\*\*ID:\*\*|\Z)', content, re.DOTALL)
        if not sources:
            return 0
        fields_per_source = [len(re.findall(r'\*\*[^:]+:\*\*', source)) for source in sources]
        return sum(fields_per_source) / len(fields_per_source)
