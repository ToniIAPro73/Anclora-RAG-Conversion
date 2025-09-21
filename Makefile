PYTHON ?= python3
BLEU_THRESHOLD ?= 0.25
ROUGE_THRESHOLD ?= 0.30
EVAL_DATASETS := tests/fixtures/sample_responses_es.json tests/fixtures/sample_responses_en.json

.PHONY: eval
## Ejecuta la evaluación de respuestas RAG con métricas BLEU y ROUGE-L

eval:
	$(PYTHON) scripts/evaluate_responses.py --datasets $(EVAL_DATASETS) \
		--bleu-threshold $(BLEU_THRESHOLD) --rouge-threshold $(ROUGE_THRESHOLD)
