# Guía de uso de `open_rag.sh` y `open_rag.bat`

Esta guía explica cómo utilizar los scripts incluidos en el repositorio para levantar Anclora AI RAG con Docker. Ambos archivos automatizan la entrada al directorio del proyecto y la ejecución de `docker-compose up -d` para iniciar los servicios en segundo plano.

## Prerrequisitos

Antes de ejecutar cualquiera de los scripts comprueba lo siguiente:

- **Repositorio clonado**: los scripts asumen que el proyecto está descargado en tu equipo local.
- **Docker Engine o Docker Desktop** con soporte para Docker Compose V2. En sistemas Linux asegúrate de que el comando `docker-compose` o el alias `docker compose` estén disponibles en tu `$PATH`.
- **Archivo `docker-compose.yml` configurado**: elige previamente si usarás el archivo con soporte GPU (`docker-compose.yml`) o el modo sin GPU (`docker-compose_sin_gpu.yml` renombrado a `docker-compose.yml`).
- **Permisos de ejecución (solo Linux/macOS)**: marca el script como ejecutable con `chmod +x open_rag.sh`.

## Configura la ruta del proyecto

Ambos scripts contienen una instrucción `cd` que debe apuntar a la carpeta donde vive tu `docker-compose.yml`. Actualiza la línea inicial antes de ejecutarlos:

- En Linux/macOS (`open_rag.sh`) la línea luce similar a: `cd /ruta/a/tu/Anclora-AI-RAG`.
- En Windows (`open_rag.bat`) la línea luce similar a: `cd C:\Ruta\a\tu\Anclora-AI-RAG`.

Puedes obtener la ruta correcta ejecutando `pwd` (Linux/macOS) o `cd` (Windows) dentro de la carpeta del repositorio y copiando el resultado en el script. Si la ruta es incorrecta el comando `cd` fallará y Docker Compose no llegará a ejecutarse.

## Ejecución en Linux y macOS (`open_rag.sh`)

1. Abre una terminal en cualquier carpeta.
2. Ejecuta el script con la ruta absoluta o relativa al archivo: `./open_rag.sh`.
3. El script cambiará al directorio configurado y lanzará `docker-compose up -d`, levantando Ollama, ChromaDB y la interfaz Streamlit en segundo plano.

### Ajustes opcionales

- Si tu instalación solo proporciona `docker compose` (sin guion), puedes editar la segunda línea del script y reemplazar `docker-compose` por `docker compose`.
- Para detener los servicios una vez terminada la sesión, ejecuta manualmente `docker-compose down` (o `docker compose down`) dentro del mismo directorio del proyecto.

## Ejecución en Windows (`open_rag.bat`)

1. Abre el Bloc de notas u otro editor y confirma que la primera línea apunta a la carpeta del proyecto.
2. Guarda el archivo y haz doble clic sobre `open_rag.bat` o ejecútalo desde `cmd.exe`/PowerShell con `./open_rag.bat`.
3. Docker Desktop iniciará los contenedores en segundo plano gracias a `docker-compose up -d`.

### Consejos adicionales

- Si deseas cerrar la aplicación, abre una ventana de `cmd.exe` en la carpeta del proyecto y ejecuta `docker-compose down`.
- Puedes crear un acceso directo al archivo `.bat` para facilitar futuros arranques.

## Resultados esperados y comprobaciones

Tras ejecutar cualquiera de los scripts deberías poder acceder a la interfaz en <http://localhost:8080>. Para confirmar que los servicios están activos utiliza `docker ps` y verifica que los contenedores `ui`, `ollama` y `chroma` se encuentren "Up".

## Limitaciones conocidas

- Los scripts no aceptan parámetros en línea de comandos: cualquier cambio de directorio o de archivo `docker-compose` debe realizarse editando el fichero.
- Si la ruta configurada en la instrucción `cd` no existe, la ejecución terminará con el mensaje `No such file or directory` (Linux/macOS) o `El sistema no puede encontrar la ruta especificada` (Windows).
- La validación completa requiere Docker en funcionamiento; en entornos sin Docker o dentro de contenedores aislados (como el usado para esta documentación) no es posible probar la puesta en marcha real.

Asegúrate de ajustar la ruta y contar con Docker activo antes de lanzar los scripts en tu entorno local.
