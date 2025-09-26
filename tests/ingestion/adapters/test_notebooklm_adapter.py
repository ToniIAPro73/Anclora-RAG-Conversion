"""
Tests para el adaptador NotebookLM
"""

import pytest
from pathlib import Path
import sys

# Añadir el path de la app
sys.path.append(str(Path(__file__).parent.parent.parent.parent / 'app'))

from app.ingestion.adapters.notebooklm_adapter import NotebookLMAdapter
from app.ingestion.adapters.format_detector import FormatDetector, SourceFormat

def test_format_detection():
    """Test de detección de formatos"""
    detector = FormatDetector()
    
    # Test formato Anclora
    anclora_content = """
    **ID:** [SRC-001]
    **Tipo:** [Articulo Academico]
    **Titulo:** [Deep Learning for NLP]
    """
    
    result = detector.detect_format(anclora_content)
    assert result['format'] == SourceFormat.ANCLORA
    assert result['confidence'] > 50
    
    # Test formato NotebookLM
    notebooklm_content = """
    1. **Deep Learning for NLP**
    - **Type:** Academic Paper
    - **Author:** Smith, J.
    """
    
    result = detector.detect_format(notebooklm_content)
    assert result['format'] == SourceFormat.NOTEBOOKLM

def test_adapter_conversion():
    """Test de conversión básica"""
    adapter = NotebookLMAdapter()
    
    test_content = """
    1. **Deep Learning for Natural Language Processing**
    - **Type:** Academic Paper
    - **Author:** Smith, J.; Johnson, K.
    - **Publisher:** Journal of AI Research
    - **Year:** 2023
    - **URL:** https://doi.org/10.1234/jair.2023.001
    """
    
    result = adapter.convert_content(test_content)
    assert result['success'] == True
    assert 'SRC-001' in result['content']
    assert 'Deep Learning for Natural Language Processing' in result['content']
