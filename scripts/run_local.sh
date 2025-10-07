#!/bin/bash
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
python -m streamlit run Inicio.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --browser.gatherUsageStats false
