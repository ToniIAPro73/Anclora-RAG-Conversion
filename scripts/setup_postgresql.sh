#!/bin/bash
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
