# 🚀 Anclora RAG - Configuración de Automatizaciones N8N

## 📋 **WORKFLOWS INCLUIDOS**

### **1. Document Processing Pipeline** 
- **Archivo**: `document_processing_pipeline.json`
- **Función**: Automatiza todo el ciclo de procesamiento de documentos
- **Trigger**: Webhook cuando se sube un documento
- **Flujo**: Validación → Escáner → Extracción → Embeddings → Analytics

### **2. Smart Notification System**
- **Archivo**: `notification_system.json`
- **Función**: Sistema inteligente de notificaciones multicanal
- **Trigger**: Webhook para eventos del sistema
- **Canales**: Email, Slack, SMS (crítico)

### **3. Analytics & Reporting**
- **Archivo**: `analytics_reporting.json`
- **Función**: Generación automática de reportes y análisis
- **Trigger**: Cron jobs (diario/semanal/mensual)
- **Output**: Reportes HTML, emails, dashboard

### **4. System Monitoring & Alerts**
- **Archivo**: `monitoring_alerts.json`
- **Función**: Monitoreo continuo del sistema y alertas
- **Trigger**: Cron cada 5 minutos
- **Monitorea**: API, UI, Vector DB, recursos del sistema

---

## 🔧 **CONFIGURACIÓN INICIAL**

### **PASO 1: Importar Workflows**
```bash
# En tu N8N local (http://localhost:5678)
1. Ir a "Workflows" → "Import from file"
2. Seleccionar cada archivo .json
3. Importar uno por uno
4. Activar cada workflow después de configurar credenciales
```

### **PASO 2: Configurar Credenciales**

#### **🔑 Credenciales Requeridas**

##### **Anclora API (Custom)**
```json
{
  "name": "ancloraApi",
  "type": "httpHeaderAuth",
  "data": {
    "name": "Authorization",
    "value": "Bearer YOUR_ANCLORA_API_TOKEN"
  }
}
```

##### **SendGrid (Email)**
```json
{
  "name": "sendGridApi", 
  "type": "sendGridApi",
  "data": {
    "apiKey": "SG.YOUR_SENDGRID_API_KEY"
  }
}
```

##### **VirusTotal (Malware Scanner)**
```json
{
  "name": "virusTotalApi",
  "type": "httpHeaderAuth", 
  "data": {
    "name": "apikey",
    "value": "YOUR_VIRUSTOTAL_API_KEY"
  }
}
```

##### **Twilio (SMS - Opcional)**
```json
{
  "name": "twilioApi",
  "type": "twilioApi",
  "data": {
    "accountSid": "YOUR_TWILIO_ACCOUNT_SID",
    "authToken": "YOUR_TWILIO_AUTH_TOKEN",
    "phoneNumber": "+1234567890"
  }
}
```

---

## 🌐 **CONFIGURACIÓN DE WEBHOOKS**

### **URLs de Webhooks Generadas**
```
Document Processing: http://localhost:5678/webhook/process-document
Notifications: http://localhost:5678/webhook/send-notification
```

### **Integración con Anclora RAG**
```python
# En tu código Python, agregar llamadas a webhooks
import requests

# Después de subir documento
def trigger_document_processing(file_data, user_id):
    webhook_url = "http://localhost:5678/webhook/process-document"
    payload = {
        "file": file_data,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat()
    }
    response = requests.post(webhook_url, json=payload)
    return response.json()

# Para enviar notificaciones
def send_notification(notification_type, user_data, message):
    webhook_url = "http://localhost:5678/webhook/send-notification"
    payload = {
        "notification_type": notification_type,
        "user_email": user_data["email"],
        "user_name": user_data["name"],
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    response = requests.post(webhook_url, json=payload)
    return response.json()
```

---

## 📊 **CONFIGURACIÓN DE CRON JOBS**

### **Horarios Configurados**
```
Analytics Diario: 08:00 AM (0 8 * * *)
Reporte Semanal: Lunes 09:00 AM (0 9 * * 1)  
Reporte Mensual: Día 1 10:00 AM (0 10 1 * *)
Health Check: Cada 5 minutos (*/5 * * * *)
```

### **Personalizar Horarios**
```javascript
// En N8N, editar el nodo Cron
// Formato: minuto hora día mes día_semana
"0 8 * * *"     // Diario a las 8:00 AM
"0 9 * * 1"     // Lunes a las 9:00 AM  
"*/15 * * * *"  // Cada 15 minutos
"0 */6 * * *"   // Cada 6 horas
```

---

## 🔒 **CONFIGURACIÓN DE SEGURIDAD**

### **Variables de Entorno**
```bash
# Crear archivo .env en directorio N8N
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_secure_password

# URLs permitidas para webhooks
WEBHOOK_URL=http://localhost:5678
N8N_PAYLOAD_SIZE_MAX=16777216

# Configuración de base de datos (opcional)
DB_TYPE=sqlite
DB_SQLITE_DATABASE=database.sqlite
```

### **Firewall y Acceso**
```bash
# Solo permitir acceso local inicialmente
# Configurar reverse proxy con nginx si necesitas acceso externo
```

---

## 🧪 **TESTING DE WORKFLOWS**

### **Test Document Processing**
```bash
curl -X POST http://localhost:5678/webhook/process-document \
  -H "Content-Type: application/json" \
  -d '{
    "file": {
      "name": "test.pdf",
      "size": 1024000,
      "mimetype": "application/pdf"
    },
    "user_id": "test_user_123"
  }'
```

### **Test Notifications**
```bash
curl -X POST http://localhost:5678/webhook/send-notification \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "document_processed",
    "user_email": "test@anclora.com",
    "user_name": "Test User",
    "message": "Documento procesado exitosamente"
  }'
```

---

## 📈 **MONITOREO Y LOGS**

### **Ver Logs de Ejecución**
```
1. N8N Interface → Executions
2. Filtrar por workflow
3. Ver detalles de cada ejecución
4. Revisar errores y tiempos de respuesta
```

### **Métricas Importantes**
- **Tasa de éxito** de procesamiento de documentos
- **Tiempo promedio** de ejecución por workflow
- **Errores** y reintentos automáticos
- **Uso de recursos** del servidor N8N

---

## 🚀 **PRÓXIMOS PASOS**

### **Optimizaciones Recomendadas**
1. **Configurar retry policies** para llamadas API fallidas
2. **Implementar rate limiting** para evitar spam
3. **Agregar más canales** de notificación (Discord, Teams)
4. **Crear workflows** para backup automático
5. **Implementar A/B testing** para optimizar flujos

### **Escalabilidad**
- **N8N Cloud**: Migrar cuando necesites más recursos
- **Queue system**: Implementar Redis para trabajos pesados  
- **Load balancing**: Distribuir carga entre múltiples instancias
- **Database**: Migrar de SQLite a PostgreSQL para producción

---

## 🆘 **TROUBLESHOOTING**

### **Problemas Comunes**
```
❌ Webhook no responde
✅ Verificar que N8N esté ejecutándose en puerto 5678
✅ Comprobar firewall y permisos de red

❌ Credenciales inválidas  
✅ Regenerar API keys en servicios externos
✅ Verificar formato de credenciales en N8N

❌ Workflow no se ejecuta
✅ Verificar que esté activado (toggle verde)
✅ Revisar logs de ejecución para errores
✅ Comprobar sintaxis de cron expressions
```

### **Logs Útiles**
```bash
# Ver logs de N8N
docker logs n8n_container_name -f

# Verificar conectividad
curl -I http://localhost:5678/healthz
```

---

**🎯 ¡Con estas automatizaciones, Anclora RAG tendrá un sistema robusto y completamente automatizado!**
