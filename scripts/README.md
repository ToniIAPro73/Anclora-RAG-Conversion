# Anclora RAG - Model Management Scripts

Este directorio contiene scripts para asegurar la disponibilidad y persistencia de los modelos de Ollama en el sistema Anclora RAG.

## 🛡️ Scripts de Prevención

### 1. `ensure-models.ps1` / `ensure-models.sh`
**Propósito**: Verifica y descarga automáticamente los modelos requeridos si no están disponibles.

**Uso**:
```powershell
# PowerShell (Windows)
.\ensure-models.ps1

# Bash (Linux/macOS)
./ensure-models.sh
```

**Características**:
- ✅ Verifica disponibilidad de modelos requeridos
- ✅ Descarga automática de modelos faltantes
- ✅ Reintentos automáticos con backoff
- ✅ Logging detallado

### 2. `monitor-models.ps1`
**Propósito**: Monitoreo continuo de la disponibilidad de modelos.

**Uso**:
```powershell
# Monitoreo básico (cada 5 minutos)
.\monitor-models.ps1

# Monitoreo personalizado
.\monitor-models.ps1 -CheckInterval 180 -SendAlerts
```

**Características**:
- 🔄 Monitoreo continuo configurable
- 📧 Sistema de alertas (configurable)
- 📝 Logging automático
- 🔧 Auto-reparación de modelos faltantes

### 3. `setup-scheduled-task.ps1`
**Propósito**: Configura una tarea programada de Windows para verificación automática.

**Uso** (requiere permisos de administrador):
```powershell
# Ejecutar como Administrador
.\setup-scheduled-task.ps1
```

**Características**:
- ⏰ Ejecución automática al inicio del sistema
- 🔄 Verificaciones cada 30 minutos
- 📝 Logging automático
- 🛠️ Configuración automática de Windows Task Scheduler

## 💾 Scripts de Backup

### 4. `backup-models.ps1`
**Propósito**: Crea backups de los modelos de Ollama para prevenir pérdida de datos.

**Uso**:
```powershell
# Backup básico
.\backup-models.ps1

# Backup personalizado
.\backup-models.ps1 -BackupPath "D:\Backups\Models" -Compress -RetainDays 60
```

**Características**:
- 💾 Backup completo de modelos
- 🗜️ Compresión opcional
- 🧹 Limpieza automática de backups antiguos
- 📊 Reporte de tamaño y estado

## 🚀 Configuración Recomendada

### Configuración Inicial (Una vez)

1. **Configurar tarea programada** (como Administrador):
```powershell
.\setup-scheduled-task.ps1
```

2. **Crear backup inicial**:
```powershell
.\backup-models.ps1
```

3. **Verificar que todo funciona**:
```powershell
.\ensure-models.ps1
```

### Configuración de Monitoreo Continuo (Opcional)

Para monitoreo 24/7, ejecutar en una ventana de PowerShell dedicada:
```powershell
.\monitor-models.ps1 -CheckInterval 300 -SendAlerts
```

## 📋 Mejoras Implementadas en Docker Compose

El archivo `docker-compose.yml` ha sido mejorado con:

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "ollama list | grep -q llama3 || (ollama pull llama3 && ollama list | grep -q llama3)"]
  interval: 60s
  timeout: 300s
  retries: 3
  start_period: 120s
```

**Beneficios**:
- ✅ Verificación automática de modelos en el healthcheck
- ✅ Descarga automática si el modelo no está disponible
- ✅ Timeouts más largos para permitir descargas
- ✅ Integración nativa con Docker Compose

## 🔧 Solución de Problemas

### Problema: "Modelo no encontrado"
**Solución**:
```powershell
.\ensure-models.ps1
```

### Problema: "Container no responde"
**Solución**:
```powershell
docker restart anclora_rag-ollama-1
Start-Sleep 30
.\ensure-models.ps1
```

### Problema: "Espacio insuficiente"
**Solución**:
```powershell
# Limpiar modelos no utilizados
docker exec anclora_rag-ollama-1 ollama rm <modelo-no-usado>

# Crear backup antes de limpiar
.\backup-models.ps1
```

## 📊 Logs y Monitoreo

### Ubicaciones de Logs
- **Tarea programada**: `../logs/model-check.log`
- **Monitor continuo**: `model-monitor.log`
- **Docker logs**: `docker logs anclora_rag-ollama-1`

### Comandos Útiles de Monitoreo
```powershell
# Ver modelos disponibles
docker exec anclora_rag-ollama-1 ollama list

# Ver logs del contenedor
docker logs anclora_rag-ollama-1 --tail 50

# Ver estado del volumen
docker volume inspect anclora_rag_ollama_models

# Ver uso de espacio
docker exec anclora_rag-ollama-1 du -sh /root/.ollama/models
```

## 🎯 Estrategia de Prevención Completa

1. **Persistencia**: Volumen Docker configurado ✅
2. **Healthcheck mejorado**: Verificación y descarga automática ✅
3. **Tarea programada**: Verificaciones regulares ✅
4. **Monitoreo continuo**: Opcional para entornos críticos ✅
5. **Backups regulares**: Prevención de pérdida de datos ✅
6. **Scripts de recuperación**: Restauración rápida ✅

Con esta configuración, la pérdida de modelos debería ser prácticamente imposible.