#!/usr/bin/env python3
"""
Script de configuración para desarrollo local con PostgreSQL + pgvector
Ejecutar este script para configurar el entorno de desarrollo local
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_python_version():
    """Verificar versión de Python"""
    version = sys.version_info
    if version.major != 3 or version.minor < 11:
        logger.error("❌ Se requiere Python 3.11 o superior")
        return False
    logger.info(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_python_dependencies():
    """Instalar dependencias de Python (versión simplificada)"""
    try:
        logger.info("📦 Instalando dependencias esenciales de Python...")

        # Instalar dependencias básicas primero
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ])

        # Instalar dependencias esenciales para RAG básico
        essential_packages = [
            "langchain", "langchain-community", "langchain-core",
            "sentence-transformers", "streamlit", "fastapi", "uvicorn",
            "python-dotenv", "PyYAML", "pandas", "python-docx",
            "python-multipart", "prometheus-client", "aiohttp",
            "psycopg2-binary", "SQLAlchemy", "pydantic",
            "python-multipart", "markdown"
        ]

        for package in essential_packages:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package
                ])
                logger.info(f"✅ Instalado: {package}")
            except subprocess.CalledProcessError:
                logger.warning(f"⚠️ No se pudo instalar: {package}")

        logger.info("✅ Dependencias esenciales instaladas")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error instalando dependencias: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return False

def create_local_env_file():
    """Crear archivo .env para desarrollo local"""
    try:
        env_content = """# =============================================================================
# Configuración para desarrollo local con PostgreSQL + pgvector
# =============================================================================

# Base de datos PostgreSQL
PG_HOST=localhost
PG_PORT=5432
PG_DB=anclora_rag_local
PG_USER=anclora_user
PG_PASSWORD=anclora_password

# Modelo de lenguaje
MODEL=llama3
EMBEDDINGS_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
TARGET_SOURCE_CHUNKS=5

# Configuración de seguridad (generar valores seguros para producción)
ANCLORA_API_TOKENS=dev-token-12345
ANCLORA_API_TOKEN=dev-token-12345
ANCLORA_JWT_SECRET=your-super-secret-jwt-key-change-this-in-production

# Configuración de aplicación
DB_TYPE=postgres
PYTHONPATH=${PYTHONPATH}:./app

# Configuración de logs
LOG_LEVEL=INFO
"""

        env_file = Path(__file__).parent / ".env.local"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)

        logger.info(f"✅ Archivo .env.local creado: {env_file}")
        return True

    except Exception as e:
        logger.error(f"❌ Error creando archivo .env.local: {e}")
        return False

def create_postgresql_config():
    """Crear script de configuración de PostgreSQL"""
    try:
        # Crear directorio scripts si no existe
        scripts_dir = Path(__file__).parent / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        postgres_config = """#!/bin/bash
# =============================================================================
# Script de configuración de PostgreSQL para desarrollo local
# =============================================================================

echo "🐘 Configurando PostgreSQL con pgvector..."

# Variables de configuración
DB_NAME="anclora_rag_local"
DB_USER="anclora_user"
DB_PASSWORD="anclora_password"

# Crear base de datos si no existe
echo "📊 Creando base de datos..."
createdb -U postgres $DB_NAME 2>/dev/null || echo "Base de datos ya existe"

# Crear usuario si no existe
echo "👤 Creando usuario..."
psql -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD' CREATEDB;" 2>/dev/null || echo "Usuario ya existe"

# Conceder permisos
echo "🔐 Configurando permisos..."
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Conectar a la base de datos y configurar pgvector
echo "🔧 Instalando extensión pgvector..."
psql -U $DB_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Crear esquema para LangChain
echo "📋 Creando esquema LangChain..."
psql -U $DB_USER -d $DB_NAME -c "CREATE SCHEMA IF NOT EXISTS langchain;"

# Conceder permisos en esquema
echo "🔑 Configurando permisos de esquema..."
psql -U $DB_USER -d $DB_NAME -c "GRANT USAGE ON SCHEMA langchain TO $DB_USER;"
psql -U $DB_USER -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA langchain TO $DB_USER;"
psql -U $DB_USER -d $DB_NAME -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA langchain TO $DB_USER;"

echo "✅ PostgreSQL configurado correctamente"
echo ""
echo "📋 Información de conexión:"
echo "   Host: localhost"
echo "   Puerto: 5432"
echo "   Base de datos: $DB_NAME"
echo "   Usuario: $DB_USER"
echo "   Contraseña: $DB_PASSWORD"
echo ""
echo "🔗 Puedes conectarte con: psql -h localhost -p 5432 -U $DB_USER -d $DB_NAME"
"""

        config_file = scripts_dir / "setup_postgresql.sh"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(postgres_config)

        # Hacer ejecutable en sistemas Unix
        try:
            os.chmod(config_file, 0o755)
        except:
            pass  # Ignorar en Windows

        logger.info(f"✅ Script de configuración PostgreSQL creado: {config_file}")
        return True

    except Exception as e:
        logger.error(f"❌ Error creando configuración PostgreSQL: {e}")
        return False

def create_run_local_script():
    """Crear script para ejecutar aplicación localmente"""
    try:
        run_script = """#!/bin/bash
# =============================================================================
# Script para ejecutar Anclora RAG en modo local
# =============================================================================

echo "🚀 Iniciando Anclora RAG en modo desarrollo local..."

# Cargar variables de entorno
if [ -f ".env.local" ]; then
    echo "📋 Cargando configuración local..."
    source .env.local
else
    echo "❌ Archivo .env.local no encontrado"
    exit 1
fi

# Verificar si PostgreSQL está corriendo
if ! pg_isready -h $PG_HOST -p $PG_PORT; then
    echo "❌ PostgreSQL no está corriendo en $PG_HOST:$PG_PORT"
    echo "💡 Inicia PostgreSQL y ejecuta: scripts/setup_postgresql.sh"
    exit 1
fi

echo "✅ PostgreSQL conectado correctamente"

# Ejecutar aplicación Streamlit
echo "🌐 Iniciando interfaz web Streamlit..."
echo "📍 La aplicación estará disponible en: http://localhost:8501"
echo "🔄 Presiona Ctrl+C para detener"

cd app
python -m streamlit run Inicio.py \\
    --server.port 8501 \\
    --server.address 0.0.0.0 \\
    --browser.gatherUsageStats false
"""

        scripts_dir = Path(__file__).parent / "scripts"
        script_file = scripts_dir / "run_local.sh"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(run_script)

        # Hacer ejecutable en sistemas Unix
        try:
            os.chmod(script_file, 0o755)
        except:
            pass

        logger.info(f"✅ Script de ejecución local creado: {script_file}")
        return True

    except Exception as e:
        logger.error(f"❌ Error creando script de ejecución: {e}")
        return False

def main():
    """Función principal de configuración"""
    logger.info("🔧 Configurando entorno de desarrollo local...")

    # Verificar Python
    if not check_python_version():
        return False

    # Instalar dependencias
    if not install_python_dependencies():
        return False

    # Crear archivos de configuración
    if not create_local_env_file():
        return False

    if not create_postgresql_config():
        return False

    if not create_run_local_script():
        return False

    logger.info("")
    logger.info("🎉 ¡Configuración completada exitosamente!")
    logger.info("")
    logger.info("📋 Próximos pasos:")
    logger.info("   1. Instalar y configurar PostgreSQL con pgvector")
    logger.info("   2. Ejecutar: scripts/setup_postgresql.sh")
    logger.info("   3. Ejecutar: scripts/run_local.sh")
    logger.info("   4. Acceder a: http://localhost:8501")
    logger.info("")
    logger.info("💡 Consulta MIGRATION_GUIDE.md para más detalles")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)