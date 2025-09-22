# Observabilidad de Anclora RAG

Este módulo describe cómo aprovechar la instrumentación basada en métricas Prometheus añadida a los componentes críticos del proyecto.

## Instrumentación disponible

Los flujos principales exponen métricas cuando la librería `prometheus_client` está disponible:

- **Consultas RAG** (`app/common/langchain_module.py`): latencia, volumen por estado, tamaño del contexto recuperado y desglose por colección/dominio de los documentos consultados.
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
| `anclora_rag_collection_usage_total` | Consultas en las que participó cada colección. | `collection`, `domain`, `language`, `status` |
| `anclora_rag_collection_context_documents` | Documentos aportados por colección en el contexto recuperado. | `collection`, `domain`, `language` |
| `anclora_rag_domain_usage_total` | Consultas en las que participó cada dominio funcional. | `domain`, `language`, `status` |
| `anclora_rag_domain_context_documents` | Documentos aportados por dominio. | `domain`, `language` |
| `anclora_agent_requests_total` | Tareas atendidas por agente. | `agent`, `task_type`, `status`, `language` |
| `anclora_agent_latency_seconds` | Histograma de latencias por agente. | `agent`, `task_type`, `status`, `language` |
| `anclora_ingestion_operations_total` | Ingestiones ejecutadas por dominio/extensión. | `domain`, `extension`, `status` |
| `anclora_ingestion_duration_seconds` | Histograma de duración de ingestiones. | `domain`, `extension`, `status` |
| `anclora_ingestion_documents` | Documentos producidos en cada ingestión. | `domain`, `extension`, `status` |
| `anclora_orchestrator_routing_total` | Decisiones del orquestador. | `task_type`, `result` |
| `anclora_knowledge_base_documents` | Documentos disponibles por colección de conocimiento. | `collection`, `domain` |
| `anclora_knowledge_base_domain_documents` | Documentos totales por dominio de conocimiento. | `domain` |

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
3. **Uso de colecciones RAG**: evolución temporal de las colecciones que aportan documentos a las respuestas.
4. **Cobertura por dominio**: desglose de documentos aportados por cada dominio funcional.
5. **Actividad de agentes**: comparación entre ejecuciones exitosas y fallidas por agente.
6. **Documentos en la base de conocimiento**: series por colección/dominio que reflejan el tamaño de la base.
7. **Ingestiones por dominio**: ritmo de ingestión segmentado por dominio de archivo.

El dashboard puede ampliarse añadiendo nuevos paneles; basta con colocar archivos JSON adicionales en `docker/observability/grafana/provisioning/dashboards/json` y reiniciar el servicio de Grafana.

## Harness de regresión y CI

El módulo `tests/regression/agent_suite.py` concentra escenarios de regresión para los agentes documental, multimedia, de código y legal. Internamente reutiliza `AgentRegressionHarness` para medir tres dimensiones en cada escenario:

1. **Latencia** (`time.perf_counter`): se compara con el umbral `thresholds.max_latency` y genera la incidencia `latencia_superior_al_umbral` si se supera.
2. **Cobertura de contexto**: se comprueban `thresholds.min_context_docs` o `thresholds.min_matches` y se reportan los recuentos por colección/dominio recuperados por la consulta.
3. **Calidad**: se evalúan heurísticos específicos (p. ej. presencia de fragmentos en el contexto, estructura de la respuesta o conteo de coincidencias) y se contrastan _snapshots_ como `expected_answer` o listas de resultados.

### Ejecución rápida

```bash
make regression-agents                      # ejecuta python -m tests.regression.agent_suite
python -m tests.regression.agent_suite --format json  # salida estructurada para CI
```

La salida en texto muestra una tabla con las columnas `Agente`, `Escenario`, `Estado`, `Latencia(s)`, `Umbral`, `Cobertura` e `Incidencias`. Cada bloque posterior detalla el desglose por colección/dominio y un resumen de la respuesta del agente. Un estado `OK` implica que la latencia se mantuvo bajo el umbral y que la cobertura/heurísticas cumplieron lo esperado.

### Ajuste de umbrales y datasets

Los escenarios pueden personalizarse con un archivo JSON (o YAML, si está instalada `PyYAML`) que redefine documentos, respuestas esperadas o umbrales. Ejemplo:

```json
{
  "document": {
    "thresholds": {"max_latency": 0.40, "min_context_docs": 2},
    "documents": [
      {"text": "Resumen actualizado con métricas Q4", "collection": "conversion_rules"},
      {"text": "Post-mortem del incidente crítico", "collection": "troubleshooting"}
    ],
    "llm": {
      "answer": "Nuevo resumen ejecutivo validado.",
      "context_fragments": ["Resumen actualizado", "incidente crítico"]
    }
  },
  "code": {
    "matches": [
      {"content": "Reiniciar el servicio", "metadata": {"source": "runbook.md"}}
    ],
    "thresholds": {"min_matches": 1}
  }
}
```

Puede pasarse con `python -m tests.regression.agent_suite --config overrides.json` o definir la ruta mediante la variable `AGENT_REGRESSION_CONFIG`. El _target_ `make regression-agents` hereda esta configuración, por lo que es sencillo integrar el harness en pipelines de CI/CD o comparar datasets alternativos.

## Exportación de métricas a Prometheus y Grafana

El script opcional `scripts/observability/export_metrics.py` permite capturar instantáneas de métricas o dashboards sin depender del stack Docker:

- `--prometheus-url` descarga el _payload_ del _endpoint_ `/metrics` y lo vuelca a un fichero `.prom`.
- `--grafana-url`, junto con `--grafana-api-key` y `--dashboard-uid`, exporta dashboards aprovisionados vía API.

Ejemplos:

```bash
python scripts/observability/export_metrics.py --prometheus-url http://localhost:9000/metrics --output snapshot.prom
python scripts/observability/export_metrics.py --grafana-url http://localhost:3000 \
       --grafana-api-key $GRAFANA_TOKEN --dashboard-uid anclora-rag-overview \
       --output grafana-dashboard.json
```

## Buenas prácticas

- Mantener un prefijo consistente configurando `PROMETHEUS_METRIC_PREFIX` para distinguir entornos (por defecto `anclora`).
- Evitar etiquetas con cardinalidad alta (p.ej. IDs de usuarios) al registrar métricas; las funciones de observabilidad ya normalizan entradas como el idioma (`unknown` cuando no se detecta).
- Validar los cambios ejecutando `pytest` para asegurarse de que la instrumentación no altera los flujos existentes.
