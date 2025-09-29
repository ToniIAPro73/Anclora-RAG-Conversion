#!/usr/bin/env python3
"""
Simple script to ingest Pandoc documentation into the RAG system.
This script creates sample Pandoc documentation files and uploads them directly.
"""

import os
import sys
import requests
import json
import time
from pathlib import Path
from typing import List

class SimplePandocIngestor:
    def __init__(self, api_url: str = "http://localhost:8081", api_token: str | None = None):
        self.api_url = api_url
        self.api_token = api_token or os.getenv("ANCLORA_API_TOKEN", "iFqEvYPHcqfyCQvDV8vPcS0Z10SZDeVJ9ErCAR5uEU4")
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
        }

    def test_api_connection(self) -> bool:
        """Test if the API is accessible."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                print("[OK] API connection successful")
                return True
            else:
                print(f"[ERROR] API returned status code: {response.status_code}")
                return False
        except Exception as e:
            print(f"[ERROR] API connection failed: {e}")
            return False

    def create_pandoc_documentation(self) -> List[str]:
        """Create sample Pandoc documentation files."""
        print("Creating Pandoc documentation files...")

        files_created = []

        # Main Pandoc README
        pandoc_readme = """# Pandoc - Convertidor Universal de Documentos

Pandoc es una herramienta de línea de comandos que convierte archivos de un formato de marcado a otro.

## Características Principales

- **Conversión Universal**: Soporta docenas de formatos de entrada y salida
- **Filtros**: Sistema extensible de filtros Lua
- **Plantillas**: Plantillas personalizables para diferentes formatos
- **Metadatos**: Soporte completo para metadatos

## Formatos Soportados

### Formatos de Entrada
- Markdown (incluyendo Pandoc Markdown)
- HTML
- LaTeX
- reStructuredText
- Textile
- DocBook
- JATS
- OPML
- Org-mode
- Y muchos más...

### Formatos de Salida
- HTML (incluyendo HTML5)
- PDF (a través de LaTeX)
- Word docx
- EPUB
- LaTeX
- reStructuredText
- Markdown
- Y muchos más...

## Instalación

```bash
# Usando el instalador oficial
curl -s https://api.github.com/repos/jgm/pandoc/releases/latest \\
| grep "browser_download_url.*linux-amd64.deb" \\
| cut -d '"' -f 4 \\
| xargs curl -L -o pandoc.deb && sudo dpkg -i pandoc.deb

# Usando conda
conda install -c conda-forge pandoc

# Usando chocolatey (Windows)
choco install pandoc
```

## Uso Básico

```bash
# Convertir Markdown a HTML
pandoc documento.md -o documento.html

# Convertir HTML a Markdown
pandoc documento.html -o documento.md

# Convertir Markdown a PDF
pandoc documento.md -o documento.pdf

# Convertir Word a Markdown
pandoc documento.docx -o documento.md
```

## Ejemplos Avanzados

### Con Metadatos
```yaml
---
title: "Mi Documento"
author: "Autor del Documento"
date: "2024-01-01"
---
```

### Con Filtros Lua
```bash
pandoc --filter mi-filtro.lua entrada.md -o salida.html
```

## Arquitectura

Pandoc está escrito principalmente en Haskell y utiliza un sistema de lectores y escritores modulares para manejar diferentes formatos.

- **Lectores**: Analizan el formato de entrada
- **Transformadores**: Aplican transformaciones al documento
- **Escritores**: Generan el formato de salida

## Comunidad y Contribución

- **Sitio web oficial**: https://pandoc.org/
- **Repositorio GitHub**: https://github.com/jgm/pandoc
- **Documentación**: https://pandoc.org/MANUAL.html
- **Lista de correo**: pandoc-discuss@groups.google.com

## Licencia

Pandoc está disponible bajo la licencia GPL versión 2 o posterior.
"""

        # Pandoc Manual (excerpt)
        pandoc_manual = """# Manual de Pandoc (Extracto)

## Introducción

Pandoc es un conversor universal de documentos que puede transformar documentos entre diferentes formatos de marcado.

## Sintaxis de Markdown

### Encabezados
```markdown
# Encabezado Nivel 1
## Encabezado Nivel 2
### Encabezado Nivel 3
```

### Énfasis
```markdown
*cursiva* o _cursiva_
**negrita** o __negrita__
`código`
```

### Listas
```markdown
- Elemento de lista
- Otro elemento
  - Sub-elemento
  - Otro sub-elemento

1. Elemento numerado
2. Otro elemento numerado
```

### Enlaces e Imágenes
```markdown
[texto del enlace](URL)
![texto alternativo](URL_de_la_imagen)
```

## Extensiones de Pandoc

Pandoc incluye varias extensiones útiles para Markdown:

- **Tablas**: Sintaxis de tablas pipe
- **Notas al pie**: Referencias de notas al pie
- **Citas**: Soporte para citas bibliográficas
- **Definiciones**: Listas de definiciones
- **Matemáticas**: Fórmulas matemáticas con MathJax
- **Superíndices y subíndices**: ^superíndice^ y ~subíndice~
- **Elementos tachados**: ~~texto tachado~~

## Procesamiento de Citas

Pandoc puede procesar citas usando archivos CSL (Citation Style Language):

```bash
pandoc --bibliography=refs.bib --csl=ieee.csl entrada.md -o salida.html
```

## Salidas Especiales

### Diapositivas
Pandoc puede generar presentaciones usando varias herramientas:

- **Beamer**: Para LaTeX
- **Reveal.js**: Para HTML
- **PPTX**: Para PowerPoint

### Libros Electrónicos
```bash
pandoc capitulos.md -o libro.epub
```

## Consejos y Trucos

1. **Dividir documentos grandes**: Usa archivos separados y --file-scope
2. **Personalizar plantillas**: Crea plantillas personalizadas para HTML/PDF
3. **Usar filtros**: Los filtros Lua pueden automatizar tareas repetitivas
4. **Variables de plantilla**: Usa $-variables$ para contenido dinámico
5. **Metadatos YAML**: Incluye metadatos al inicio del documento

## Solución de Problemas

### Problemas Comunes

1. **Codificación de caracteres**: Asegúrate de usar UTF-8
2. **Caminos de archivos**: Usa comillas para caminos con espacios
3. **Dependencias**: Instala dependencias necesarias (LaTeX para PDF)
4. **Memoria**: Documentos grandes pueden requerir más memoria

### Recursos de Ayuda

- Manual oficial: https://pandoc.org/MANUAL.html
- Comunidad: https://groups.google.com/forum/#!forum/pandoc-discuss
- Wiki: https://github.com/jgm/pandoc/wiki
"""

        # Pandoc Use Cases
        pandoc_use_cases = """# Casos de Uso de Pandoc

## Automatización de Documentos

Pandoc es ideal para:

### Generación de Informes
- Convertir datos de investigación a múltiples formatos
- Crear informes académicos en PDF y HTML
- Generar documentación técnica

### Publicación Web
- Convertir Markdown a HTML para sitios web
- Crear blogs desde archivos de texto
- Generar documentación para GitHub Pages

### Publicación Académica
- Convertir tesis de Word a PDF académico
- Gestionar referencias bibliográficas
- Crear presentaciones para conferencias

### Documentación Técnica
- Convertir README.md a múltiples formatos
- Crear manuales de usuario
- Generar documentación de API

## Ejemplos Prácticos

### Script de Conversión Automática
```bash
#!/bin/bash
# Convertir todos los .md a HTML y PDF
for file in *.md; do
    base=$(basename "$file" .md)
    pandoc "$file" -o "${base}.html"
    pandoc "$file" -o "${base}.pdf"
done
```

### Pipeline de Publicación
```bash
# Generar sitio web completo
pandoc --template=templates/default.html \\
       --output-dir=public \\
       --standalone \\
       content/*.md
```

### Integración con Git
```bash
# Hook de Git para generar PDF en commits
#!/bin/bash
pandoc main.md -o docs/latest.pdf
git add docs/latest.pdf
```

## Ventajas de Pandoc

1. **Consistencia**: Mismo contenido en múltiples formatos
2. **Automatización**: Procesamiento por lotes
3. **Flexibilidad**: Fácil personalización
4. **Comunidad**: Amplio soporte y documentación
5. **Estabilidad**: Herramienta madura y confiable

## Limitaciones

1. **Curva de aprendizaje**: Requiere familiaridad con la sintaxis
2. **Dependencias**: Necesita herramientas externas para algunos formatos
3. **Tamaño**: Documentos muy grandes pueden ser lentos
4. **Personalización compleja**: Las plantillas avanzadas requieren tiempo

## Alternativas

- **Marked 2**: Aplicación macOS para Markdown
- **Typora**: Editor WYSIWYG para Markdown
- **MultiMarkdown**: Extensión de Markdown
- **RMarkdown**: Integración con R para análisis reproducibles
"""

        # Save files
        files_content = [
            ("pandoc_readme.md", pandoc_readme),
            ("pandoc_manual.md", pandoc_manual),
            ("pandoc_use_cases.md", pandoc_use_cases)
        ]

        for filename, content in files_content:
            file_path = Path(filename)
            file_path.write_text(content, encoding='utf-8')
            files_created.append(filename)
            print(f"   [OK] Created: {filename}")

        return files_created

    def upload_file_to_api(self, file_path: str, filename: str) -> bool:
        """Upload a single file through the API."""
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()

            files = {
                'file': (filename, file_content, 'application/octet-stream')
            }

            response = requests.post(
                f"{self.api_url}/upload",
                files=files,
                headers={"Authorization": f"Bearer {self.api_token}"},
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                print(f"   [OK] Uploaded: {filename}")
                return True
            else:
                print(f"   [ERROR] Upload failed for {filename}: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"   [ERROR] Error uploading {filename}: {e}")
            return False

    def check_indexed_documents(self) -> list:
        """Check what documents are currently indexed."""
        try:
            response = requests.get(
                f"{self.api_url}/documents",
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                documents = result.get("documents", [])
                print(f"DOCS: Currently indexed documents: {len(documents)}")
                for doc in documents[:10]:
                    print(f"   • {doc}")
                if len(documents) > 10:
                    print(f"   ... and {len(documents) - 10} more")
                return documents
            else:
                print(f"[ERROR] Failed to get documents: {response.status_code}")
                return []

        except Exception as e:
            print(f"[ERROR] Error checking documents: {e}")
            return []

    def test_pandoc_query(self) -> bool:
        """Test a query about Pandoc to verify ingestion worked."""
        print("TEST: Testing Pandoc query...")

        test_query = "¿Qué me puedes contar acerca de la librería Pandoc?"

        try:
            response = requests.post(
                f"{self.api_url}/chat",
                headers=self.headers,
                json={
                    "message": test_query,
                    "language": "es",
                    "max_length": 1000
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")

                print("[OK] Query successful!")
                print(f"INFO: Response preview: {response_text[:200]}...")

                # Check if the response contains actual information about Pandoc
                pandoc_keywords = ["pandoc", "conversión", "documentos", "markdown", "formato"]
                has_pandoc_info = any(keyword in response_text.lower() for keyword in pandoc_keywords)

                if has_pandoc_info and "no tengo documentos" not in response_text.lower():
                    print("[OK] Response contains Pandoc information - ingestion successful!")
                    return True
                else:
                    print("WARNING: Response doesn't contain specific Pandoc information")
                    return False
            else:
                print(f"[ERROR] Query failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"[ERROR] Error during query test: {e}")
            return False

    def run_ingestion(self):
        """Run the complete ingestion process."""
        print("Starting Pandoc documentation ingestion process")
        print("=" * 60)

        # Step 1: Test API connection
        if not self.test_api_connection():
            print("[ERROR] Cannot proceed without API connection")
            return False

        # Step 2: Create documentation files
        files_created = self.create_pandoc_documentation()

        # Step 3: Upload files
        uploaded_count = 0
        for filename in files_created:
            if self.upload_file_to_api(filename, filename):
                uploaded_count += 1

        print(f"\nSTATS: Upload complete: {uploaded_count}/{len(files_created)} files uploaded")

        # Step 4: Wait a bit for processing
        print("WAIT: Waiting for document processing...")
        import time
        time.sleep(15)

        # Step 5: Check indexed documents
        print("\nCHECK: Checking indexed documents...")
        documents = self.check_indexed_documents()

        # Step 6: Test query
        print("\nTEST: Testing Pandoc query...")
        query_success = self.test_pandoc_query()

        # Step 7: Cleanup
        for filename in files_created:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"CLEAN: Cleaned up: {filename}")

        # Final results
        print("\n" + "=" * 60)
        print("RESULTS: INGESTION RESULTS")
        print("=" * 60)
        print(f"INFO: Files created: {len(files_created)}")
        print(f"UPLOAD: Files uploaded: {uploaded_count}")
        print(f"DOCS: Documents indexed: {len(documents)}")
        print(f"TEST: Query test: {'[OK] PASSED' if query_success else '[ERROR] FAILED'}")

        return query_success

def main():
    """Main function."""
    api_token = os.getenv("ANCLORA_API_TOKEN", "iFqEvYPHcqfyCQvDV8vPcS0Z10SZDeVJ9ErCAR5uEU4")

    ingestor = SimplePandocIngestor(api_token=api_token)
    success = ingestor.run_ingestion()

    if success:
        print("\nSUCCESS: Pandoc documentation successfully ingested into RAG system!")
        print("You can now ask questions about Pandoc and get informed responses.")
    else:
        print("\nWARNING: Ingestion completed but query test failed.")
        print("The documents may still be processing or there might be an issue.")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()