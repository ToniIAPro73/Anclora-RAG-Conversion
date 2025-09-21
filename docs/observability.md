# Observabilidad de Anclora RAG

Este módulo describe cómo aprovechar la instrumentación basada en métricas Prometheus añadida a los componentes críticos del proyecto.

## Instrumentación disponible

Los flujos principales exponen métricas cuando la librería `prometheus_client` está disponible:

- **Consultas RAG** (`app/common/langchain_module.py`): latencia, volumen por estado y tamaño del contexto recuperado.
- **Agentes** (`app/agents/`): ejecuciones por agente, estado y latencia por tarea.
- **Ingestión de archivos** (`BaseFileIngestor`): duración por extensión y conteo de documentos generados.
- **Orquestador**: decisiones de ruteo exitosas o sin agente asignado.

Las métricas se activan cuando se define el puerto de publicación mediante la variable de entorno `PROMETHEUS_METRICS_PORT`. Si la librería no está instalada, las funciones actúan como _no-ops_, evitando errores en entornos de pruebas o pipelines sin Prometheus.

### Métricas expuestas

| Métrica | Descripción | Etiquetas |
| --- | --- | --- |
| `anclora_rag_requests_total` | Consultas procesadas por el pipeline RAG. | `language`, `status` |
| `anclora_rag_request_latency_seconds` | Histograma de latencias del pipeline. | `language`, `status` |
| `anclora_rag_context_documents` | Documentos utilizados como contexto en cada consulta. | `language` |
| `anclora_agent_requests_total` | Tareas atendidas por agente. | `agent`, `task_type`, `status`, `language` |
| `anclora_agent_latency_seconds` | Histograma de latencias por agente. | `agent`, `task_type`, `status`, `language` |
| `anclora_ingestion_operations_total` | Ingestiones ejecutadas por dominio/extensión. | `domain`, `extension`, `status` |
| `anclora_ingestion_duration_seconds` | Histograma de duración de ingestiones. | `domain`, `extension`, `status` |
| `anclora_ingestion_documents` | Documentos producidos en cada ingestión. | `domain`, `extension`, `status` |
| `anclora_orchestrator_routing_total` | Decisiones del orquestador. | `task_type`, `result` |
| `anclora_knowledge_base_documents` | Gauge con el tamaño de la colección vectorial. | `collection` |

## Uso local sin contenedores

1. Instalar la dependencia opcional:
   ```bash
   pip install prometheus-client
   ```
2. Definir el puerto antes de ejecutar el módulo objetivo:
   ```bash
   export PROMETHEUS_METRICS_PORT=9000
   export PROMETHEUS_METRICS_HOST=0.0.0.0  # Opcional (por defecto 0.0.0.0)
   python app/api_endpoints.py  # Ejemplo
   ```
3. Visitar `http://localhost:9000/` para comprobar el _endpoint_ de métricas o apuntar una instancia de Prometheus externa.

## Stack de observabilidad con Docker Compose

Los ficheros `docker-compose.yml` y `docker-compose_sin_gpu.yml` añaden tres servicios adicionales:

- `prometheus` (puerto 9090) con un _scrape_ estático hacia `ui:9000` y `api:9001`.
- `grafana` (puerto 3000) con aprovisionamiento automático del _data source_ y del dashboard `Anclora RAG Observability`.
- Publicación de puertos 9000 y 9001 en los servicios `ui` y `api` para consumir métricas desde el host.

Para levantar el stack completo:

```bash
docker compose up --build
```

Una vez iniciado:

- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3000` (usuario y contraseña por defecto `admin` / `admin`, configurables con `GRAFANA_USER` y `GRAFANA_PASSWORD`).

## Dashboard de referencia

El dashboard se aprovisiona automáticamente en Grafana dentro de la carpeta raíz con el identificador `anclora-rag-overview`. Incluye:

1. **Consultas RAG por estado**: volumen por minuto segmentado por `status`.
2. **Latencia RAG (P95/P50)**: percentiles calculados a partir del histograma de latencia.
3. **Actividad de agentes**: comparación entre ejecuciones exitosas y fallidas por agente.
4. **Documentos en la base de conocimiento**: gauge con el tamaño publicado por `CHROMA_SETTINGS`.
5. **Ingestiones por dominio**: ritmo de ingestión segmentado por dominio de archivo.

El dashboard puede ampliarse añadiendo nuevos paneles; basta con colocar archivos JSON adicionales en `docker/observability/grafana/provisioning/dashboards/json` y reiniciar el servicio de Grafana.

## Buenas prácticas

- Mantener un prefijo consistente configurando `PROMETHEUS_METRIC_PREFIX` para distinguir entornos (por defecto `anclora`).
- Evitar etiquetas con cardinalidad alta (p.ej. IDs de usuarios) al registrar métricas; las funciones de observabilidad ya normalizan entradas como el idioma (`unknown` cuando no se detecta).
- Validar los cambios ejecutando `pytest` para asegurarse de que la instrumentación no altera los flujos existentes.
