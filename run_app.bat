@echo off
REM Anclora RAG Application Runner for Windows
REM
REM This script:
REM 1. Checks for existing Streamlit sessions on port 8501 and kills them
REM 2. Checks if virtual environment is active (provides instructions if not)
REM 3. Runs the Streamlit application
REM
REM Usage: run_app.bat

echo === Anclora RAG Application Runner ===

REM Check and kill existing processes on port 8501
echo Checking for existing processes on port 8501...
netstat -ano | findstr :8501 >nul
if %errorlevel% equ 0 (
    echo Found existing processes on port 8501. Killing them...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501') do (
        echo Killing process %%a
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo Existing processes killed.
) else (
    echo No existing processes found on port 8501.
)

REM Check if virtual environment is active
echo Checking virtual environment status...
if "%VIRTUAL_ENV%"=="" (
    echo WARNING: Virtual environment not active!
    echo.
    echo Please activate the virtual environment first by running:
    echo   venv_rag\Scripts\activate.bat
    echo.
    echo Or create it if it doesn't exist:
    echo   python -m venv venv_rag
    echo   venv_rag\Scripts\activate.bat
    echo.
    echo Then run this script again.
    pause
    exit /b 1
) else (
    echo Virtual environment is active: %VIRTUAL_ENV%
)

REM Run the Streamlit application
echo.
echo Starting application...
echo Press Ctrl+C to stop the application
echo.
python -m streamlit run app/Inicio.py --server.headless true --server.port 8501

echo.
echo Application stopped.
pause