#!/usr/bin/env python3
"""
Script para analizar todos los formatos de archivo soportados por Anclora RAG
y las dependencias necesarias para procesarlos.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

def get_supported_formats():
    """Obtiene todos los formatos soportados de cada agente"""
    
    formats = {
        "documents": {},
        "code": {},
        "multimedia": {},
        "archives": {}
    }
    
    try:
        # Documentos
        from agents.document_agent.ingestor import DOCUMENT_LOADERS
        formats["documents"] = DOCUMENT_LOADERS
        print("✅ Formatos de documentos cargados")
    except Exception as e:
        print(f"❌ Error cargando formatos de documentos: {e}")
    
    try:
        # Código
        from agents.code_agent.ingestor import CODE_LOADERS
        formats["code"] = CODE_LOADERS
        print("✅ Formatos de código cargados")
    except Exception as e:
        print(f"❌ Error cargando formatos de código: {e}")
    
    try:
        # Multimedia
        from agents.media_agent.ingestor import MULTIMEDIA_LOADERS
        formats["multimedia"] = MULTIMEDIA_LOADERS
        print("✅ Formatos multimedia cargados")
    except Exception as e:
        print(f"❌ Error cargando formatos multimedia: {e}")
    
    try:
        # Archivos comprimidos
        from agents.archive_agent.ingestor import ARCHIVE_LOADERS
        formats["archives"] = ARCHIVE_LOADERS
        print("✅ Formatos de archivos cargados")
    except Exception as e:
        print(f"❌ Error cargando formatos de archivos: {e}")
    
    return formats

def analyze_dependencies(formats):
    """Analiza las dependencias necesarias para cada tipo de formato"""
    
    dependencies = {
        "python_packages": set(),
        "system_tools": set(),
        "optional_tools": set()
    }
    
    # Dependencias por categoría
    category_deps = {
        "documents": {
            "python_packages": {
                "langchain-community", "unstructured", "python-docx", "PyMuPDF", 
                "python-magic", "pandas", "openpyxl", "xlrd", "python-pptx",
                "beautifulsoup4", "lxml", "markdown", "pypandoc"
            },
            "system_tools": {
                "pandoc", "poppler-utils", "tesseract-ocr", "libreoffice", 
                "wkhtmltopdf", "imagemagick"
            },
            "optional_tools": {"calibre"}
        },
        "code": {
            "python_packages": {"langchain-community", "pygments", "tree-sitter"},
            "system_tools": {"git"},
            "optional_tools": {"clang", "gcc", "node", "java", "go", "rustc"}
        },
        "multimedia": {
            "python_packages": {
                "openai-whisper", "moviepy", "ffmpeg-python", "opencv-python",
                "pillow", "librosa", "pydub", "speech_recognition"
            },
            "system_tools": {"ffmpeg", "sox", "mediainfo"},
            "optional_tools": {"youtube-dl", "yt-dlp"}
        },
        "archives": {
            "python_packages": {
                "llama-parse", "zipfile", "tarfile", "rarfile", "py7zr"
            },
            "system_tools": {"unzip", "tar", "gzip"},
            "optional_tools": {"7zip", "rar", "unrar"}
        }
    }
    
    # Agregar dependencias basadas en formatos encontrados
    for category, category_formats in formats.items():
        if category_formats and category in category_deps:
            deps = category_deps[category]
            dependencies["python_packages"].update(deps["python_packages"])
            dependencies["system_tools"].update(deps["system_tools"])
            dependencies["optional_tools"].update(deps["optional_tools"])
    
    return dependencies

def print_format_summary(formats):
    """Imprime un resumen de todos los formatos soportados"""
    
    print("\n📋 FORMATOS SOPORTADOS POR ANCLORA RAG")
    print("=" * 60)
    
    for category, category_formats in formats.items():
        if not category_formats:
            continue
            
        print(f"\n📁 {category.upper()}")
        print("-" * 30)
        
        # Agrupar por tipo de loader
        loader_groups = {}
        for ext, (loader_class, config) in category_formats.items():
            loader_name = loader_class.__name__
            if loader_name not in loader_groups:
                loader_groups[loader_name] = []
            loader_groups[loader_name].append(ext)
        
        for loader_name, extensions in loader_groups.items():
            extensions_str = ", ".join(sorted(extensions))
            print(f"  {loader_name:<30} {extensions_str}")
    
    # Contar totales
    total_formats = sum(len(formats) for formats in formats.values())
    print(f"\n📊 TOTAL: {total_formats} formatos de archivo soportados")

def print_dependencies_summary(dependencies):
    """Imprime un resumen de las dependencias necesarias"""
    
    print("\n🔧 DEPENDENCIAS NECESARIAS")
    print("=" * 60)
    
    print("\n🐍 PAQUETES DE PYTHON:")
    for package in sorted(dependencies["python_packages"]):
        print(f"  • {package}")
    
    print("\n🛠️  HERRAMIENTAS DEL SISTEMA (REQUERIDAS):")
    for tool in sorted(dependencies["system_tools"]):
        print(f"  • {tool}")
    
    print("\n⚙️  HERRAMIENTAS OPCIONALES:")
    for tool in sorted(dependencies["optional_tools"]):
        print(f"  • {tool}")

def generate_requirements_file(dependencies):
    """Genera un archivo requirements_complete.txt con todas las dependencias"""
    
    # Leer requirements.txt actual
    current_requirements = set()
    requirements_path = Path("app/requirements.txt")
    
    if requirements_path.exists():
        with open(requirements_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extraer solo el nombre del paquete (sin versión)
                    package_name = line.split('>=')[0].split('==')[0].split('<')[0]
                    current_requirements.add(package_name)
    
    # Combinar con nuevas dependencias
    all_packages = current_requirements.union(dependencies["python_packages"])
    
    # Generar archivo completo
    with open("requirements_complete.txt", 'w') as f:
        f.write("# Dependencias completas para Anclora RAG\n")
        f.write("# Incluye todas las librerías necesarias para procesar todos los formatos\n\n")
        
        f.write("# === DEPENDENCIAS CORE ===\n")
        core_packages = {
            "langchain>=0.2.0", "langchain-community>=0.2.0", "pydantic>=2.8.0",
            "chromadb==0.5.15", "streamlit>=1.28.0", "fastapi>=0.111.0"
        }
        for package in sorted(core_packages):
            f.write(f"{package}\n")
        
        f.write("\n# === PROCESAMIENTO DE DOCUMENTOS ===\n")
        doc_packages = {
            "unstructured[all-docs]", "python-docx", "PyMuPDF==1.23.5", 
            "python-magic>=0.4.27", "openpyxl", "xlrd", "python-pptx",
            "beautifulsoup4", "lxml", "markdown", "pypandoc"
        }
        for package in sorted(doc_packages):
            f.write(f"{package}\n")
        
        f.write("\n# === MULTIMEDIA ===\n")
        media_packages = {
            "openai-whisper>=20231117", "moviepy>=1.0.3", "ffmpeg-python>=0.2.0",
            "opencv-python", "Pillow", "librosa", "pydub", "SpeechRecognition"
        }
        for package in sorted(media_packages):
            f.write(f"{package}\n")
        
        f.write("\n# === CÓDIGO Y DESARROLLO ===\n")
        code_packages = {"pygments", "tree-sitter", "tree-sitter-languages"}
        for package in sorted(code_packages):
            f.write(f"{package}\n")
        
        f.write("\n# === ARCHIVOS COMPRIMIDOS ===\n")
        archive_packages = {"llama-parse>=0.4.0", "rarfile", "py7zr"}
        for package in sorted(archive_packages):
            f.write(f"{package}\n")
        
        f.write("\n# === UTILIDADES ADICIONALES ===\n")
        util_packages = {
            "pytesseract", "ebooklib", "epub-meta", "pdfplumber", 
            "camelot-py[cv]", "tabula-py", "python-docx2txt"
        }
        for package in sorted(util_packages):
            f.write(f"{package}\n")
    
    print(f"\n📄 Archivo 'requirements_complete.txt' generado con {len(all_packages)} paquetes")

def main():
    print("🔍 ANALIZADOR DE FORMATOS SOPORTADOS - ANCLORA RAG")
    print("=" * 60)
    
    # Obtener formatos soportados
    formats = get_supported_formats()
    
    # Analizar dependencias
    dependencies = analyze_dependencies(formats)
    
    # Mostrar resúmenes
    print_format_summary(formats)
    print_dependencies_summary(dependencies)
    
    # Generar archivo de requirements completo
    generate_requirements_file(dependencies)
    
    print("\n💡 PRÓXIMOS PASOS:")
    print("1. Ejecuta: python install_system_dependencies.py")
    print("2. Instala dependencias Python: pip install -r requirements_complete.txt")
    print("3. Verifica todo: python test_environment.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
