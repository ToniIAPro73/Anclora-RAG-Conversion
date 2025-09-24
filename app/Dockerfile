# Usa una imagen base de Python mas ligera
FROM python:3.11-slim

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

# Configurar variables de entorno para Streamlit
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_HEADLESS=true

# Exponer el puerto
EXPOSE 8501

# Configurar healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Comando para ejecutar la aplicacion
CMD ["streamlit", "run", "Inicio.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--browser.gatherUsageStats", "false"]
