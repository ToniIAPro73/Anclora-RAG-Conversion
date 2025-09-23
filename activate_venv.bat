@echo off
echo.
echo ========================================
echo   🐍 Activando entorno virtual RAG
echo ========================================
echo.
echo ✅ Python 3.11.8 con todas las dependencias
echo ✅ llama-parse para procesar archivos ZIP
echo ✅ langchain, chromadb, streamlit, fastapi
echo ✅ Compatible con Pydantic v2
echo.
call venv_rag\Scripts\activate.bat
echo.
echo 🚀 Entorno virtual activado!
echo 💡 Para ejecutar la aplicación:
echo    streamlit run app/main.py
echo.
