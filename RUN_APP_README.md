# Anclora RAG Application Runner

This directory contains scripts to easily run the Anclora RAG application with proper environment setup.

## Scripts Available

### `run_app.py` (Cross-platform Python script)

- **Language**: Python 3
- **Features**:
  - Checks for existing Streamlit processes on port 8501 and kills them
  - Verifies virtual environment activation
  - Runs the Streamlit application
- **Usage**: `python run_app.py`

### `run_app.bat` (Windows batch script)

- **Platform**: Windows
- **Features**:
  - Checks for existing Streamlit processes on port 8501 and kills them
  - Verifies virtual environment activation (with helpful instructions)
  - Runs the Streamlit application
- **Usage**: `run_app.bat` or double-click the file

## Prerequisites

1. **Virtual Environment**: Make sure you have a virtual environment named `venv_rag` in the project root

   ```bash
   python -m venv venv_rag
   ```

2. **Activate Virtual Environment** (do this before running the scripts):

   ```bash
   # Windows
   venv_rag\Scripts\activate.bat

   # Linux/Mac
   source venv_rag/bin/activate
   ```

3. **Dependencies**: Ensure all required packages are installed in the virtual environment

   ```bash
   pip install -r requirements.txt
   ```

## How to Use

### Option 1: Using the Batch File (Windows)

1. Double-click `run_app.bat` or run it from command prompt
2. If virtual environment is not active, follow the instructions provided
3. The script will automatically:
   - Kill any existing Streamlit processes on port 8501
   - Start the application on <http://localhost:8501>

### Option 2: Using the Python Script (Cross-platform)

1. Run `python run_app.py`
2. If virtual environment is not active, follow the instructions provided
3. The script will automatically:
   - Kill any existing Streamlit processes on port 8501
   - Start the application on <http://localhost:8501>

### Option 3: Manual Setup

If you prefer to do it manually:

1. **Kill existing processes** (if any):

   ```bash
   # Windows
   taskkill /F /IM streamlit.exe

   # Linux/Mac
   pkill -f streamlit
   ```

2. **Activate virtual environment**:

   ```bash
   # Windows
   venv_rag\Scripts\activate.bat

   # Linux/Mac
   source venv_rag/bin/activate
   ```

3. **Run the application**:

   ```bash
   streamlit run app/Inicio.py --server.headless true --server.port 8501
   ```

## Troubleshooting

### "Virtual environment not active" Error

- Make sure you've activated the virtual environment before running the script
- The scripts will provide clear instructions if the virtual environment is not active

### Port 8501 Already in Use

- The scripts automatically detect and kill processes using port 8501
- If this doesn't work, manually kill the processes using Task Manager (Windows) or `pkill` (Linux/Mac)

### Permission Errors

- Make sure you have permission to run the scripts
- On Windows, try running Command Prompt as Administrator

## Application URL

Once running, the application will be available at:
**<http://localhost:8501>**

## Stopping the Application

- Press `Ctrl+C` in the terminal where the application is running
- Or close the terminal/command prompt window
