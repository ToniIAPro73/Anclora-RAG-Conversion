# Usa una imagen base de Python mas ligera
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    cmake \
    pkg-config \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar requirements primero para mejor cache de Docker
COPY requirements.txt .

# Actualizar pip e instalar dependencias
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto del codigo
COPY . .

# Exponer el puerto
EXPOSE 8080

# Configurar healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# Comando para ejecutar la aplicacion
CMD ["streamlit", "run", "Inicio.py", "--server.port", "8080", "--server.address", "0.0.0.0"]
