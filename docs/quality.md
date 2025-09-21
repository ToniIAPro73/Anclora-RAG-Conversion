# Control de calidad de respuestas RAG

Este documento describe cómo evaluar respuestas generadas por el sistema RAG con datasets de referencia en español e inglés. El objetivo es contar con una verificación rápida que podamos automatizar en CI antes de desplegar cambios que afecten la calidad de las respuestas.

## Script de evaluación

El script [`scripts/evaluate_responses.py`](../scripts/evaluate_responses.py) calcula dos métricas básicas:

- **BLEU** (BLEU-4 suavizado) para medir la coincidencia de n-gramas entre las respuestas del RAG y las referencias.
- **ROUGE-L** para capturar la superposición basada en subsecuencias entre ambas respuestas.

Por defecto el script busca datasets en `tests/fixtures/sample_responses_es.json` y `tests/fixtures/sample_responses_en.json`, que contienen pares de pregunta, respuesta de referencia y respuesta candidata. Los datasets de ejemplo se construyeron para reflejar estructuras lingüísticas comunes en ambos idiomas.

## Cómo ejecutar la evaluación

El repositorio incluye una tarea de Make para integrar la verificación en pipelines de CI/CD:

```bash
make eval
```

Variables opcionales:

- `BLEU_THRESHOLD`: valor mínimo permitido para el promedio de BLEU (por defecto `0.25`).
- `ROUGE_THRESHOLD`: valor mínimo permitido para el promedio de ROUGE-L (por defecto `0.30`).
- `PYTHON`: intérprete de Python a utilizar.

El comando termina con código de salida distinto de cero si algún dataset evaluado queda por debajo de los umbrales definidos.

## Umbrales mínimos

Los umbrales por defecto se fijaron con base en las métricas obtenidas sobre los datasets incluidos:

- BLEU promedio ≥ **0.25**
- ROUGE-L promedio ≥ **0.30**

Estos valores representan un punto de partida conservador que permite detectar respuestas con poca superposición frente a la referencia sin exigir coincidencia exacta.

## Interpretación de resultados

Al ejecutar el script se imprime un resumen por dataset y un promedio global:

- `OK`: el dataset supera ambos umbrales.
- `FALLO`: al menos una métrica queda por debajo del mínimo configurado.

En caso de fallo se recomienda revisar:

1. La calidad de la respuesta candidata y su alineación semántica con la referencia.
2. Posibles problemas de tokenización o limpieza del texto de entrada.
3. Si los umbrales deben ajustarse para el dominio evaluado (por ejemplo, respuestas muy creativas o resúmenes largos).

El parámetro `--save-report` permite generar un archivo JSON con métricas detalladas por pregunta, útil para depurar o visualizar tendencias en dashboards externos.
