#!/usr/bin/env python3
"""
Script de prueba final para RAG con PostgreSQL + pgvector
Usa la instalación global de Python que funciona correctamente
"""

import os
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar variables de entorno directamente
os.environ.setdefault("PG_HOST", "localhost")
os.environ.setdefault("PG_PORT", "5432")
os.environ.setdefault("PG_DB", "anclora_rag_local")
os.environ.setdefault("PG_USER", "anclora_user")
os.environ.setdefault("PG_PASSWORD", "anclora_password")

def test_database_connection():
    """Probar conexión básica a PostgreSQL"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="anclora_rag_local",
            user="anclora_user",
            password="anclora_password",
        )
        logger.info("✅ Conexion a PostgreSQL exitosa")
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Error conectando a PostgreSQL: {e}")
        return False

def test_pgvector_extension():
    """Verificar que la extensión pgvector esté instalada"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="anclora_rag_local",
            user="anclora_user",
            password="anclora_password",
        )

        with conn.cursor() as cur:
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            result = cur.fetchone()

        conn.close()

        if result:
            logger.info("✅ Extension pgvector instalada correctamente")
            return True
        else:
            logger.error("❌ Extension pgvector no encontrada")
            return False

    except Exception as e:
        logger.error(f"❌ Error verificando extension pgvector: {e}")
        return False

def test_langchain_tables():
    """Verificar tablas creadas por LangChain/PGVector"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="anclora_rag_local",
            user="anclora_user",
            password="anclora_password",
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

        conn.close()

        logger.info(f"✅ Tablas LangChain encontradas: {[t[0] for t in tables]}")
        return True

    except Exception as e:
        logger.error(f"❌ Error verificando tablas LangChain: {e}")
        return False

def main():
    """Función principal de prueba"""
    logger.info("🚀 Iniciando pruebas finales del sistema RAG...")

    # Test 1: Conexión básica
    logger.info("1️⃣ Verificando conexión a PostgreSQL...")
    if not test_database_connection():
        return False

    # Test 2: Extensión pgvector
    logger.info("2️⃣ Verificando extensión pgvector...")
    if not test_pgvector_extension():
        return False

    # Test 3: Tablas LangChain
    logger.info("3️⃣ Verificando tablas LangChain...")
    if not test_langchain_tables():
        logger.warning("⚠️ No se encontraron tablas LangChain (esto es normal si no se han usado aún)")

    logger.info("")
    logger.info("🎉 ¡Sistema RAG configurado exitosamente!")
    logger.info("")
    logger.info("✅ PostgreSQL + pgvector operativo")
    logger.info("✅ Conexión a base de datos funcionando")
    logger.info("✅ Extensión pgvector instalada")
    logger.info("")
    logger.info("🚀 Próximos pasos:")
    logger.info("   1. Ejecutar migración: python scripts/migrate_to_pgvector.py")
    logger.info("   2. Verificar migración: python scripts/verify_pgvector_migration.py")
    logger.info("   3. Iniciar aplicación: python -m streamlit run app/Inicio.py")
    logger.info("")
    logger.info("💡 Consulta MIGRATION_GUIDE.md para instrucciones completas")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)