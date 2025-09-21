# Ejemplos del cliente `AncloraRAGClient`

Estos fragmentos muestran cómo configurar el cliente Python para conectarse a un despliegue de Anclora RAG.

## Inicialización y verificación de salud

```python
from anclora_rag_client import AncloraRAGClient

client = AncloraRAGClient(
    base_url="http://localhost:8081",
    api_key="mi-token-super-seguro",
)

salud = client.health_check()
print(salud["status"])
```

## Configurar token y esquema de autenticación

El nuevo esquema permite rotar el token y definir el prefijo a utilizar en la cabecera `Authorization`.

```python
client.set_auth_token("token-rotado-123", auth_scheme="Token")
```

Si la API espera el token sin prefijo puede establecerse `auth_scheme=""`.

## Seleccionar idioma de trabajo

```python
# Establecer idioma por defecto
client.set_language("en")

# Sobrescribir idioma en una consulta concreta
respuesta = client.query("¿Qué productos ofrece PBC?", language="es")
print(respuesta["response"])
```

El cliente valida automáticamente que el idioma solicitado esté en la lista de soportados. Si se requiere un conjunto distinto basta con proporcionar la lista en el constructor:

```python
client = AncloraRAGClient(
    api_key="mi-token",
    supported_languages=["es", "en", "pt"],
    default_language="pt",
)
```

## Manejo de caracteres especiales en respuestas

Las respuestas que contienen tildes, eñes u otros caracteres Unicode se mantienen intactas gracias a la normalización automática del encoding HTTP.

```python
resultado = client.query("¿Cuál es la visión de la empresa?", language="es")
print(resultado["response"])  # Ejemplo: "La visión es innovación continua"
```

## Uso con la interfaz de agente

```python
from anclora_rag_client import AIAgentRAGInterface

agent = AIAgentRAGInterface(api_key="mi-token", default_language="es")
agent.set_auth_token("nuevo-token", auth_scheme="Bearer")
agent.set_language("en")
print(agent.ask_question("Which are the PBC products?"))
```
