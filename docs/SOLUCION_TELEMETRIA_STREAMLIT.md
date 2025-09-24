# Solución al Problema de Telemetría de Streamlit

## 🔍 Diagnóstico del Problema

### Síntomas Observados

- La aplicación UI se queda en un bucle de ejecución sin salir
- Error repetitivo en los logs: `Failed to send telemetry event client_start: capture() takes 1 positional argument but 3 were given`
- Los servicios de salud (healthcheck) reportan como "healthy" pero la UI no funciona correctamente
- Logs muestran reinicio constante de Streamlit con recolección de estadísticas de uso

### Causa Raíz

El problema se debe a un conflicto de versiones en el sistema de telemetría de Streamlit. La función `capture()` del sistema de telemetría está recibiendo más argumentos de los esperados, lo que indica una incompatibilidad entre la versión de Streamlit instalada y las dependencias internas de telemetría.

## 🛠️ Solución Implementada

### 1. Configuración de Streamlit (.streamlit/config.toml)

Se creó el archivo `app/.streamlit/config.toml` con la siguiente configuración:

```toml
[browser]
gatherUsageStats = false

[server]
headless = true
port = 8501
address = "0.0.0.0"

[theme]
base = "light"

[client]
showErrorDetails = false
```

### 2. Variables de Entorno en Docker

Se agregaron las siguientes variables de entorno en el `Dockerfile`:

```dockerfile
# Configurar variables de entorno para Streamlit
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_HEADLESS=true
```

### 3. Actualización del Docker Compose

Se agregó la variable de entorno en `docker-compose.yml`:

```yaml
environment:
  # ... otras variables ...
  # Disable Streamlit telemetry to prevent capture() error
  STREAMLIT_BROWSER_GATHER_USAGE_STATS: false
```

### 4. Parámetros de Línea de Comandos

Se actualizó el comando de inicio en el `Dockerfile`:

```dockerfile
CMD ["streamlit", "run", "Inicio.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--browser.gatherUsageStats", "false"]
```

### 5. Actualización de Versión de Streamlit

Se especificó una versión mínima en `requirements.txt`:

```txt
streamlit>=1.28.0
```

## 🔧 Archivos Modificados

1. **Nuevo archivo**: `app/.streamlit/config.toml`
2. **Modificado**: `app/Dockerfile`
3. **Modificado**: `docker-compose.yml`
4. **Modificado**: `app/requirements.txt`

## 📋 Pasos para Aplicar la Solución

1. **Detener los servicios actuales**:

   ```bash
   docker compose down
   ```

2. **Reconstruir la imagen UI**:

   ```bash
   docker compose build ui --no-cache
   ```

3. **Iniciar los servicios**:

   ```bash
   docker compose up -d
   ```

4. **Verificar los logs**:

   ```bash
   docker logs anclora_rag-ui-1 --tail=20
   ```

## ✅ Verificación de la Solución

### Logs Esperados (Sin Error)

Después de aplicar la solución, los logs deberían mostrar:

```text
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8080
Network URL: http://172.x.x.x:8080
```

**Sin** el mensaje de error de telemetría.

### Pruebas de Funcionalidad

1. Acceder a `http://localhost:8080`
2. Verificar que la interfaz carga correctamente
3. Probar la funcionalidad de chat
4. Verificar que no hay bucles de reinicio en los logs

## 🔍 Explicación Técnica

### ¿Por qué ocurre este problema?

- Streamlit incluye un sistema de telemetría que recopila estadísticas de uso
- En versiones recientes, hubo cambios en la API interna de telemetría
- La función `capture()` cambió su signatura, causando incompatibilidades
- El error hace que Streamlit se reinicie constantemente

### ¿Cómo lo resuelve la solución?

- **Deshabilitación completa**: Se desactiva la telemetría por múltiples vías
- **Configuración redundante**: Se asegura que la configuración se aplique en todos los niveles
- **Modo headless**: Se ejecuta en modo servidor sin interfaz gráfica local
- **Versión específica**: Se asegura una versión compatible de Streamlit

## 🚨 Notas Importantes

1. **Privacidad**: Deshabilitar la telemetría mejora la privacidad
2. **Rendimiento**: Elimina la sobrecarga de recolección de estadísticas
3. **Estabilidad**: Previene errores relacionados con telemetría
4. **Compatibilidad**: Funciona con diferentes versiones de Streamlit

## 🔄 Rollback (Si es necesario)

Si la solución causa problemas, se puede revertir:

1. Eliminar el archivo `app/.streamlit/config.toml`
2. Revertir los cambios en `Dockerfile` y `docker-compose.yml`
3. Reconstruir y reiniciar los servicios

## 📞 Soporte Adicional

Si el problema persiste después de aplicar esta solución:

1. Verificar la versión de Docker y Docker Compose
2. Revisar los logs completos de todos los servicios
3. Comprobar la conectividad de red entre contenedores
4. Verificar los recursos disponibles del sistema
