#!/usr/bin/env python3
"""
Script de prueba simplificado para RAG con PostgreSQL + pgvector
Usa la instalación global de Python que funciona correctamente
"""

import os
import sys
import logging
from dotenv import load_dotenv
from langchain_community.vectorstores import PGVector
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.documents import Document

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar variables de entorno directamente
os.environ.setdefault("PG_HOST", "localhost")
os.environ.setdefault("PG_PORT", "5432")
os.environ.setdefault("PG_DB", "anclora_rag_local")
os.environ.setdefault("PG_USER", "anclora_user")
os.environ.setdefault("PG_PASSWORD", "anclora_password")

def test_basic_functionality():
    """Probar funcionalidades básicas del RAG"""
    try:
        logger.info("🔍 Probando RAG con PostgreSQL + pgvector...")

        # Configurar embeddings
        embeddings = SentenceTransformerEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        logger.info("✅ Embeddings configurados")

        # Configurar PGVector
        connection_string = PGVector.connection_string_from_db_params(
            driver="psycopg2",
            host="localhost",
            port=5432,
            database="anclora_rag_local",
            user="anclora_user",
            password="anclora_password",
        )

        # Crear instancia PGVector
        collection_name = "test_collection"
        vectorstore = PGVector(
            collection_name=collection_name,
            connection_string=connection_string,
            embedding_function=embeddings,
        )
        logger.info("✅ Vector store configurado")

        # Documentos de prueba
        test_docs = [
            Document(page_content="El sistema RAG permite buscar información de manera inteligente usando vectores."),
            Document(page_content="PostgreSQL con pgvector es una excelente opción para almacenamiento vectorial."),
            Document(page_content="La aplicación Anclora RAG está diseñada para facilitar la consulta de documentos."),
            Document(page_content="Los embeddings transforman texto en representaciones numéricas para búsqueda por similitud."),
            Document(page_content="El módulo markdown permite procesar documentos en formato Markdown correctamente.")
        ]

        logger.info(f"📄 Agregando {len(test_docs)} documentos de prueba...")

        # Agregar documentos
        vectorstore.add_documents(test_docs)
        logger.info("✅ Documentos agregados exitosamente")

        # Probar búsqueda
        query = "sistema RAG con PostgreSQL"
        logger.info(f"🔍 Buscando: '{query}'")

        results = vectorstore.similarity_search(query, k=3)

        if results:
            logger.info("✅ Búsqueda exitosa!")
            for i, doc in enumerate(results, 1):
                logger.info(f"   {i}. {doc.page_content[:100]}...")
        else:
            logger.error("❌ No se encontraron resultados")
            return False

        # Probar búsqueda con embeddings
        logger.info("🔍 Probando búsqueda con embeddings...")
        query_embedding = embeddings.embed_query("base de datos vectorial")
        results = vectorstore.similarity_search_by_vector(query_embedding, k=2)

        if results:
            logger.info("✅ Búsqueda por vector exitosa!")
            for i, doc in enumerate(results, 1):
                logger.info(f"   {i}. {doc.page_content[:100]}...")
        else:
            logger.error("❌ Búsqueda por vector falló")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Error en prueba de RAG: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal de prueba"""
    logger.info("🚀 Iniciando pruebas del sistema RAG...")

    # Verificar variables de entorno
    required_vars = ["PG_HOST", "PG_PORT", "PG_DB", "PG_USER", "PG_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
        logger.info("💡 Crea o verifica el archivo .env.local")
        return False

    # Ejecutar prueba
    if test_basic_functionality():
        logger.info("")
        logger.info("🎉 ¡RAG funcionando correctamente!")
        logger.info("")
        logger.info("✅ PostgreSQL + pgvector operativo")
        logger.info("✅ Búsqueda vectorial funcionando")
        logger.info("✅ Sistema listo para uso")
        logger.info("")
        logger.info("🚀 Puedes proceder con:")
        logger.info("   - Migración completa de datos")
        logger.info("   - Desarrollo de nuevas funcionalidades")
        logger.info("   - Despliegue en producción")
        return True
    else:
        logger.error("❌ Las pruebas fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)