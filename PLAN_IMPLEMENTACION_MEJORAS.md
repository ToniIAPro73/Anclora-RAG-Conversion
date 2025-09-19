# Plan de Implementación de Mejoras - Anclora RAG

## 🎯 Objetivo
Implementar las mejoras identificadas en el análisis del repositorio Anclora RAG, priorizando por criticidad y impacto en la funcionalidad del sistema.

---

## 📊 Matriz de Priorización

| Mejora | Criticidad | Impacto | Esfuerzo | Prioridad |
|--------|------------|---------|----------|-----------|
| Corregir conflicto de nombres | CRÍTICA | ALTO | BAJO | 1 |
| Mejorar gestión de errores | ALTA | ALTO | MEDIO | 2 |
| Corregir títulos inconsistentes | MEDIA | BAJO | BAJO | 3 |
| Implementar validación entrada | ALTA | ALTO | MEDIO | 4 |
| Configuración Docker | MEDIA | MEDIO | BAJO | 5 |
| Implementar logging | MEDIA | MEDIO | MEDIO | 6 |
| Mejorar UI/UX | BAJA | MEDIO | ALTO | 7 |
| Sistema autenticación | BAJA | ALTO | ALTO | 8 |

---

## 🚀 FASE 1: Correcciones Críticas (Semana 1)

### 1.1 Corregir Conflicto de Nombres ⚠️ CRÍTICO
**Tiempo estimado**: 30 minutos
**Responsable**: Desarrollador Senior
**Archivos**: `app/Inicio.py`

#### Pasos:
1. **Identificar el problema**:
   ```python
   # Línea 50 - PROBLEMA
   response = response(user_input)  # Sobrescribe la función
   ```

2. **Implementar la corrección**:
   ```python
   # SOLUCIÓN
   assistant_response = response(user_input)
   ```

3. **Actualizar referencias**:
   ```python
   # Líneas 52-55
   with st.chat_message("assistant"):
       st.markdown(assistant_response)
   st.session_state.messages.append({"role": "assistant", "content": assistant_response})
   ```

4. **Testing**:
   - Probar múltiples mensajes consecutivos
   - Verificar que el historial funciona correctamente
   - Confirmar que no hay errores en consola

#### Criterios de Aceptación:
- ✅ El chat funciona después del primer mensaje
- ✅ El historial se mantiene correctamente
- ✅ No hay errores en logs

### 1.2 Mejorar Gestión de Errores
**Tiempo estimado**: 4 horas
**Responsable**: Desarrollador Senior

#### Pasos:

1. **Implementar manejo de errores en langchain_module.py**:
   ```python
   def response(query: str) -> str:
       try:
           # Código existente
           return rag_chain.invoke(query)
       except Exception as e:
           logger.error(f"Error en respuesta RAG: {str(e)}")
           return "Lo siento, ocurrió un error al procesar tu consulta. Por favor, intenta nuevamente."
   ```

2. **Mejorar manejo de errores en ingest_file.py**:
   ```python
   def ingest_file(uploaded_file, file_name):
       try:
           # Código existente
       except Exception as e:
           st.error(f"Error al procesar archivo: {str(e)}")
           logger.error(f"Error en ingest_file: {str(e)}")
   ```

3. **Implementar logging estructurado**:
   ```python
   import logging
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   logger = logging.getLogger(__name__)
   ```

#### Criterios de Aceptación:
- ✅ Errores capturados y loggeados
- ✅ Mensajes de error informativos para usuarios
- ✅ Sistema no se cuelga ante errores

### 1.3 Implementar Validación de Entrada
**Tiempo estimado**: 3 horas
**Responsable**: Desarrollador

#### Pasos:

1. **Validar entrada de chat**:
   ```python
   def validate_user_input(user_input: str) -> bool:
       if not user_input or len(user_input.strip()) == 0:
           return False
       if len(user_input) > 1000:  # Límite de caracteres
           return False
       return True
   ```

2. **Validar archivos subidos**:
   ```python
   def validate_uploaded_file(uploaded_file) -> tuple[bool, str]:
       MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
       
       if uploaded_file.size > MAX_FILE_SIZE:
           return False, "Archivo demasiado grande (máximo 10MB)"
       
       allowed_extensions = ['.csv', '.doc', '.docx', '.pdf', '.txt']
       file_ext = os.path.splitext(uploaded_file.name)[1].lower()
       
       if file_ext not in allowed_extensions:
           return False, f"Tipo de archivo no soportado: {file_ext}"
       
       return True, "Válido"
   ```

3. **Implementar sanitización**:
   ```python
   import html
   
   def sanitize_input(user_input: str) -> str:
       return html.escape(user_input.strip())
   ```

#### Criterios de Aceptación:
- ✅ Inputs validados antes de procesamiento
- ✅ Mensajes claros para inputs inválidos
- ✅ Archivos validados por tamaño y tipo

---

## 🔧 FASE 2: Mejoras de Estabilidad (Semana 2)

### 2.1 Corregir Títulos Inconsistentes
**Tiempo estimado**: 15 minutos
**Responsable**: Desarrollador Junior

#### Pasos:
1. **Actualizar app/pages/Archivos.py línea 4**:
   ```python
   # Cambiar de:
   page_title='Archivos - Basdonax AI RAG'
   # A:
   page_title='Archivos - Anclora AI RAG'
   ```

2. **Verificar consistencia en otros archivos**
3. **Actualizar README si es necesario**

### 2.2 Mejorar Configuración Docker
**Tiempo estimado**: 2 horas
**Responsable**: DevOps Engineer

#### Pasos:

1. **Agregar configuración de red al servicio UI**:
   ```yaml
   ui:
     build: ./app
     ports:
       - 8080:8080
     networks:
       - net  # Agregar esta línea
     volumes:
       - ./app:/app
   ```

2. **Optimizar Dockerfile**:
   ```dockerfile
   FROM python:3.11-slim  # Usar imagen más ligera
   
   WORKDIR /app
   
   # Copiar requirements primero para mejor cache
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 8080
   CMD ["streamlit", "run", "Inicio.py", "--server.port", "8080", "--server.address", "0.0.0.0"]
   ```

3. **Agregar healthchecks**:
   ```yaml
   ui:
     # ... configuración existente
     healthcheck:
       test: ["CMD", "curl", "-f", "http://localhost:8080"]
       interval: 30s
       timeout: 10s
       retries: 3
   ```

### 2.3 Implementar Sistema de Logging
**Tiempo estimado**: 3 horas
**Responsable**: Desarrollador Senior

#### Pasos:

1. **Crear módulo de logging**:
   ```python
   # app/common/logger.py
   import logging
   import sys
   from datetime import datetime
   
   def setup_logger(name: str) -> logging.Logger:
       logger = logging.getLogger(name)
       logger.setLevel(logging.INFO)
       
       handler = logging.StreamHandler(sys.stdout)
       formatter = logging.Formatter(
           '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
       )
       handler.setFormatter(formatter)
       logger.addHandler(handler)
       
       return logger
   ```

2. **Integrar logging en módulos principales**
3. **Configurar rotación de logs**

---

## 🎨 FASE 3: Mejoras de UX (Semana 3-4)

### 3.1 Mejorar Interfaz de Usuario
**Tiempo estimado**: 8 horas
**Responsable**: Frontend Developer

#### Pasos:

1. **Implementar indicadores de progreso**:
   ```python
   with st.spinner('Procesando tu consulta...'):
       response = get_response(user_input)
   ```

2. **Mejorar feedback visual**:
   ```python
   # Mostrar estado de procesamiento de archivos
   progress_bar = st.progress(0)
   status_text = st.empty()
   
   for i, chunk in enumerate(process_file_chunks(file)):
       progress_bar.progress((i + 1) / total_chunks)
       status_text.text(f'Procesando chunk {i+1}/{total_chunks}')
   ```

3. **Implementar confirmaciones**:
   ```python
   if st.button('Eliminar archivo'):
       if st.confirm('¿Estás seguro de eliminar este archivo?'):
           delete_file(filename)
   ```

### 3.2 Optimizar Performance
**Tiempo estimado**: 6 horas
**Responsable**: Desarrollador Senior

#### Pasos:

1. **Implementar caché de embeddings**:
   ```python
   @st.cache_data
   def get_embeddings(text: str):
       return embeddings_model.embed_query(text)
   ```

2. **Optimizar consultas a ChromaDB**:
   ```python
   # Implementar paginación
   # Optimizar filtros
   # Usar índices apropiados
   ```

3. **Implementar lazy loading**

---

## 🔐 FASE 4: Seguridad y Escalabilidad (Semana 5-6)

### 4.1 Implementar Autenticación Básica
**Tiempo estimado**: 12 horas
**Responsable**: Desarrollador Senior

#### Pasos:

1. **Crear sistema de login simple**:
   ```python
   # app/auth.py
   import streamlit_authenticator as stauth
   
   def setup_authentication():
       names = ['Admin', 'User']
       usernames = ['admin', 'user']
       passwords = ['admin123', 'user123']  # En producción usar hash
       
       hashed_passwords = stauth.Hasher(passwords).generate()
       
       authenticator = stauth.Authenticate(
           names, usernames, hashed_passwords,
           'anclora_rag', 'auth_key', cookie_expiry_days=30
       )
       
       return authenticator
   ```

2. **Integrar en páginas principales**
3. **Implementar gestión de sesiones**

### 4.2 Implementar API REST
**Tiempo estimado**: 16 horas
**Responsable**: Backend Developer

#### Pasos:

1. **Crear endpoints FastAPI**:
   ```python
   # app/api.py
   from fastapi import FastAPI, UploadFile, File
   
   app = FastAPI()
   
   @app.post("/chat")
   async def chat_endpoint(message: str):
       response = get_rag_response(message)
       return {"response": response}
   
   @app.post("/upload")
   async def upload_file(file: UploadFile = File(...)):
       result = process_uploaded_file(file)
       return {"status": "success", "message": result}
   ```

2. **Documentar API con Swagger**
3. **Implementar rate limiting**

---

## 📋 Checklist de Implementación

### Pre-implementación
- [ ] Backup del código actual
- [ ] Configurar entorno de desarrollo
- [ ] Preparar entorno de testing
- [ ] Definir criterios de aceptación

### Durante implementación
- [ ] Seguir orden de prioridades
- [ ] Documentar cambios realizados
- [ ] Realizar testing continuo
- [ ] Mantener comunicación con stakeholders

### Post-implementación
- [ ] Testing integral del sistema
- [ ] Documentación actualizada
- [ ] Deployment en ambiente de producción
- [ ] Monitoreo de métricas

---

## 🎯 Métricas de Éxito

### Técnicas
- **Tiempo de respuesta**: < 3 segundos (actual: ~5-8 segundos)
- **Uptime**: > 99% (actual: ~95%)
- **Errores**: < 1% de consultas (actual: ~5%)

### Funcionales
- **Chat funcional**: 100% de mensajes procesados
- **Carga de archivos**: 100% de archivos válidos procesados
- **Satisfacción usuario**: > 4/5 en encuestas

---

## 📅 Timeline Resumido

| Semana | Fase | Entregables |
|--------|------|-------------|
| 1 | Correcciones Críticas | Chat funcional, Gestión errores |
| 2 | Mejoras Estabilidad | Docker optimizado, Logging |
| 3-4 | Mejoras UX | UI mejorada, Performance |
| 5-6 | Seguridad | Autenticación, API |

**Duración total estimada**: 6 semanas
**Esfuerzo total**: ~80 horas de desarrollo

---

## 🚨 Riesgos y Mitigaciones

### Riesgos Identificados
1. **Dependencias externas**: Ollama, ChromaDB pueden fallar
2. **Compatibilidad**: Cambios pueden romper funcionalidad existente
3. **Performance**: Mejoras pueden impactar rendimiento

### Mitigaciones
1. **Testing exhaustivo** en cada fase
2. **Rollback plan** preparado
3. **Monitoreo continuo** de métricas
4. **Comunicación proactiva** con usuarios

---

*Plan creado el: 2025-01-19*
*Versión: 1.0*
*Próxima revisión: Semanal durante implementación*
