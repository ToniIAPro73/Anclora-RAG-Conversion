#!/usr/bin/env python3
"""
Script de verificación y optimización post-migración a Pgvector
Ejecutar después de completar la migración para validar funcionamiento
"""

import os
import sys
import logging
from typing import Dict, Any
import psycopg2
from langchain_community.vectorstores import PGVector
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def test_database_connection() -> bool:
    """Probar conexión básica a PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST", "localhost"),
            port=int(os.getenv("PG_PORT", "5432")),
            database=os.getenv("PG_DB", "anclora_rag"),
            user=os.getenv("PG_USER", "anclora_user"),
            password=os.getenv("PG_PASSWORD", "anclora_password"),
        )
        conn.close()
        logger.info("✅ Conexión a PostgreSQL exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ Error conectando a PostgreSQL: {e}")
        return False

def check_pgvector_extension() -> bool:
    """Verificar que la extensión pgvector esté instalada"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST", "localhost"),
            port=int(os.getenv("PG_PORT", "5432")),
            database=os.getenv("PG_DB", "anclora_rag"),
            user=os.getenv("PG_USER", "anclora_user"),
            password=os.getenv("PG_PASSWORD", "anclora_password"),
        )

        with conn.cursor() as cur:
            cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
            result = cur.fetchone()

        conn.close()

        if result:
            logger.info("✅ Extensión pgvector instalada correctamente")
            return True
        else:
            logger.error("❌ Extensión pgvector no encontrada")
            return False

    except Exception as e:
        logger.error(f"❌ Error verificando extensión pgvector: {e}")
        return False

def check_langchain_tables() -> Dict[str, Any]:
    """Verificar tablas creadas por LangChain/PGVector"""
    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST", "localhost"),
            port=int(os.getenv("PG_PORT", "5432")),
            database=os.getenv("PG_DB", "anclora_rag"),
            user=os.getenv("PG_USER", "anclora_user"),
            password=os.getenv("PG_PASSWORD", "anclora_password"),
        )

        with conn.cursor() as cur:
            # Verificar tablas de LangChain
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'langchain'
                AND table_name LIKE 'langchain_pg_%';
            """)
            tables = cur.fetchall()

            # Contar documentos por colección
            collections_data = {}
            for table in tables:
                table_name = table[0]
                if table_name == 'langchain_pg_collection':
                    cur.execute("SELECT COUNT(*) FROM langchain.langchain_pg_collection;")
                    collections_count = cur.fetchone()[0]
                    collections_data['total_collections'] = collections_count
                elif table_name == 'langchain_pg_embedding':
                    cur.execute("SELECT COUNT(*) FROM langchain.langchain_pg_embedding;")
                    embeddings_count = cur.fetchone()[0]
                    collections_data['total_embeddings'] = embeddings_count

        conn.close()

        logger.info(f"✅ Tablas LangChain encontradas: {[t[0] for t in tables]}")
        logger.info(f"📊 Datos migrados: {collections_data}")

        return {
            'tables': [t[0] for t in tables],
            'data': collections_data
        }

    except Exception as e:
        logger.error(f"❌ Error verificando tablas LangChain: {e}")
        return {}

def test_vector_search() -> bool:
    """Probar búsqueda vectorial básica"""
    try:
        # Configurar embeddings
        embeddings = SentenceTransformerEmbeddings(
            model_name=os.getenv("EMBEDDINGS_MODEL_NAME", "sentence-transformers/all-mpnet-base-v2")
        )

        # Configurar PGVector
        connection_string = PGVector.connection_string_from_db_params(
            driver="psycopg2",
            host=os.getenv("PG_HOST", "localhost"),
            port=int(os.getenv("PG_PORT", "5432")),
            database=os.getenv("PG_DB", "anclora_rag"),
            user=os.getenv("PG_USER", "anclora_user"),
            password=os.getenv("PG_PASSWORD", "anclora_password"),
        )

        # Crear instancia PGVector
        vectorstore = PGVector(
            collection_name="test_collection",
            connection_string=connection_string,
            embedding_function=embeddings,
        )

        # Documento de prueba
        test_docs = [Document(page_content="Esto es un documento de prueba para verificar la búsqueda vectorial")]

        # Agregar documento de prueba
        vectorstore.add_documents(test_docs)

        # Buscar documento
        results = vectorstore.similarity_search("documento de prueba", k=1)

        if results:
            logger.info("✅ Búsqueda vectorial funcionando correctamente")
            logger.info(f"📄 Documento encontrado: {results[0].page_content[:100]}...")
            return True
        else:
            logger.error("❌ Búsqueda vectorial no devolvió resultados")
            return False

    except Exception as e:
        logger.error(f"❌ Error en búsqueda vectorial: {e}")
        return False

def run_performance_tests() -> Dict[str, Any]:
    """Ejecutar pruebas básicas de rendimiento"""
    try:
        logger.info("🏃‍♂️ Ejecutando pruebas de rendimiento...")

        # Configurar PGVector
        connection_string = PGVector.connection_string_from_db_params(
            driver="psycopg2",
            host=os.getenv("PG_HOST", "localhost"),
            port=int(os.getenv("PG_PORT", "5432")),
            database=os.getenv("PG_DB", "anclora_rag"),
            user=os.getenv("PG_USER", "anclora_user"),
            password=os.getenv("PG_PASSWORD", "anclora_password"),
        )

        embeddings = SentenceTransformerEmbeddings(
            model_name=os.getenv("EMBEDDINGS_MODEL_NAME", "sentence-transformers/all-mpnet-base-v2")
        )

        vectorstore = PGVector(
            collection_name="performance_test",
            connection_string=connection_string,
            embedding_function=embeddings,
        )

        # Crear documentos de prueba
        test_docs = [Document(page_content=f"Documento de prueba número {i} con contenido único") for i in range(100)]

        # Test 1: Inserción
        import time
        start_time = time.time()
        vectorstore.add_documents(test_docs)
        insert_time = time.time() - start_time

        # Test 2: Búsqueda
        start_time = time.time()
        results = vectorstore.similarity_search("contenido único", k=5)
        search_time = time.time() - start_time

        performance_results = {
            'insert_time_100_docs': insert_time,
            'search_time_5_results': search_time,
            'docs_per_second': 100 / insert_time if insert_time > 0 else 0,
            'searches_per_second': 1 / search_time if search_time > 0 else 0
        }

        logger.info(f"⏱️ Rendimiento - Inserción: {insert_time:.2f}s para 100 docs ({performance_results['docs_per_second']:.1f} docs/s)")
        logger.info(f"⏱️ Rendimiento - Búsqueda: {search_time:.4f}s ({performance_results['searches_per_second']:.1f} búsquedas/s)")

        return performance_results

    except Exception as e:
        logger.error(f"❌ Error en pruebas de rendimiento: {e}")
        return {}

def generate_migration_report(results: Dict[str, Any]) -> str:
    """Generar reporte de migración"""
    report = []
    report.append("📋 REPORTE DE MIGRACIÓN PGVECTOR")
    report.append("=" * 50)
    report.append("")

    # Estado de conexión
    report.append("🔌 CONEXIÓN A BASE DE DATOS:")
    report.append(f"  PostgreSQL: {'✅ Conectado' if results.get('db_connection') else '❌ Error'}")
    report.append(f"  pgvector: {'✅ Instalado' if results.get('pgvector_extension') else '❌ Error'}")
    report.append("")

    # Estado de tablas
    if results.get('langchain_tables'):
        tables = results['langchain_tables']
        report.append("📊 TABLAS LANGCHAIN:")
        report.append(f"  Tablas encontradas: {', '.join(tables.get('tables', []))}")
        report.append(f"  Colecciones: {tables.get('data', {}).get('total_collections', 0)}")
        report.append(f"  Embeddings: {tables.get('data', {}).get('total_embeddings', 0)}")
    else:
        report.append("📊 TABLAS LANGCHAIN: ❌ No se encontraron tablas")

    report.append("")

    # Estado de búsqueda vectorial
    report.append("🔍 BÚSQUEDA VECTORIAL:")
    report.append(f"  Funcionamiento: {'✅ OK' if results.get('vector_search') else '❌ Error'}")
    report.append("")

    # Rendimiento
    if results.get('performance'):
        perf = results['performance']
        report.append("⚡ RENDIMIENTO:")
        report.append(f"  Inserción: {perf.get('docs_per_second', 0):.1f} docs/s")
        report.append(f"  Búsqueda: {perf.get('searches_per_second', 0):.1f} búsquedas/s")
    else:
        report.append("⚡ RENDIMIENTO: ❌ No se pudieron ejecutar pruebas")

    report.append("")
    report.append("=" * 50)

    # Recomendaciones
    report.append("💡 RECOMENDACIONES:")
    if not results.get('db_connection'):
        report.append("  ❌ Revisar configuración de conexión PostgreSQL")
    if not results.get('pgvector_extension'):
        report.append("  ❌ Instalar extensión pgvector en PostgreSQL")
    if not results.get('vector_search'):
        report.append("  ❌ Verificar configuración de LangChain con PGVector")
    if results.get('performance') and results['performance'].get('docs_per_second', 0) < 10:
        report.append("  ⚠️ Considerar optimización de configuración PostgreSQL")

    return "\n".join(report)

def main():
    """Función principal de verificación"""
    logger.info("🔍 Iniciando verificación post-migración a Pgvector...")

    results = {}

    # Test 1: Conexión básica
    logger.info("1️⃣ Verificando conexión a PostgreSQL...")
    results['db_connection'] = test_database_connection()

    # Test 2: Extensión pgvector
    logger.info("2️⃣ Verificando extensión pgvector...")
    results['pgvector_extension'] = check_pgvector_extension()

    # Test 3: Tablas LangChain
    logger.info("3️⃣ Verificando tablas LangChain...")
    results['langchain_tables'] = check_langchain_tables()

    # Test 4: Búsqueda vectorial
    logger.info("4️⃣ Probando búsqueda vectorial...")
    results['vector_search'] = test_vector_search()

    # Test 5: Rendimiento
    logger.info("5️⃣ Ejecutando pruebas de rendimiento...")
    results['performance'] = run_performance_tests()

    # Generar reporte
    report = generate_migration_report(results)
    logger.info(f"\n{report}")

    # Determinar éxito general
    success = all([
        results.get('db_connection', False),
        results.get('pgvector_extension', False),
        results.get('vector_search', False)
    ])

    if success:
        logger.info("🎉 ¡Migración a Pgvector verificada exitosamente!")
        logger.info("✅ Puedes proceder a usar el sistema con Pgvector")
    else:
        logger.error("❌ La migración tiene problemas que requieren atención")
        logger.info("💡 Consulta el reporte arriba para detalles y soluciones")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)