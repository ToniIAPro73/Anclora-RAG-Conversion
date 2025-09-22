PYTHON ?= python3
BLEU_THRESHOLD ?= 0.25
ROUGE_THRESHOLD ?= 0.30
EVAL_DATASETS := tests/fixtures/sample_responses_es.json tests/fixtures/sample_responses_en.json

.PHONY: test
## Ejecuta toda la batería de pruebas de Pytest, incluyendo los pipelines simulados
test:
	pytest

.PHONY: test-converter
## Ejecuta únicamente las pruebas del conversor y verificación de metadatos
test-converter:
	pytest tests/converter

.PHONY: eval
## Ejecuta la evaluación de respuestas RAG con métricas BLEU y ROUGE-L

eval:
	$(PYTHON) scripts/evaluate_responses.py --datasets $(EVAL_DATASETS) \
		--bleu-threshold $(BLEU_THRESHOLD) --rouge-threshold $(ROUGE_THRESHOLD)

.PHONY: regression-agents
## Ejecuta el harness de regresión para agentes y verifica latencia/calidad
regression-agents:
	$(PYTHON) -m tests.regression.agent_suite
