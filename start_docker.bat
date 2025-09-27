@echo off
echo ========================================
echo Anclora RAG - Docker Startup Script
echo ========================================

echo.
echo Stopping any existing containers...
docker compose down

echo.
echo Building images (this may take a few minutes)...
docker compose build --no-cache

echo.
echo Starting services...
docker compose up -d

echo.
echo Waiting for services to be ready...
timeout /t 30 /nobreak > nul

echo.
echo Checking service status...
docker compose ps

echo.
echo ========================================
echo Services should be available at:
echo - UI (Streamlit): http://localhost:8501
echo - API (FastAPI): http://localhost:8081
echo - ChromaDB: http://localhost:8000
echo - Prometheus: http://localhost:9090
echo - Grafana: http://localhost:3000
echo ========================================

echo.
echo To view logs, use: docker compose logs -f [service_name]
echo To stop services, use: docker compose down
echo.
pause