# Colecciones de Chroma y agentes relacionados

El pipeline de *Retrieval Augmented Generation* (RAG) organiza los documentos en
colecciones temáticas dentro de ChromaDB. Cada colección mantiene una
configuración (`CollectionConfig`) que indica el dominio semántico al que
pertenece y permite a los agentes elegir la fuente adecuada al preparar una
respuesta. La siguiente tabla resume el propósito de cada colección y cómo se
relaciona con los agentes disponibles.

| Colección             | Dominio      | Contenido clave                                                                                     | Ingestor principal¹                     | Agente consumidor |
|-----------------------|--------------|------------------------------------------------------------------------------------------------------|-----------------------------------------|-------------------|
| `conversion_rules`    | `documents`  | Manuales, guías y documentación de referencia utilizados en procesos de conversión y capacitación.  | `DocumentIngestor`                      | `DocumentAgent`   |
| `troubleshooting`     | `code`       | Snippets de código y procedimientos para diagnosticar incidentes técnicos.                          | `CodeIngestor`                          | `DocumentAgent`   |
| `multimedia_assets`   | `multimedia` | Transcripciones y descripciones de material audiovisual que enriquecen respuestas multimodales.     | `MultimediaIngestor`                    | `MediaAgent`      |
| `format_specs`        | `formats`    | Convenciones, plantillas y requerimientos de formato que aseguran consistencia en entregables.       | `DocumentIngestor` (extensión planificada) | `DocumentAgent`   |
| `knowledge_guides`    | `guides`     | Playbooks y guías operativas paso a paso para estructurar recomendaciones y mejores prácticas.       | `DocumentIngestor`                      | `DocumentAgent`   |
| `compliance_archive`  | `compliance` | Políticas internas y lineamientos regulatorios para respaldar respuestas con enfoque legal.         | `DocumentIngestor` (curaduría legal)    | `DocumentAgent`   |

¹ *Los ingestors son las clases ubicadas en `app/agents` encargadas de cargar y
normalizar los archivos antes de almacenarlos en ChromaDB. Algunos dominios, como
`formats`, reutilizan la infraestructura de `DocumentIngestor`, pero permiten
filtrar y auditar el contenido con reglas específicas.*

Gracias a esta clasificación, el orquestador puede enrutar tareas hacia el
agente más apropiado (`DocumentAgent` para consultas textuales y `MediaAgent`
para material audiovisual), mientras que las nuevas colecciones amplían la
cobertura temática sin duplicar lógica en los agentes existentes.
