#!/usr/bin/env python3
"""
Script para analizar y mejorar el chunking de código en Anclora RAG.
Esto es crucial para recuperar fragmentos de código precisos de la base vectorial.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

def analyze_current_chunking():
    """Analiza la configuración actual de chunking"""
    
    print("🔍 ANÁLISIS DEL CHUNKING ACTUAL")
    print("=" * 50)
    
    try:
        from common.ingest_file import CHUNK_SIZE, CHUNK_OVERLAP
        print(f"📏 Tamaño de chunk actual: {CHUNK_SIZE} caracteres")
        print(f"🔗 Overlap actual: {CHUNK_OVERLAP} caracteres")
        print(f"📊 Ratio de overlap: {(CHUNK_OVERLAP/CHUNK_SIZE)*100:.1f}%")
    except Exception as e:
        print(f"❌ Error obteniendo configuración: {e}")
        return None
    
    return {"chunk_size": CHUNK_SIZE, "chunk_overlap": CHUNK_OVERLAP}

def test_code_chunking_examples():
    """Prueba el chunking con ejemplos de código"""
    
    print("\n🧪 PRUEBAS DE CHUNKING CON CÓDIGO")
    print("=" * 50)
    
    # Ejemplos de código de diferentes lenguajes
    code_examples = {
        "python_function": '''
def process_document(file_path, chunk_size=500):
    """
    Procesa un documento y lo divide en chunks.
    
    Args:
        file_path (str): Ruta al archivo
        chunk_size (int): Tamaño del chunk
    
    Returns:
        List[str]: Lista de chunks procesados
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    chunks = []
    for i in range(0, len(content), chunk_size):
        chunk = content[i:i + chunk_size]
        chunks.append(chunk.strip())
    
    return chunks
''',
        
        "javascript_class": '''
class DocumentProcessor {
    constructor(options = {}) {
        this.chunkSize = options.chunkSize || 500;
        this.overlap = options.overlap || 50;
        this.language = options.language || 'auto';
    }
    
    async processFile(filePath) {
        try {
            const content = await fs.readFile(filePath, 'utf8');
            return this.createChunks(content);
        } catch (error) {
            console.error('Error processing file:', error);
            throw error;
        }
    }
    
    createChunks(text) {
        const chunks = [];
        let start = 0;
        
        while (start < text.length) {
            const end = Math.min(start + this.chunkSize, text.length);
            const chunk = text.slice(start, end);
            chunks.push(chunk.trim());
            start += this.chunkSize - this.overlap;
        }
        
        return chunks;
    }
}
''',
        
        "sql_query": '''
-- Consulta compleja para análisis de documentos
WITH document_stats AS (
    SELECT 
        d.id,
        d.title,
        d.file_type,
        COUNT(c.id) as chunk_count,
        AVG(LENGTH(c.content)) as avg_chunk_size,
        MAX(c.created_at) as last_processed
    FROM documents d
    LEFT JOIN chunks c ON d.id = c.document_id
    WHERE d.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    GROUP BY d.id, d.title, d.file_type
),
processing_metrics AS (
    SELECT 
        file_type,
        COUNT(*) as total_docs,
        AVG(chunk_count) as avg_chunks_per_doc,
        AVG(avg_chunk_size) as overall_avg_chunk_size
    FROM document_stats
    GROUP BY file_type
)
SELECT 
    pm.file_type,
    pm.total_docs,
    ROUND(pm.avg_chunks_per_doc, 2) as avg_chunks,
    ROUND(pm.overall_avg_chunk_size, 2) as avg_size
FROM processing_metrics pm
ORDER BY pm.total_docs DESC;
'''
    }
    
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        # Configuración actual
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
        for name, code in code_examples.items():
            print(f"\n📝 Ejemplo: {name}")
            print("-" * 30)
            
            chunks = splitter.split_text(code)
            print(f"🔢 Número de chunks: {len(chunks)}")
            
            for i, chunk in enumerate(chunks):
                lines = chunk.count('\n') + 1
                chars = len(chunk)
                print(f"  Chunk {i+1}: {chars} chars, {lines} líneas")
                
                # Mostrar primeras líneas del chunk
                first_lines = '\n'.join(chunk.split('\n')[:3])
                print(f"  Contenido: {first_lines[:100]}...")
                print()
                
    except Exception as e:
        print(f"❌ Error en pruebas de chunking: {e}")

def recommend_code_chunking_improvements():
    """Recomienda mejoras para el chunking de código"""
    
    print("\n💡 RECOMENDACIONES PARA MEJORAR EL CHUNKING DE CÓDIGO")
    print("=" * 60)
    
    recommendations = [
        {
            "title": "🎯 Chunking específico por lenguaje",
            "description": "Usar diferentes estrategias según el tipo de archivo",
            "implementation": "Implementar CodeTextSplitter de LangChain con soporte para múltiples lenguajes"
        },
        {
            "title": "🔍 Preservar contexto semántico",
            "description": "Mantener funciones, clases y bloques de código completos",
            "implementation": "Usar separadores específicos como '\\n\\nclass ', '\\n\\ndef ', '\\n\\nfunction '"
        },
        {
            "title": "📏 Tamaños adaptativos",
            "description": "Ajustar tamaño de chunk según el tipo de contenido",
            "implementation": "Código: 1000-1500 chars, Documentación: 500-800 chars"
        },
        {
            "title": "🏷️ Metadatos enriquecidos",
            "description": "Agregar información sobre el contexto del código",
            "implementation": "Incluir: lenguaje, tipo (función/clase/comentario), línea de inicio"
        },
        {
            "title": "🔗 Overlap inteligente",
            "description": "Overlap basado en estructura, no solo caracteres",
            "implementation": "Mantener imports, definiciones de clase en chunks relacionados"
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['title']}")
        print(f"   📋 {rec['description']}")
        print(f"   🛠️  {rec['implementation']}")
        print()

def create_improved_chunking_config():
    """Crea una configuración mejorada para chunking de código"""
    
    print("\n⚙️ CONFIGURACIÓN MEJORADA PROPUESTA")
    print("=" * 50)
    
    config = {
        "code_files": {
            "chunk_size": 1200,
            "chunk_overlap": 100,
            "separators": [
                "\n\nclass ",
                "\n\ndef ",
                "\n\nfunction ",
                "\n\n# ",
                "\n\n// ",
                "\n\n/*",
                "\n\n",
                "\n",
                " "
            ]
        },
        "documentation": {
            "chunk_size": 800,
            "chunk_overlap": 80,
            "separators": [
                "\n\n## ",
                "\n\n### ",
                "\n\n",
                "\n",
                ". ",
                " "
            ]
        },
        "mixed_content": {
            "chunk_size": 1000,
            "chunk_overlap": 100,
            "separators": [
                "\n\n```",
                "\n\nclass ",
                "\n\ndef ",
                "\n\n## ",
                "\n\n",
                "\n",
                " "
            ]
        }
    }
    
    for content_type, settings in config.items():
        print(f"📁 {content_type.upper()}:")
        print(f"   Tamaño: {settings['chunk_size']} caracteres")
        print(f"   Overlap: {settings['chunk_overlap']} caracteres")
        print(f"   Separadores: {len(settings['separators'])} niveles")
        print()
    
    return config

def main():
    print("🔧 ANALIZADOR DE CHUNKING DE CÓDIGO - ANCLORA RAG")
    print("=" * 60)
    print("Optimizando la recuperación precisa de fragmentos de código")
    print()
    
    # Analizar configuración actual
    current_config = analyze_current_chunking()
    
    # Probar con ejemplos de código
    test_code_chunking_examples()
    
    # Generar recomendaciones
    recommend_code_chunking_improvements()
    
    # Crear configuración mejorada
    improved_config = create_improved_chunking_config()
    
    print("🎯 PRÓXIMOS PASOS:")
    print("1. Implementar CodeTextSplitter específico por lenguaje")
    print("2. Agregar metadatos de contexto a los chunks")
    print("3. Probar con documentación técnica real")
    print("4. Medir precisión de recuperación antes/después")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
