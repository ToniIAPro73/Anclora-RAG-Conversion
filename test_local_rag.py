#!/usr/bin/env python3
"""
Script de prueba para verificar funcionamiento local del RAG con PostgreSQL + pgvector
Ejecutar con el entorno virtual activado
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

# Cargar variables de entorno
load_dotenv()

def test_basic_vector_store():
    """Probar funcionalidades básicas del vector store"""
    try:
        logger.info("🔍 Probando vector store con PostgreSQL + pgvector...")

        # Configurar embeddings
        embeddings = SentenceTransformerEmbeddings(
            model_name=os.getenv("EMBEDDINGS_MODEL_NAME", "sentence-transformers/all-mpnet-base-v2")
        )
        logger.info("✅ Embeddings configurados")

        # Configurar PGVector
        connection_string = PGVector.connection_string_from_db_params(
            driver="psycopg2",
            host=os.getenv("PG_HOST", "localhost"),
            port=int(os.getenv("PG_PORT", "5432")),
            database=os.getenv("PG_DB", "anclora_rag_local"),
            user=os.getenv("PG_USER", "anclora_user"),
            password=os.getenv("PG_PASSWORD", "anclora_password"),
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
        logger.error(f"❌ Error en prueba de vector store: {e}")
        return False

def test_database_schema():
    """Verificar esquema de base de datos"""
    try:
        import psycopg2

        conn = psycopg2.connect(
            host=os.getenv("PG_HOST", "localhost"),
            port=int(os.getenv("PG_PORT", "5432")),
            database=os.getenv("PG_DB", "anclora_rag_local"),
            user=os.getenv("PG_USER", "anclora_user"),
            password=os.getenv("PG_PASSWORD", "anclora_password"),
        )

        with conn.cursor() as cur:
            # Verificar tablas
            cur.execute("""
                SELECT table_name, table_schema
                FROM information_schema.tables
                WHERE table_schema = 'langchain'
                ORDER BY table_name;
            """)

            tables = cur.fetchall()
            logger.info("📊 Tablas encontradas:")
            for table_name, schema in tables:
                logger.info(f"   - {schema}.{table_name}")

            # Verificar extensión pgvector
            cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
            extension = cur.fetchone()
            if extension:
                logger.info(f"✅ Extensión pgvector: {extension[0]} v{extension[1]}")
            else:
                logger.error("❌ Extensión pgvector no encontrada")
                return False

        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Error verificando esquema: {e}")
        return False

def main():
    """Función principal de prueba"""
    logger.info("🚀 Iniciando pruebas del sistema RAG local...")

    # Verificar variables de entorno
    required_vars = ["PG_HOST", "PG_PORT", "PG_DB", "PG_USER", "PG_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
        logger.info("💡 Crea o verifica el archivo .env.local")
        return False

    # Test 1: Esquema de base de datos
    logger.info("1️⃣ Verificando esquema de base de datos...")
    if not test_database_schema():
        return False

    # Test 2: Vector store
    logger.info("2️⃣ Probando funcionalidades del vector store...")
    if not test_basic_vector_store():
        return False

    logger.info("")
    logger.info("🎉 ¡Todas las pruebas pasaron exitosamente!")
    logger.info("")
    logger.info("✅ Sistema RAG local funcionando correctamente")
    logger.info("✅ PostgreSQL + pgvector operativo")
    logger.info("✅ Búsqueda vectorial funcionando")
    logger.info("")
    logger.info("🚀 Puedes proceder con:")
    logger.info("   - Migración completa de datos")
    logger.info("   - Desarrollo de nuevas funcionalidades")
    logger.info("   - Despliegue en producción")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)