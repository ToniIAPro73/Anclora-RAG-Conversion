#!/usr/bin/env python3
"""
Script para verificar que el entorno virtual está configurado correctamente
"""

import sys
import importlib.util
import subprocess
import shutil

def test_import(module_name, description=""):
    """Prueba importar un módulo y muestra el resultado"""
    try:
        if '.' in module_name:
            # Para imports como 'agents.archive_agent.ingestor'
            parts = module_name.split('.')
            module = __import__(module_name, fromlist=[parts[-1]])
        else:
            module = __import__(module_name)
        
        version = getattr(module, '__version__', 'N/A')
        print(f"✅ {module_name:<25} {description} (v{version})")
        return True
    except ImportError as e:
        print(f"❌ {module_name:<25} {description} - Error: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name:<25} {description} - Warning: {e}")
        return True

def test_system_tool(tool_name, command, description=""):
    """Prueba que una herramienta del sistema esté disponible"""
    try:
        if shutil.which(tool_name):
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {tool_name:<25} {description}")
                return True
            else:
                print(f"❌ {tool_name:<25} {description} - Error ejecutando")
                return False
        else:
            print(f"❌ {tool_name:<25} {description} - No encontrado")
            return False
    except Exception as e:
        print(f"⚠️  {tool_name:<25} {description} - Error: {e}")
        return False

def test_system_dependencies():
    """Verifica herramientas del sistema necesarias"""
    print("\n🔧 Verificando herramientas del sistema...")
    print("=" * 60)

    system_tools = [
        ("pandoc", "pandoc --version", "Conversión de documentos"),
        ("ffmpeg", "ffmpeg -version", "Procesamiento audio/video"),
        ("tesseract", "tesseract --version", "OCR (reconocimiento óptico)"),
        ("convert", "convert -version", "ImageMagick para imágenes"),
        ("ebook-convert", "ebook-convert --version", "Calibre para ebooks"),
        ("pdfinfo", "pdfinfo -v", "Poppler para PDFs"),
        ("git", "git --version", "Control de versiones"),
    ]

    success_count = 0
    total_count = len(system_tools)

    for tool, command, description in system_tools:
        if test_system_tool(tool, command, description):
            success_count += 1

    print("=" * 60)
    print(f"📊 Herramientas del sistema: {success_count}/{total_count} disponibles")

    if success_count < total_count:
        print("💡 Para instalar herramientas faltantes, ejecuta:")
        print("   python install_system_dependencies.py")

    return success_count, total_count

def main():
    print("🔍 Verificando entorno completo para Anclora RAG...")
    print("=" * 60)
    print(f"🐍 Python: {sys.version}")
    print("=" * 60)
    
    # Lista de módulos críticos para verificar
    modules_to_test = [
        # Core RAG
        ("llama_parse", "Procesamiento de documentos complejos"),
        ("langchain", "Framework LLM"),
        ("langchain_community", "Extensiones de LangChain"),
        ("pydantic", "Validación de datos"),
        ("chromadb", "Base de datos vectorial"),

        # Web y API
        ("streamlit", "Interfaz web"),
        ("fastapi", "API REST"),

        # Procesamiento de datos
        ("pandas", "Manipulación de datos"),
        ("numpy", "Computación numérica"),
        ("nltk", "Procesamiento de lenguaje natural"),

        # Documentos
        ("docx", "Procesamiento Word (python-docx)"),
        ("fitz", "Procesamiento PDF (PyMuPDF)"),
        ("unstructured", "Procesamiento documentos no estructurados"),

        # Audio y Video
        ("whisper", "Transcripción de audio (OpenAI Whisper)"),
        ("moviepy.editor", "Procesamiento de video"),
        ("ffmpeg", "Codecs de audio/video"),

        # Imágenes y OCR
        ("cv2", "Procesamiento de imágenes (OpenCV)"),
        ("PIL", "Manipulación de imágenes (Pillow)"),
        ("pytesseract", "OCR (Tesseract)"),

        # Libros electrónicos
        ("ebooklib", "Procesamiento de ebooks"),

        # APIs y servicios
        ("openai", "Cliente OpenAI"),
        ("plotly", "Visualización de datos"),

        # Utilidades
        ("magic", "Detección de tipos de archivo"),

        # Procesamiento adicional de documentos
        ("bs4", "BeautifulSoup para HTML"),
        ("lxml", "Parser XML/HTML"),
        ("openpyxl", "Archivos Excel modernos"),
        ("xlrd", "Archivos Excel legacy"),
        ("pptx", "Presentaciones PowerPoint"),
        ("pypandoc", "Conversión de documentos"),

        # Libros electrónicos
        ("ebooklib", "Procesamiento de ebooks"),
        ("epub_meta", "Metadatos de EPUB"),

        # Procesamiento avanzado de PDFs
        ("pdfplumber", "Extracción avanzada de PDFs"),
        ("camelot", "Extracción de tablas de PDFs"),
        ("tabula", "Tablas de PDFs con Tabula"),

        # Audio adicional
        ("librosa", "Análisis de audio"),
        ("pydub", "Manipulación de audio"),
        ("speech_recognition", "Reconocimiento de voz"),

        # Código y desarrollo
        ("pygments", "Resaltado de sintaxis"),
        ("tree_sitter", "Parsing de código"),

        # Archivos comprimidos
        ("py7zr", "Archivos 7z"),
        ("rarfile", "Archivos RAR"),
    ]
    
    success_count = 0
    total_count = len(modules_to_test)
    
    for module_name, description in modules_to_test:
        if test_import(module_name, description):
            success_count += 1
    
    print("=" * 60)
    print(f"📊 Resultado: {success_count}/{total_count} módulos importados correctamente")
    
    if success_count == total_count:
        print("🎉 ¡Entorno virtual configurado perfectamente!")
        print("🚀 Puedes ejecutar la aplicación con: streamlit run app/main.py")
    else:
        print("⚠️  Algunos módulos tienen problemas. Revisa las dependencias.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
