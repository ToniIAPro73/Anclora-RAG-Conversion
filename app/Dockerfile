# Multi-stage build for both API and UI services
FROM python:3.11-slim as base

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    cmake \
    pkg-config \
    libopenblas-dev \
    libmagic1 \
    libmagic-dev \
    file \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar requirements primero para mejor cache de Docker
COPY requirements.txt .

# Actualizar pip e instalar dependencias
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Descargar datos de NLTK necesarios
RUN python -c "import nltk; nltk.download('punkt')"

# Copiar el resto del codigo
COPY . .

# Configurar PYTHONPATH para que Python encuentre el módulo app
ENV PYTHONPATH=/app

# ==========================================
# Stage for API service
# ==========================================
FROM base as api-service

# Configurar healthcheck para API
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Exponer puerto para API
EXPOSE 8081

# Comando para ejecutar la API
CMD ["python", "-c", "import api_endpoints; import uvicorn; uvicorn.run(api_endpoints.app, host='0.0.0.0', port=8081)"]

# ==========================================
# Stage for UI service (default)
# ==========================================
FROM base as ui-service

# Configurar variables de entorno para Streamlit
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_HEADLESS=true

# Configurar healthcheck para Streamlit
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Exponer puerto para Streamlit
EXPOSE 8501

# Comando para ejecutar Streamlit
CMD ["streamlit", "run", "Inicio.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--browser.gatherUsageStats", "false"]
