#!/usr/bin/env python3
"""
Script para probar el nuevo sistema de chunking por dominio.
Compara el chunking anterior vs el nuevo sistema diferenciado.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

def test_domain_chunking():
    """Prueba el nuevo sistema de chunking por dominio"""
    
    print("🎯 PRUEBA DEL CHUNKING POR DOMINIO")
    print("=" * 50)
    
    try:
        from common.ingest_file import _get_text_splitter_for_domain, CHUNKING_CONFIG
        print("✅ Funciones de chunking importadas correctamente")
    except Exception as e:
        print(f"❌ Error importando funciones: {e}")
        return
    
    # Ejemplos de contenido por dominio
    test_cases = {
        "code": {
            "domain": "code",
            "content": '''
import os
import sys
from typing import List, Dict, Optional

class DocumentProcessor:
    """Procesador de documentos con chunking inteligente"""
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
        self.processed_docs = []
    
    def process_file(self, file_path: str) -> List[str]:
        """
        Procesa un archivo y lo divide en chunks.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Lista de chunks procesados
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self._create_chunks(content)
    
    def _create_chunks(self, content: str) -> List[str]:
        """Crea chunks del contenido"""
        chunks = []
        # Lógica de chunking aquí...
        return chunks

def main():
    """Función principal"""
    processor = DocumentProcessor()
    print("Sistema inicializado")
'''
        },
        
        "documents": {
            "domain": "documents",
            "content": '''
# Guía de Implementación del Sistema RAG

## Introducción

El sistema RAG (Retrieval-Augmented Generation) combina la recuperación de información con la generación de texto para proporcionar respuestas precisas y contextuales.

## Arquitectura del Sistema

### Componentes Principales

1. **Base de Datos Vectorial**: ChromaDB para almacenar embeddings
2. **Modelo de Embeddings**: HuggingFace para convertir texto a vectores
3. **Modelo de Lenguaje**: Para generar respuestas basadas en contexto

### Flujo de Procesamiento

El procesamiento sigue estos pasos:

1. **Ingesta de Documentos**
   - Carga de archivos múltiples formatos
   - Chunking inteligente por tipo de contenido
   - Generación de embeddings

2. **Consulta y Recuperación**
   - Análisis de la consulta del usuario
   - Búsqueda de similitud en la base vectorial
   - Selección de chunks más relevantes

3. **Generación de Respuesta**
   - Construcción del contexto con chunks recuperados
   - Generación de respuesta usando LLM
   - Post-procesamiento y validación

## Configuración Avanzada

### Parámetros de Chunking

Para optimizar la recuperación, se pueden ajustar:

- **Tamaño de chunk**: Según el tipo de contenido
- **Overlap**: Para mantener contexto entre chunks
- **Separadores**: Específicos por formato de archivo

### Métricas de Evaluación

- **Precisión**: Relevancia de documentos recuperados
- **Recall**: Cobertura de información relevante
- **Latencia**: Tiempo de respuesta del sistema
'''
        },
        
        "multimedia": {
            "domain": "multimedia", 
            "content": '''
Transcripción de audio: Presentación sobre IA

Hola y bienvenidos a esta presentación sobre inteligencia artificial. 

En los últimos años hemos visto avances increíbles en el campo de la IA, especialmente en el procesamiento de lenguaje natural y la visión por computadora.

Los modelos de lenguaje como GPT han revolucionado la forma en que interactuamos con las máquinas, permitiendo conversaciones más naturales y la generación de contenido de alta calidad.

En el ámbito empresarial, la IA está transformando industrias enteras, desde la atención al cliente hasta el análisis de datos y la toma de decisiones automatizada.

Sin embargo, también enfrentamos desafíos importantes como la ética en IA, la privacidad de datos y la necesidad de transparencia en los algoritmos.

Es crucial que desarrollemos estas tecnologías de manera responsable, considerando su impacto en la sociedad y asegurándonos de que beneficien a todos.

Gracias por su atención y espero que esta información les sea útil.
'''
        }
    }
    
    print("\n🔍 COMPARACIÓN DE CHUNKING POR DOMINIO")
    print("=" * 60)
    
    for test_name, test_data in test_cases.items():
        domain = test_data["domain"]
        content = test_data["content"]
        
        print(f"\n📁 DOMINIO: {domain.upper()}")
        print("-" * 40)
        
        # Chunking tradicional (500 chars)
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            traditional_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            traditional_chunks = traditional_splitter.split_text(content)
            
            print(f"📊 CHUNKING TRADICIONAL (500 chars):")
            print(f"   Chunks generados: {len(traditional_chunks)}")
            print(f"   Tamaños: {[len(c) for c in traditional_chunks]}")
            
            # Mostrar si se cortaron elementos importantes
            if domain == "code":
                functions_cut = any("def " in chunk and not chunk.strip().endswith(":") for chunk in traditional_chunks)
                classes_cut = any("class " in chunk and not chunk.strip().endswith(":") for chunk in traditional_chunks)
                print(f"   ⚠️  Funciones cortadas: {'Sí' if functions_cut else 'No'}")
                print(f"   ⚠️  Clases cortadas: {'Sí' if classes_cut else 'No'}")
            
        except Exception as e:
            print(f"❌ Error en chunking tradicional: {e}")
        
        # Chunking por dominio
        try:
            domain_splitter = _get_text_splitter_for_domain(domain)
            domain_chunks = domain_splitter.split_text(content)
            
            config = CHUNKING_CONFIG[domain]
            print(f"\n🎯 CHUNKING POR DOMINIO ({config['chunk_size']} chars):")
            print(f"   Chunks generados: {len(domain_chunks)}")
            print(f"   Tamaños: {[len(c) for c in domain_chunks]}")
            print(f"   Configuración: {config['chunk_size']} chars, overlap {config['chunk_overlap']}")
            
            # Análisis específico por dominio
            if domain == "code":
                complete_functions = sum(1 for chunk in domain_chunks if "def " in chunk and chunk.count("def ") == chunk.count("return"))
                complete_classes = sum(1 for chunk in domain_chunks if "class " in chunk and ":" in chunk)
                print(f"   ✅ Funciones completas: {complete_functions}")
                print(f"   ✅ Clases completas: {complete_classes}")
            
            elif domain == "documents":
                headers = sum(1 for chunk in domain_chunks if "##" in chunk)
                sections = sum(1 for chunk in domain_chunks if chunk.strip().startswith("#"))
                print(f"   ✅ Headers preservados: {headers}")
                print(f"   ✅ Secciones completas: {sections}")
            
        except Exception as e:
            print(f"❌ Error en chunking por dominio: {e}")
        
        print()
    
    # Mostrar configuración completa
    print("\n⚙️ CONFIGURACIÓN DE CHUNKING POR DOMINIO")
    print("=" * 50)
    
    for domain, config in CHUNKING_CONFIG.items():
        print(f"\n📁 {domain.upper()}:")
        print(f"   Tamaño: {config['chunk_size']} caracteres")
        print(f"   Overlap: {config['chunk_overlap']} caracteres")
        print(f"   Separadores: {len(config['separators'])} niveles")
        print(f"   Principales: {config['separators'][:3]}")
    
    print("\n✨ BENEFICIOS DEL CHUNKING POR DOMINIO:")
    print("• 🎯 Preserva la estructura semántica del contenido")
    print("• 📏 Tamaños optimizados según el tipo de información")
    print("• 🔍 Mejor recuperación de contexto relevante")
    print("• 🧠 Chunks más coherentes para el modelo de lenguaje")
    print("• 📊 Metadatos enriquecidos para análisis")

if __name__ == "__main__":
    test_domain_chunking()
