#!/usr/bin/env python3
"""
Script para probar el sistema de chunking inteligente.
Compara el chunking tradicional vs el chunking inteligente.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

def test_smart_chunking():
    """Prueba el sistema de chunking inteligente"""
    
    print("🧠 PRUEBA DEL CHUNKING INTELIGENTE")
    print("=" * 50)
    
    try:
        from common.smart_chunking import smart_chunker
        print("✅ SmartChunker importado correctamente")
    except Exception as e:
        print(f"❌ Error importando SmartChunker: {e}")
        return
    
    # Ejemplos de código para probar
    test_cases = {
        "python_complex.py": '''
import os
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class DocumentChunk:
    """Representa un chunk de documento con metadatos"""
    content: str
    metadata: Dict[str, any]
    chunk_id: str
    
    def __post_init__(self):
        if not self.chunk_id:
            self.chunk_id = f"chunk_{hash(self.content)}"

class DocumentProcessor:
    """Procesador de documentos con chunking inteligente"""
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
        self.processed_docs = []
    
    def process_file(self, file_path: str) -> List[DocumentChunk]:
        """
        Procesa un archivo y lo divide en chunks inteligentes.
        
        Args:
            file_path: Ruta al archivo a procesar
            
        Returns:
            Lista de chunks procesados
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo está vacío
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            raise ValueError("El archivo está vacío")
        
        chunks = self._create_chunks(content)
        self.processed_docs.extend(chunks)
        return chunks
    
    def _create_chunks(self, content: str) -> List[DocumentChunk]:
        """Crea chunks del contenido"""
        chunks = []
        # Lógica de chunking aquí...
        return chunks

def main():
    """Función principal de prueba"""
    processor = DocumentProcessor()
    print("Procesador inicializado correctamente")
''',
        
        "javascript_api.js": '''
/**
 * API Client para el sistema de RAG
 * Maneja la comunicación con el backend de procesamiento de documentos
 */

class RAGApiClient {
    constructor(baseUrl = 'http://localhost:8081', apiKey = null) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        this.headers = {
            'Content-Type': 'application/json',
            ...(apiKey && { 'Authorization': `Bearer ${apiKey}` })
        };
    }
    
    /**
     * Sube un documento para procesamiento
     * @param {File} file - Archivo a subir
     * @param {Object} options - Opciones de procesamiento
     * @returns {Promise<Object>} Respuesta del servidor
     */
    async uploadDocument(file, options = {}) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('options', JSON.stringify(options));
        
        try {
            const response = await fetch(`${this.baseUrl}/upload`, {
                method: 'POST',
                headers: {
                    ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
                },
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error uploading document:', error);
            throw error;
        }
    }
    
    /**
     * Realiza una consulta al sistema RAG
     * @param {string} query - Consulta a realizar
     * @param {Object} filters - Filtros opcionales
     * @returns {Promise<Object>} Resultados de la consulta
     */
    async query(query, filters = {}) {
        const payload = {
            query,
            filters,
            max_results: filters.max_results || 5
        };
        
        const response = await fetch(`${this.baseUrl}/query`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(payload)
        });
        
        return await response.json();
    }
}

// Exportar para uso en Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RAGApiClient;
}
''',
        
        "complex_query.sql": '''
-- Análisis complejo de rendimiento del sistema RAG
-- Incluye métricas de chunking, consultas y precisión

WITH document_metrics AS (
    SELECT 
        d.id as doc_id,
        d.filename,
        d.file_type,
        d.size_bytes,
        COUNT(c.id) as total_chunks,
        AVG(LENGTH(c.content)) as avg_chunk_size,
        MIN(LENGTH(c.content)) as min_chunk_size,
        MAX(LENGTH(c.content)) as max_chunk_size,
        d.created_at as upload_date
    FROM documents d
    LEFT JOIN chunks c ON d.id = c.document_id
    WHERE d.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    GROUP BY d.id, d.filename, d.file_type, d.size_bytes, d.created_at
),

query_performance AS (
    SELECT 
        q.id as query_id,
        q.query_text,
        q.response_time_ms,
        COUNT(qr.chunk_id) as chunks_retrieved,
        AVG(qr.similarity_score) as avg_similarity,
        MAX(qr.similarity_score) as max_similarity,
        q.created_at as query_date
    FROM queries q
    LEFT JOIN query_results qr ON q.id = qr.query_id
    WHERE q.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY q.id, q.query_text, q.response_time_ms, q.created_at
),

chunking_efficiency AS (
    SELECT 
        dm.file_type,
        COUNT(dm.doc_id) as total_documents,
        AVG(dm.total_chunks) as avg_chunks_per_doc,
        AVG(dm.avg_chunk_size) as overall_avg_chunk_size,
        AVG(dm.size_bytes / dm.total_chunks) as avg_bytes_per_chunk
    FROM document_metrics dm
    GROUP BY dm.file_type
)

SELECT 
    ce.file_type,
    ce.total_documents,
    ROUND(ce.avg_chunks_per_doc, 2) as avg_chunks,
    ROUND(ce.overall_avg_chunk_size, 0) as avg_chunk_chars,
    ROUND(ce.avg_bytes_per_chunk, 0) as avg_bytes_per_chunk,
    
    -- Métricas de consulta relacionadas
    COUNT(DISTINCT qp.query_id) as related_queries,
    ROUND(AVG(qp.response_time_ms), 2) as avg_response_time,
    ROUND(AVG(qp.avg_similarity), 3) as avg_similarity_score
    
FROM chunking_efficiency ce
LEFT JOIN document_metrics dm ON ce.file_type = dm.file_type
LEFT JOIN chunks c ON dm.doc_id = c.document_id
LEFT JOIN query_results qr ON c.id = qr.chunk_id
LEFT JOIN query_performance qp ON qr.query_id = qp.query_id

GROUP BY 
    ce.file_type, 
    ce.total_documents, 
    ce.avg_chunks_per_doc, 
    ce.overall_avg_chunk_size, 
    ce.avg_bytes_per_chunk

ORDER BY ce.total_documents DESC, avg_similarity_score DESC;
'''
    }
    
    print("\n🔍 COMPARACIÓN: CHUNKING TRADICIONAL vs INTELIGENTE")
    print("=" * 60)
    
    for filename, content in test_cases.items():
        print(f"\n📄 Archivo: {filename}")
        print("-" * 40)
        
        # Chunking tradicional
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            traditional_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            traditional_chunks = traditional_splitter.split_text(content)
            
            print(f"📊 TRADICIONAL:")
            print(f"   Chunks: {len(traditional_chunks)}")
            print(f"   Tamaños: {[len(c) for c in traditional_chunks]}")
            
        except Exception as e:
            print(f"❌ Error en chunking tradicional: {e}")
        
        # Chunking inteligente
        try:
            smart_docs = smart_chunker.chunk_content(content, filename)
            stats = smart_chunker.get_chunking_stats(smart_docs)
            
            print(f"🧠 INTELIGENTE:")
            print(f"   Chunks: {stats['total_chunks']}")
            print(f"   Tamaño promedio: {stats['avg_chunk_size']:.0f}")
            print(f"   Tipo detectado: {smart_docs[0].metadata.get('content_type', 'unknown')}")
            print(f"   Lenguaje: {smart_docs[0].metadata.get('language', 'unknown')}")
            
            # Mostrar metadatos del primer chunk
            first_chunk_meta = smart_docs[0].metadata
            if first_chunk_meta.get('has_functions'):
                print(f"   Funciones: {first_chunk_meta.get('functions', [])}")
            if first_chunk_meta.get('has_classes'):
                print(f"   Clases: {first_chunk_meta.get('classes', [])}")
            
        except Exception as e:
            print(f"❌ Error en chunking inteligente: {e}")
    
    print("\n✨ VENTAJAS DEL CHUNKING INTELIGENTE:")
    print("• Preserva la estructura del código (funciones, clases completas)")
    print("• Adapta el tamaño según el tipo de contenido")
    print("• Agrega metadatos ricos para mejor recuperación")
    print("• Usa separadores específicos por lenguaje")
    print("• Mantiene el contexto semántico")

if __name__ == "__main__":
    test_smart_chunking()
