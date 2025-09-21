# Anclora AI RAG v1.0

Este repositorio contiene todo lo necesario para poder crear tu propia secretaria hecha con Inteligencia Artificial, todo gracias al RAG de Basdonax AI, que utiliza los modelos open source de Meta y de Microsoft: `Llama3-7b` y `Phi3-4b` para de esta forma darte la posibilidad de subir tus documentos y hacer consultas a los mismos. Esto fue creado para poder facilitarle la vida a las personas con la IA.

## Información del Proyecto

### Resumen

Anclora AI RAG es un sistema de Generación Aumentada por Recuperación (RAG) que permite a los usuarios subir documentos y realizar consultas sobre ellos utilizando modelos de lenguaje de código abierto como Llama3-7b y Phi3-4b. La aplicación proporciona una interfaz multilingüe (Español, Inglés, Francés, Alemán) y utiliza Docker para la contenerización.

### Estructura

- **app/**: Código principal de la aplicación incluyendo la interfaz de Streamlit, procesamiento de documentos e implementación RAG
- **docs/**: Archivos de documentación del proyecto
- **.vscode/**: Configuración de VS Code
- **docker-compose.yml**: Configuración Docker para setup con GPU (Llama3)
- **docker-compose_sin_gpu.yml**: Configuración Docker para setup sin GPU (Phi3)

### Lenguaje y Entorno

**Lenguaje**: Python 3.11  
**Framework**: Streamlit  
**Sistema de Construcción**: Docker  
**Gestor de Paquetes**: pip  

### Dependencias

**Dependencias Principales**:

- langchain (0.1.16)
- langchain-community (0.0.34)
- chromadb (0.4.7)
- streamlit
- sentence_transformers
- PyMuPDF (1.23.5)
- ollama (vía Docker)

**Servicios Externos**:

- ChromaDB (base de datos vectorial)
- Ollama (servicio LLM)

### Docker

**Dockerfile**: app/Dockerfile  
**Imágenes**:

- ollama/ollama:latest (servicio LLM)
- chromadb/chroma:0.5.1.dev111 (Base de datos vectorial)
- nvidia/cuda:12.3.1-base-ubuntu20.04 (Soporte GPU)
- Imagen UI personalizada construida desde ./app

**Configuración**:

- Paso de GPU para el modelo Llama3
- Configuración solo CPU disponible para el modelo Phi3
- Volumen persistente para ChromaDB
- Variables de entorno para selección de modelo y configuración de embeddings

### Archivos Principales

**Punto de Entrada**: app/Inicio.py  
**Módulos Clave**:

- app/common/langchain_module.py: Implementación RAG
- app/common/ingest_file.py: Procesamiento de documentos
- app/common/assistant_prompt.py: Plantilla de prompt para LLM
- app/pages/Archivos.py: Interfaz de gestión de archivos

### Uso

La aplicación se ejecuta en <http://localhost:8080> y proporciona:

- Interfaz de chat para consultar documentos
- Interfaz de carga de archivos para añadir documentos a la base de conocimiento
- Selección de idioma para la interfaz
- Gestión de documentos (ver y eliminar)

## Requisitos previos

- Docker o Docker desktop: <https://www.docker.com/products/docker-desktop/>
- **(opcional)** Tarjeta gráfica RTX

## Instalación

### Elección del modelo de datos (LLM)

Antes de comenzar con la instalación, tenemos que analizar si tenemos o no una tarjeta gráfica capaz de utilizar Llama3-7b o no. Si tenemos una tarjeta gráfica capaz de utilizar este modelo de datos utilizaremos el archivo `docker-compose.yml`, si no contamos con esa posibilidad vamos a eliminar el `docker-compose.yml` y vamos a renombrar el archivo `docker-compose_sin_gpu.yml` por `docker-compose.yml`. La diferencia entre un archivo y otro es que el `docker-compose_sin_gpu.yml` utiliza el LLM `Phi3-4b`, que es mucho más ligero para correrlo en el procesador de tu PC, mientras que `Llama3-7b` es mucho más pesado y si bien puede correr en CPU, es más recomendable una gráfica. En el video voy a estar utilizando una RTX 4060 8GB.

#### Docker Installation

Tenemos que tener Docker o Docker Desktop instalado, te recomiendo ver este video para instalar todo: <https://www.youtube.com/watch?v=ZyBBv1JmnWQ>

Una vez instalado y prendido el Docker Desktop si lo estamos utilizando, vamos a ejecutar en esta misma carpeta:

```bash
docker-compose up
```

La primera vez vamos a tener que esperar a que todo se instale correctamente, va a tardar unos cuantos minutos en ese paso.

Ahora tenemos que instalarnos nuestro modelo LLM, si tenemos una GPU que pueda soportar vamos a ejecutar el comando para traernos Llama3, sino va a ser Phi3 (si queremos utilizar otro modelo, en esta pagina: <https://ollama.com/library> tenes la lista de todos los modelos open source posibles en esta página, recorda que seguramente vayas a tener que hacer cambios en la prompt si cambias el modelo), ejecutamos:

```bash
docker ps
```

Te va a aparecer algo como esto:

```text
CONTAINER ID   IMAGE                    COMMAND                  CREATED              STATUS              PORTS                    NAMES
696d2e45ce7c   ui                       "/bin/sh -c 'streaml…"   About a minute ago   Up About a minute   0.0.0.0:8080->8080/tcp   ui-1
28cf32abee50   ollama/ollama:latest     "/bin/ollama serve"      About a minute ago   Up About a minute   11434/tcp                ollama-1
ec09714c3c86   chromadb/chroma:latest   "/docker_entrypoint.…"   About a minute ago   Up About a minute   0.0.0.0:8000->8000/tcp   chroma-1
```

En esta parte tenés que copiar el `CONTAINER ID` de la imagen llamada `ollama/ollama:latest` y utilizarla para este comando:

```bash
docker exec [CONTAINER ID] ollama pull [nombredelmodelo]
```

Un ejemplo con `Llama3-7b` y mi `CONTAINER ID`

```bash
docker exec 28cf32abee50 ollama pull llama3
```

Un ejemplo con `Phi3-4b` y mi `CONTAINER ID`

```bash
docker exec 28cf32abee50 ollama pull phi3
```

Ahora vamos a tener que esperar a que se descargue el modelo, una vez hecho esto solo nos queda modificar la prompt:

Esto se va a hacer a nuestro gusto en el archivo `./app/common/assistant_prompt.py`.

Una vez hecho todo lo anterior solo queda un paso: que entremos al siguiente link: <http://localhost:8080> para poder utilizar el RAG.

## Selección de idioma

La aplicación ahora soporta múltiples idiomas. Puedes cambiar el idioma de la interfaz utilizando el selector de idioma en la barra lateral. Los idiomas disponibles son:

- Español (por defecto)
- Inglés
- Francés
- Alemán

El idioma seleccionado se mantendrá durante toda la sesión.

## ¿Como ejecutarlo posteriormente instalado y una vez lo cerremos?

Tenemos que dejarnos en el escritorio el archivo de `open_rag.bat` si estamos en Windows y si estamos en Mac/Linux el `open_rag.sh`

Ahora tenemos que abrirlo y modificarlo, tenemos que agregar la ruta donde hicimos/tenemos el `docker-compose.yml`, por ejemplo mi ruta es:

```text
C:\Users\fcore\OneDrive\Desktop\Basdonax\basdonax-rag>
```

> 💡 Consulta la [guía detallada en `docs/guia_open_rag.md`](docs/guia_open_rag.md) para revisar prerrequisitos, pasos de ejecución y soluciones a errores comunes al usar `open_rag.sh` y `open_rag.bat`.

Entonces en mi caso va a ser así el `open_rag.bat` (el .sh es lo mismo):

```batch
cd C:\Users\fcore\OneDrive\Desktop\Basdonax\basdonax-rag
docker-compose up -d
```

Ahora mientras que tengamos el Docker/Docker Desktop prendido y mientras que ejecutemos este archivo vamos a poder acceder al RAG en este link: <http://localhost:8080>

Próximo paso: disfrutar
