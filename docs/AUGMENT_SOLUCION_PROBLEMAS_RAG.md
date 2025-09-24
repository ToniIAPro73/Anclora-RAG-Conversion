# Solución de Problemas - Anclora RAG

> **Nota de idioma:** Las interfaces y respuestas están certificadas en español e inglés. Si utilizas otro idioma podrías recibir mensajes mixtos mientras se completa la localización.

### Roadmap de soporte lingüístico

1. **Portugués**: validación en curso para interfaz y respuestas automáticas.
2. **Francés y Alemán**: se incorporarán tras cerrar la fase de pruebas de portugués.
3. **Otros idiomas**: se priorizarán según demanda y siempre junto con documentación y pruebas específicas.

## 🚨 Problema: "El RAG no responde a 'Hola'"

### ✅ **SOLUCIÓN IMPLEMENTADA**

He identificado y corregido el problema principal. El sistema ahora debería responder correctamente a saludos básicos.

---

## 🔍 Diagnóstico Rápido

### **Ejecutar Script de Diagnóstico**
```bash
python diagnostico_rag.py
```

Este script verificará automáticamente:
- ✅ Servicios Docker
- ✅ Interfaz Streamlit (puerto 8501)
- ✅ ChromaDB (puerto 8000)
- ✅ Ollama y modelos LLM
- ✅ Documentos en la base de conocimiento

Para comprobar la API expuesta en FastAPI puedes ejecutar manualmente:

```bash
curl http://localhost:8081/health
```

---

## 🛠️ Problemas Comunes y Soluciones

### **1. El chat no responde a "Hola"**

#### ✅ **YA CORREGIDO** - Cambios implementados:

**Problema**: El sistema solo funcionaba con contexto específico de documentos.

**Solución aplicada**:
- Mejorado el prompt para manejar saludos básicos
- Agregada detección de saludos simples
- Implementada respuesta automática para casos sin contexto

**Resultado**: Ahora cuando escribas "Hola", recibirás:
> "¡Hola! Soy Bastet, tu asistente virtual de PBC. Estoy aquí para ayudarte con información sobre nuestros proyectos, productos y servicios. ¿En qué puedo asistirte hoy?"

### **2. No hay documentos en la base de conocimiento**

#### **Síntomas**:
- El RAG responde: "No tengo documentos en mi base de conocimiento"
- Las consultas específicas no obtienen respuestas relevantes

#### **Solución**:
```bash
# 1. Verificar estado
python diagnostico_rag.py

# 2. Ir a la interfaz web
# http://localhost:8080

# 3. Hacer clic en "Archivos" (barra lateral)

# 4. Subir un documento de prueba
# - Formatos: PDF, DOC, DOCX, TXT, MD, etc.
# - Tamaño máximo: 10MB
```

#### **Documentos de prueba recomendados**:
Crea un archivo `info_pbc.txt` con contenido básico:
```text
PBC es una consultora de Ingeniería de Software e Inteligencia Artificial.

Productos principales:
1. Cubo de Datos - Centraliza información de Business Intelligence
2. AVI - Asistente Virtual Inteligente para atención al cliente
3. Plataforma Business Intelligence PBC - Democratiza insights empresariales

Servicios:
- Desarrollo de software
- Implementación de IA
- Consultoría en transformación digital
- Análisis de datos
```

### **3. Servicios Docker no están corriendo**

#### **Verificar estado**:
```bash
docker-compose ps
```

#### **Si no están corriendo**:
```bash
# Detener todo
docker-compose down

# Reconstruir (si hay cambios)
docker-compose build --no-cache

# Iniciar servicios
docker-compose up -d

# Verificar logs
docker-compose logs -f ui
```

### **4. Modelo LLM no está descargado**

#### **Síntomas**:
- Error: "model not found"
- Ollama no responde

#### **Solución**:
```bash
# 1. Ver contenedores corriendo
docker ps

# 2. Copiar CONTAINER ID de ollama/ollama:latest

# 3. Descargar modelo (para GPU - Llama3)
docker exec [CONTAINER_ID] ollama pull llama3

# O para CPU (Phi3)
docker exec [CONTAINER_ID] ollama pull phi3

# 4. Verificar modelos instalados
docker exec [CONTAINER_ID] ollama list
```

### **5. ChromaDB no accesible**

#### **Verificar**:
```bash
curl http://localhost:8000/api/v1/heartbeat
```

#### **Si falla**:
```bash
# Ver logs de ChromaDB
docker-compose logs chroma

# Reiniciar solo ChromaDB
docker-compose restart chroma

# Verificar puerto
netstat -an | grep 8000
```

### **6. Streamlit no carga**

#### **Verificar**:
```bash
curl http://localhost:8501
```

#### **Si falla**:
```bash
# Ver logs detallados
docker-compose logs ui

# Reiniciar UI
docker-compose restart ui

# Verificar puerto
netstat -an | grep 8501
```

---

## 🔧 Comandos de Mantenimiento

### **Reinicio Completo**
```bash
# Parar todo
docker-compose down

# Limpiar volúmenes (CUIDADO: borra datos)
docker-compose down -v

# Reconstruir desde cero
docker-compose build --no-cache

# Iniciar
docker-compose up -d
```

### **Ver Logs en Tiempo Real**
```bash
# Todos los servicios
docker-compose logs -f

# Solo UI
docker-compose logs -f ui

# Solo ChromaDB
docker-compose logs -f chroma

# Solo Ollama
docker-compose logs -f ollama
```

### **Verificar Recursos**
```bash
# Uso de recursos
docker stats

# Espacio en disco
docker system df

# Limpiar recursos no utilizados
docker system prune
```

---

## 📋 Checklist de Verificación

### **Antes de reportar un problema**:

- [ ] ✅ Servicios Docker corriendo (`docker-compose ps`)
- [ ] ✅ Streamlit accesible (http://localhost:8080)
- [ ] ✅ ChromaDB accesible (http://localhost:8000/api/v1/heartbeat)
- [ ] ✅ Modelo LLM descargado (`docker exec [ID] ollama list`)
- [ ] ✅ Al menos un documento subido
- [ ] ✅ Logs sin errores críticos (`docker-compose logs`)

### **Pruebas básicas**:

1. **Saludo simple**: Escribir "Hola" → Debe responder Bastet
2. **Consulta general**: "¿Qué es PBC?" → Debe usar contexto o info básica
3. **Subir archivo**: Probar subir un TXT pequeño
4. **Consulta específica**: Preguntar sobre el contenido subido

---

## 🚀 Pasos para Resolver "Hola" No Responde

### **Paso 1: Aplicar correcciones**
```bash
# Las correcciones ya están implementadas en el código
# Solo necesitas reconstruir:

docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### **Paso 2: Verificar funcionamiento**
```bash
# Ejecutar diagnóstico
python diagnostico_rag.py

# O verificar manualmente:
# 1. Ir a http://localhost:8501
# 2. Escribir "Hola"
# 3. Debe responder: "¡Hola! Soy Bastet..."
```

### **Paso 3: Si aún no funciona**
```bash
# Ver logs específicos
docker-compose logs ui | grep -i error

# Verificar modelo LLM
docker ps
docker exec [OLLAMA_CONTAINER_ID] ollama list

# Probar conexión directa a Ollama
curl http://localhost:11434/api/tags
```

---

## 📞 Escalación de Problemas

### **Si el problema persiste**:

1. **Recopilar información**:
   ```bash
   # Ejecutar diagnóstico completo
   python diagnostico_rag.py > diagnostico_resultado.txt
   
   # Capturar logs
   docker-compose logs > logs_completos.txt
   
   # Estado de servicios
   docker-compose ps > estado_servicios.txt
   ```

2. **Información del sistema**:
   - Sistema operativo
   - Versión de Docker
   - Recursos disponibles (RAM, CPU)
   - Configuración utilizada (GPU/CPU)

3. **Pasos ya intentados**:
   - Lista de comandos ejecutados
   - Errores específicos observados
   - Cambios realizados

---

## ✅ Estado Actual

**Correcciones implementadas**:
- ✅ Manejo de saludos básicos
- ✅ Detección de base de conocimiento vacía
- ✅ Mensajes informativos mejorados
- ✅ Logging detallado
- ✅ Script de diagnóstico automático

**El sistema ahora debería**:
- ✅ Responder a "Hola" correctamente
- ✅ Informar cuando no hay documentos
- ✅ Proporcionar ayuda contextual
- ✅ Manejar errores graciosamente

---

*Documento actualizado: 2025-01-19*
*Versión: 1.1*
*Estado: Problemas críticos resueltos*
