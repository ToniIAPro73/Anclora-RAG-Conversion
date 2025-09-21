# Guía de Acceso para Agentes IA - Anclora RAG

## 🤖 Cómo Acceder al Sistema RAG desde Agentes IA

Esta guía explica las diferentes formas en que un agente de inteligencia artificial puede acceder e interactuar con el sistema Anclora RAG.

> **Nota de idioma:** Las respuestas de la API y los mensajes del asistente están validadas actualmente para español e inglés. Otros idiomas siguen en desarrollo y pueden presentar inconsistencias.

### Idiomas soportados y roadmap

- **Disponibles hoy:** Español (predeterminado) e Inglés.
- **En preparación:** Portugués (siguiente iteración), seguido por Francés y Alemán tras la fase de validación.
- **Evaluación continua:** Se priorizarán nuevos idiomas según la demanda, documentando prompts y casos de prueba específicos antes de habilitarlos en la API.

---

## 🚀 Opciones de Acceso

### 1. **API REST (Recomendado)**

#### Configuración Inicial
```bash
# Iniciar el sistema con API
docker-compose up -d

# Verificar que la API esté funcionando
curl http://localhost:8081/health
```

#### Endpoints Disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Estado del sistema |
| POST | `/chat` | Consulta al RAG |
| POST | `/upload` | Subir documentos |
| GET | `/documents` | Listar documentos |
| DELETE | `/documents/{filename}` | Eliminar documento |

#### Autenticación
```bash
# Todas las requests requieren header de autorización
Authorization: Bearer your-api-key-here
```

#### Ejemplos de Uso

**Consulta al RAG:**
```bash
curl -X POST "http://localhost:8081/chat" \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cuáles son los productos de PBC?",
    "max_length": 1000
  }'
```

**Subir documento:**
```bash
curl -X POST "http://localhost:8081/upload" \
  -H "Authorization: Bearer your-api-key-here" \
  -F "file=@documento.pdf"
```

**Listar documentos:**
```bash
curl -X GET "http://localhost:8081/documents" \
  -H "Authorization: Bearer your-api-key-here"
```

### 2. **Cliente Python**

#### Instalación
```bash
pip install requests
```

#### Uso Básico
```python
from anclora_rag_client import AIAgentRAGInterface

# Crear interfaz
ai_rag = AIAgentRAGInterface(
    rag_url="http://localhost:8081",
    api_key="your-api-key-here"
)

# Verificar disponibilidad
if ai_rag.is_healthy():
    # Hacer consulta
    response = ai_rag.ask_question("¿Qué servicios ofrece PBC?")
    print(response)
    
    # Agregar conocimiento
    success = ai_rag.add_knowledge("nuevo_documento.pdf")
    if success:
        print("Documento agregado exitosamente")
```

#### Uso Avanzado
```python
from anclora_rag_client import AncloraRAGClient

# Cliente completo
client = AncloraRAGClient("http://localhost:8081", "your-api-key-here")

# Consulta con parámetros
result = client.query(
    message="Explica el Cubo de Datos de PBC",
    max_length=500
)

# Consultas en lote
messages = [
    "¿Qué es AVI?",
    "¿Cómo funciona la Plataforma BI?",
    "¿Cuáles son los beneficios del Cubo de Datos?"
]
responses = client.batch_query(messages)
```

---

## 🔧 Integración con Diferentes Tipos de Agentes

### 1. **Agentes LangChain**

```python
from langchain.tools import Tool
from anclora_rag_client import AIAgentRAGInterface

# Crear herramienta RAG para LangChain
rag_interface = AIAgentRAGInterface()

def rag_query_tool(query: str) -> str:
    """Consultar base de conocimiento RAG"""
    return rag_interface.ask_question(query)

# Definir herramienta
rag_tool = Tool(
    name="RAG_Knowledge_Base",
    description="Consulta la base de conocimiento de PBC para información sobre productos y servicios",
    func=rag_query_tool
)

# Usar en agente LangChain
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI

llm = OpenAI(temperature=0)
agent = initialize_agent(
    tools=[rag_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

# Ejecutar consulta
response = agent.run("¿Qué productos ofrece PBC y cómo pueden ayudar a mi empresa?")
```

### 2. **Agentes CrewAI**

```python
from crewai import Agent, Task, Crew
from anclora_rag_client import AIAgentRAGInterface

# Configurar RAG
rag = AIAgentRAGInterface()

# Crear agente especializado
knowledge_agent = Agent(
    role='Especialista en Conocimiento PBC',
    goal='Proporcionar información precisa sobre productos y servicios de PBC',
    backstory='Soy un experto en los productos de PBC con acceso a toda la documentación.',
    tools=[],  # Agregar herramientas RAG aquí
    verbose=True
)

# Crear tarea
research_task = Task(
    description='Investigar información sobre {topic} en la base de conocimiento',
    agent=knowledge_agent
)

# Ejecutar crew
crew = Crew(
    agents=[knowledge_agent],
    tasks=[research_task],
    verbose=True
)

result = crew.kickoff(inputs={'topic': 'Cubo de Datos'})
```

### 3. **Agentes AutoGen**

```python
import autogen
from anclora_rag_client import AIAgentRAGInterface

# Configurar RAG
rag = AIAgentRAGInterface()

# Función para consultas RAG
def query_rag(message):
    return rag.ask_question(message)

# Configurar agente
config_list = [
    {
        'model': 'gpt-4',
        'api_key': 'your-openai-key'
    }
]

# Crear agente con acceso a RAG
assistant = autogen.AssistantAgent(
    name="rag_assistant",
    llm_config={"config_list": config_list},
    system_message="Eres un asistente con acceso a la base de conocimiento de PBC. Usa la función query_rag para obtener información específica."
)

# Registrar función RAG
assistant.register_function(
    function_map={"query_rag": query_rag}
)
```

---

## 🔐 Configuración de Seguridad

### 1. **Autenticación por API Key**

```python
# Configurar en variables de entorno
import os
os.environ['ANCLORA_RAG_API_KEY'] = 'your-secure-api-key'

# Usar en cliente
api_key = os.getenv('ANCLORA_RAG_API_KEY')
rag = AIAgentRAGInterface(api_key=api_key)
```

### 2. **Rate Limiting**

```python
# El sistema incluye rate limiting automático
# Máximo 100 requests por minuto por API key
```

### 3. **Validación de Entrada**

```python
# Todas las entradas son validadas automáticamente:
# - Longitud máxima de mensaje: 1000 caracteres
# - Tamaño máximo de archivo: 10MB
# - Tipos de archivo permitidos: PDF, DOC, TXT, etc.
```

---

## 📊 Monitoreo y Logs

### 1. **Health Checks**

```python
# Verificar estado del sistema
health = rag.client.health_check()
print(f"Estado: {health['status']}")
print(f"Servicios: {health['services']}")
```

### 2. **Logs de Actividad**

```bash
# Ver logs de la API
docker-compose logs api

# Ver logs en tiempo real
docker-compose logs -f api
```

### 3. **Métricas de Uso**

```python
# El cliente incluye logging automático
import logging
logging.basicConfig(level=logging.INFO)

# Los logs incluyen:
# - Consultas realizadas
# - Documentos subidos
# - Errores y excepciones
# - Tiempos de respuesta
```

---

## 🚨 Manejo de Errores

### 1. **Errores Comunes**

```python
# Sistema no disponible
if not rag.is_healthy():
    print("Sistema RAG no disponible")
    # Implementar fallback o retry

# Error en consulta
response = rag.ask_question("pregunta")
if response.startswith("Error:"):
    print(f"Error en consulta: {response}")
    # Manejar error apropiadamente
```

### 2. **Retry Logic**

```python
import time
from typing import Optional

def query_with_retry(rag: AIAgentRAGInterface, question: str, max_retries: int = 3) -> Optional[str]:
    for attempt in range(max_retries):
        try:
            if rag.is_healthy():
                response = rag.ask_question(question)
                if not response.startswith("Error:"):
                    return response
        except Exception as e:
            print(f"Intento {attempt + 1} falló: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Backoff exponencial
    
    return None
```

---

## 📝 Ejemplos Completos

### Agente de Consultas Empresariales

```python
class BusinessQueryAgent:
    def __init__(self):
        self.rag = AIAgentRAGInterface()
    
    def analyze_business_need(self, company_description: str) -> str:
        """Analizar necesidades empresariales y recomendar productos PBC"""
        
        # Consultar información sobre productos
        products_info = self.rag.ask_question("¿Cuáles son todos los productos de PBC y sus beneficios?")
        
        # Consultar casos de uso
        use_cases = self.rag.ask_question("¿Qué casos de uso resuelve cada producto de PBC?")
        
        # Generar recomendación personalizada
        recommendation_query = f"""
        Basándose en esta descripción de empresa: {company_description}
        Y considerando los productos: {products_info}
        ¿Qué productos de PBC recomendarías y por qué?
        """
        
        recommendation = self.rag.ask_question(recommendation_query)
        
        return {
            "products": products_info,
            "use_cases": use_cases,
            "recommendation": recommendation
        }

# Uso
agent = BusinessQueryAgent()
result = agent.analyze_business_need("Empresa de retail con múltiples sucursales que necesita centralizar datos de ventas")
```

---

## 🔄 Actualización y Mantenimiento

### 1. **Actualizar Documentos**

```python
# Agregar nuevos documentos
rag.add_knowledge("nuevo_producto_2024.pdf")

# Verificar documentos disponibles
docs = rag.get_available_documents()
print(f"Documentos disponibles: {len(docs)}")
```

### 2. **Monitoreo Continuo**

```python
import schedule
import time

def monitor_rag_health():
    if not rag.is_healthy():
        # Enviar alerta
        print("⚠️ Sistema RAG no disponible")
        # Implementar notificación

# Monitorear cada 5 minutos
schedule.every(5).minutes.do(monitor_rag_health)

while True:
    schedule.run_pending()
    time.sleep(1)
```

---

*Guía creada el: 2025-01-19*
*Versión: 1.0*
*Compatible con: Anclora RAG v1.1+*
