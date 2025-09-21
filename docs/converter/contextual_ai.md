# Conversion Advisor API (Contextual AI)

El módulo `rag_core.conversion_advisor` encapsula el conocimiento especializado
sobre preservación digital, publicación web y accesibilidad para recomendar el
formato de salida más adecuado antes de convertir documentos. Esta guía describe
la API interna y cómo integrarla en los flujos de agentes.

## Objetivos del asesor

* **Consumo de reglas especializadas**: las recomendaciones incorporan buenas
  prácticas reconocidas (ISO 19005, WCAG 2.1, TIFF sin pérdidas, etc.).
* **Contextualización dinámica**: considera formato de origen, metadatos
  disponibles y uso previsto (`archivado`, `web`, `accesibilidad`).
* **Supervisión para agentes**: permite detectar cuando un archivo aún no cumple
  el formato sugerido y genera advertencias o bloqueos opcionales.

## API principal

### `FormatRecommendation`

```python
from rag_core.conversion_advisor import FormatRecommendation
```

Objeto inmutable que resume la recomendación. Sus atributos clave son:

| Campo | Descripción |
|-------|-------------|
| `recommended_format` | Extensión sugerida (`pdf`, `html`, `epub`, `tiff`, etc.). |
| `profile` | Perfil normativo asociado (ej. `PDF/A-2b`, `HTML5 semántico`). |
| `justification` | Resumen del razonamiento aplicado. |
| `metadata_requirements` | Metadatos adicionales organizados por categoría. |
| `pre_conversion_checks` | Validaciones previas que deben realizarse. |
| `post_conversion_steps` | Acciones posteriores sugeridas. |
| `warnings` | Advertencias dinámicas generadas a partir de los metadatos. |
| `confidence` | Confianza de la regla aplicada (`alta`, `media`). |
| `accepted_extensions` | Extensiones aceptadas como equivalentes al formato. |

Métodos auxiliares:

* `to_dict()` serializa la recomendación.
* `matches_extension(extension)` indica si un archivo con determinada extensión
  ya cumple con la sugerencia.

### `ConversionAdvisor`

```python
from rag_core.conversion_advisor import ConversionAdvisor
```

Constructor opcionalmente acepta un diccionario de reglas personalizadas. En
caso contrario se utilizan los conocimientos por defecto para archivado, web y
accesibilidad.

Método principal:

```python
advisor = ConversionAdvisor()
plan = advisor.recommend(
    source_format="docx",
    intended_use="archivado",
    metadata={"dominant_content": "text", "retention_policy_years": 5},
)
```

El objeto `plan` es una instancia de `FormatRecommendation`. La función acepta
sinónimos en español e inglés para los casos de uso (`"archival"`,
`"preservation"`, `"accessibility"`, etc.).

## Integración con agentes

`AIAgentRAGInterface` utiliza el asesor antes de subir archivos cuando el agente
proporciona el uso previsto:

```python
from anclora_rag_client import AIAgentRAGInterface

agent = AIAgentRAGInterface(api_key="token")
plan = agent.plan_conversion(
    file_path="manual.docx",
    intended_use="web",
    metadata={"dominant_content": "article", "requires_responsive": True},
)

if not plan.matches_extension(".docx"):
    # Convertir el documento a HTML5 antes de subirlo
    transformed_path = convert_to_html("manual.docx")
    agent.add_knowledge(transformed_path, intended_use="web")
else:
    agent.add_knowledge("manual.docx", intended_use="web")
```

El método `add_knowledge` acepta parámetros adicionales:

* `intended_use`: caso de uso a evaluar.
* `metadata`: metadatos opcionales para reglas especializadas.
* `allow_non_recommended_format`: si es `False`, el agente recibe un error cuando
  el archivo no coincide con la recomendación.

Tras cada invocación, `agent.last_conversion_plan` expone la última recomendación
calculada para su consulta o registro.

## Escenarios cubiertos

### Archivado (`archivado`)

* Preferencia por `TIFF` sin pérdidas para másteres escaneados (`>= 300 dpi`).
* Uso de `PDF/A-2b` para documentos textuales con retención controlada.
* Recomendaciones de metadatos Dublin Core, PREMIS y controles de checksum.

### Publicación web (`web`)

* Exportación a `HTML5` semántico con CSS responsivo y metadatos SEO.
* Optimización de imágenes (WebP/AVIF) y buenas prácticas de despliegue
  (`lazy-loading`, pruebas Lighthouse, purga de CDN).

### Accesibilidad (`accesibilidad`)

* Conversión prioritaria a `EPUB 3.2` con cumplimiento WCAG 2.1.
* Alternativa `PDF/UA-1` para documentos cortos etiquetados.
* Validaciones específicas (alt text, MathML, contraste, PAC/Ace).

## Mejores prácticas

1. **Proveer metadatos desde el origen**: cuanto más contexto se entregue al
   asesor, más precisa será la recomendación.
2. **Registrar advertencias**: los mensajes devueltos en `warnings` ayudan a
   detectar acciones pendientes (OCR, alt text, resúmenes web, etc.).
3. **Combinar con pipelines existentes**: el asesor no ejecuta la conversión; su
   objetivo es guiar al agente para que seleccione la herramienta adecuada antes
   de subir el documento a la base de conocimiento.

## Próximos pasos

* Extender la base de conocimientos con perfiles específicos por industria
  (finanzas, salud, educación).
* Conectar el asesor con flujos automáticos de conversión en Docker para
  habilitar auto-remediaciones cuando el agente lo solicite explícitamente.
