#!/usr/bin/env python3
"""
Script para instalar todas las dependencias del sistema necesarias para Anclora RAG
Incluye herramientas para procesar documentos, audio, video, libros electrónicos, etc.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, description=""):
    """Ejecuta un comando y maneja errores"""
    print(f"🔧 {description}")
    print(f"   Ejecutando: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"   ✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stderr:
            print(f"   Error details: {e.stderr.strip()}")
        return False

def detect_os():
    """Detecta el sistema operativo"""
    system = platform.system().lower()
    if system == "linux":
        # Detectar distribución Linux
        try:
            with open("/etc/os-release") as f:
                content = f.read().lower()
                if "ubuntu" in content or "debian" in content:
                    return "debian"
                elif "centos" in content or "rhel" in content or "fedora" in content:
                    return "redhat"
        except:
            pass
        return "linux"
    elif system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    return "unknown"

def install_debian_dependencies():
    """Instala dependencias en sistemas Debian/Ubuntu"""
    packages = [
        # Herramientas básicas
        "curl", "wget", "git", "build-essential", "cmake", "pkg-config",
        
        # Para procesamiento de documentos
        "pandoc", "poppler-utils", "tesseract-ocr", "tesseract-ocr-spa", "tesseract-ocr-eng",
        "libreoffice", "wkhtmltopdf",
        
        # Para audio y video
        "ffmpeg", "libav-tools", "sox", "mediainfo",
        
        # Para libros electrónicos
        "calibre",
        
        # Para imágenes
        "imagemagick", "libopencv-dev", "python3-opencv",
        
        # Librerías del sistema
        "libmagic1", "libmagic-dev", "file",
        "libopenblas-dev", "liblapack-dev", "libatlas-base-dev",
        "libffi-dev", "libssl-dev", "libxml2-dev", "libxslt1-dev",
        "libjpeg-dev", "libpng-dev", "libtiff-dev", "libwebp-dev",
        "libfreetype6-dev", "liblcms2-dev", "libharfbuzz-dev", "libfribidi-dev",
        
        # Para Python
        "python3-dev", "python3-pip", "python3-venv",
        
        # Dependencias adicionales
        "zlib1g-dev", "libbz2-dev", "libreadline-dev", "libsqlite3-dev",
        "libncursesw5-dev", "xz-utils", "tk-dev", "libxml2-dev", "libxmlsec1-dev",
    ]
    
    print("📦 Instalando dependencias en Debian/Ubuntu...")
    
    # Actualizar repositorios
    if not run_command("sudo apt-get update", "Actualizando repositorios"):
        return False
    
    # Instalar paquetes
    packages_str = " ".join(packages)
    return run_command(f"sudo apt-get install -y {packages_str}", "Instalando paquetes del sistema")

def install_macos_dependencies():
    """Instala dependencias en macOS usando Homebrew"""
    
    # Verificar si Homebrew está instalado
    if not run_command("which brew", "Verificando Homebrew"):
        print("🍺 Instalando Homebrew...")
        install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        if not run_command(install_cmd, "Instalando Homebrew"):
            return False
    
    packages = [
        # Herramientas básicas
        "git", "cmake", "pkg-config",
        
        # Para procesamiento de documentos
        "pandoc", "poppler", "tesseract", "tesseract-lang", "libreoffice", "wkhtmltopdf",
        
        # Para audio y video
        "ffmpeg", "sox", "mediainfo",
        
        # Para libros electrónicos
        "calibre",
        
        # Para imágenes
        "imagemagick", "opencv",
        
        # Librerías del sistema
        "libmagic", "openblas", "lapack",
        "libffi", "openssl", "libxml2", "libxslt",
        "jpeg", "libpng", "libtiff", "webp", "freetype", "little-cms2",
        
        # Dependencias adicionales
        "zlib", "bzip2", "readline", "sqlite", "xz",
    ]
    
    print("📦 Instalando dependencias en macOS...")
    
    # Actualizar Homebrew
    if not run_command("brew update", "Actualizando Homebrew"):
        return False
    
    # Instalar paquetes
    for package in packages:
        run_command(f"brew install {package}", f"Instalando {package}")
    
    return True

def install_windows_dependencies():
    """Instala dependencias en Windows"""
    print("🪟 Para Windows, necesitas instalar manualmente:")
    print("1. Chocolatey: https://chocolatey.org/install")
    print("2. Luego ejecuta:")
    print("   choco install pandoc poppler tesseract ffmpeg imagemagick calibre")
    print("3. O usa conda/mamba:")
    print("   conda install -c conda-forge pandoc poppler tesseract ffmpeg opencv")
    
    # Verificar si chocolatey está disponible
    if run_command("choco --version", "Verificando Chocolatey"):
        packages = [
            "pandoc", "poppler", "tesseract", "ffmpeg", "imagemagick", "calibre",
            "libreoffice", "wkhtmltopdf"
        ]
        
        for package in packages:
            run_command(f"choco install -y {package}", f"Instalando {package}")
        
        return True
    
    return False

def install_python_dependencies():
    """Instala dependencias adicionales de Python que pueden faltar"""
    additional_packages = [
        # Para procesamiento de imágenes
        "opencv-python",
        "Pillow",
        
        # Para OCR
        "pytesseract",
        
        # Para procesamiento de documentos
        "python-magic",
        "unstructured[all-docs]",
        
        # Para libros electrónicos
        "ebooklib",
        "epub-meta",
        
        # Para audio/video (ya están en requirements.txt pero por si acaso)
        "openai-whisper",
        "moviepy",
        "ffmpeg-python",
        
        # Utilidades adicionales
        "python-docx2txt",
        "pdfplumber",
        "camelot-py[cv]",
    ]
    
    print("🐍 Instalando dependencias adicionales de Python...")
    
    for package in additional_packages:
        run_command(f"pip install {package}", f"Instalando {package}")
    
    return True

def verify_installations():
    """Verifica que las herramientas estén instaladas correctamente"""
    tools = {
        "pandoc": "pandoc --version",
        "ffmpeg": "ffmpeg -version",
        "tesseract": "tesseract --version",
        "convert (ImageMagick)": "convert -version",
        "calibre": "ebook-convert --version",
        "poppler": "pdfinfo -v",
    }
    
    print("\n🔍 Verificando instalaciones...")
    success_count = 0
    
    for tool, cmd in tools.items():
        if run_command(cmd, f"Verificando {tool}"):
            success_count += 1
    
    print(f"\n📊 Resultado: {success_count}/{len(tools)} herramientas instaladas correctamente")
    return success_count == len(tools)

def main():
    print("🚀 Instalador de dependencias del sistema para Anclora RAG")
    print("=" * 60)
    
    os_type = detect_os()
    print(f"🖥️  Sistema operativo detectado: {os_type}")
    
    success = False
    
    if os_type == "debian":
        success = install_debian_dependencies()
    elif os_type == "macos":
        success = install_macos_dependencies()
    elif os_type == "windows":
        success = install_windows_dependencies()
    else:
        print(f"❌ Sistema operativo no soportado: {os_type}")
        return 1
    
    if success:
        print("\n🐍 Instalando dependencias adicionales de Python...")
        install_python_dependencies()
        
        print("\n🔍 Verificando instalaciones...")
        if verify_installations():
            print("\n🎉 ¡Todas las dependencias instaladas correctamente!")
            print("🚀 Ahora puedes ejecutar: python test_environment.py")
            return 0
        else:
            print("\n⚠️  Algunas herramientas no se instalaron correctamente")
            return 1
    else:
        print("\n❌ Error instalando dependencias del sistema")
        return 1

if __name__ == "__main__":
    sys.exit(main())
