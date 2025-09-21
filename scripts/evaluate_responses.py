#!/usr/bin/env python3
"""Utility to evaluate RAG responses against reference answers.

The script computes basic BLEU and ROUGE-L metrics for multilingual
fixtures to provide a lightweight quality gate that can be automated in CI.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


@dataclass
class EvaluationItem:
    """Container for a single question/response pair."""

    question: str
    reference: str
    candidate: str
    bleu: float
    rouge_l: float


@dataclass
class DatasetEvaluation:
    """Aggregated results for a dataset in a specific language."""

    path: Path
    language: str
    size: int
    bleu: float
    rouge_l: float
    items: List[EvaluationItem]


_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> List[str]:
    """Tokenise text into lower-case word tokens for metric computation."""

    return _TOKEN_PATTERN.findall(text.lower())


def _generate_ngrams(tokens: Sequence[str], n: int) -> Iterable[Sequence[str]]:
    for i in range(len(tokens) - n + 1):
        yield tuple(tokens[i : i + n])


def compute_bleu(reference_tokens: Sequence[str], candidate_tokens: Sequence[str], max_n: int = 4) -> float:
    """Compute a smoothed BLEU score for a candidate against a reference."""

    candidate_len = len(candidate_tokens)
    reference_len = len(reference_tokens)

    if candidate_len == 0:
        return 0.0

    effective_max_n = min(max_n, candidate_len)
    weights = [1 / effective_max_n] * effective_max_n

    precisions: List[float] = []
    ref_counters: Dict[int, Counter] = {}

    for n in range(1, effective_max_n + 1):
        cand_ngrams = Counter(_generate_ngrams(candidate_tokens, n))
        if n not in ref_counters:
            ref_counters[n] = Counter(_generate_ngrams(reference_tokens, n))
        ref_ngrams = ref_counters[n]
        overlap = sum(min(count, ref_ngrams[ngram]) for ngram, count in cand_ngrams.items())
        total = sum(cand_ngrams.values())
        if total == 0:
            precisions.append(0.0)
        else:
            precisions.append((overlap + 1) / (total + 1))

    if not precisions or any(p == 0 for p in precisions):
        geo_mean = 0.0
    else:
        geo_mean = math.exp(sum(weight * math.log(p) for weight, p in zip(weights, precisions)))

    if candidate_len > reference_len:
        brevity_penalty = 1.0
    else:
        brevity_penalty = math.exp(1 - reference_len / candidate_len)

    return brevity_penalty * geo_mean


def _lcs_length(reference_tokens: Sequence[str], candidate_tokens: Sequence[str]) -> int:
    ref_len = len(reference_tokens)
    cand_len = len(candidate_tokens)
    if ref_len == 0 or cand_len == 0:
        return 0

    dp = [[0] * (cand_len + 1) for _ in range(ref_len + 1)]
    for i in range(1, ref_len + 1):
        for j in range(1, cand_len + 1):
            if reference_tokens[i - 1] == candidate_tokens[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[-1][-1]


def compute_rouge_l(reference_tokens: Sequence[str], candidate_tokens: Sequence[str], beta: float = 1.2) -> float:
    """Compute ROUGE-L based on longest common subsequence."""

    lcs = _lcs_length(reference_tokens, candidate_tokens)
    if lcs == 0:
        return 0.0

    recall = lcs / len(reference_tokens) if reference_tokens else 0.0
    precision = lcs / len(candidate_tokens) if candidate_tokens else 0.0

    if recall == 0 or precision == 0:
        return 0.0

    beta_sq = beta ** 2
    return (1 + beta_sq) * recall * precision / (recall + beta_sq * precision)


def evaluate_dataset(path: Path) -> DatasetEvaluation:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    items_payload = payload.get("items", [])
    language = payload.get("language", "unknown")

    evaluation_items: List[EvaluationItem] = []

    for item in items_payload:
        reference = item["reference"]
        candidate = item["candidate"]
        reference_tokens = tokenize(reference)
        candidate_tokens = tokenize(candidate)
        bleu = compute_bleu(reference_tokens, candidate_tokens)
        rouge_l = compute_rouge_l(reference_tokens, candidate_tokens)
        evaluation_items.append(
            EvaluationItem(
                question=item.get("question", ""),
                reference=reference,
                candidate=candidate,
                bleu=bleu,
                rouge_l=rouge_l,
            )
        )

    dataset_bleu = sum(item.bleu for item in evaluation_items) / len(evaluation_items) if evaluation_items else 0.0
    dataset_rouge = sum(item.rouge_l for item in evaluation_items) / len(evaluation_items) if evaluation_items else 0.0

    return DatasetEvaluation(
        path=path,
        language=language,
        size=len(evaluation_items),
        bleu=dataset_bleu,
        rouge_l=dataset_rouge,
        items=evaluation_items,
    )


def format_metric(value: float) -> str:
    return f"{value:.3f}"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    default_datasets = [
        root / "tests" / "fixtures" / "sample_responses_es.json",
        root / "tests" / "fixtures" / "sample_responses_en.json",
    ]

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--datasets",
        nargs="+",
        type=Path,
        default=default_datasets,
        help="Ruta(s) a los archivos JSON con preguntas, referencias y respuestas evaluadas.",
    )
    parser.add_argument("--bleu-threshold", type=float, default=0.25, help="Mínimo BLEU promedio permitido.")
    parser.add_argument(
        "--rouge-threshold", type=float, default=0.30, help="Mínimo ROUGE-L promedio permitido."
    )
    parser.add_argument(
        "--save-report",
        type=Path,
        help="Ruta opcional para almacenar un informe JSON con los resultados detallados.",
    )

    args = parser.parse_args()

    datasets: List[DatasetEvaluation] = []
    for dataset_path in args.datasets:
        if not dataset_path.exists():
            raise FileNotFoundError(f"No se encontró el dataset: {dataset_path}")
        datasets.append(evaluate_dataset(dataset_path))

    total_items = sum(dataset.size for dataset in datasets)
    overall_bleu = (
        sum(dataset.bleu * dataset.size for dataset in datasets) / total_items if total_items else 0.0
    )
    overall_rouge = (
        sum(dataset.rouge_l * dataset.size for dataset in datasets) / total_items if total_items else 0.0
    )

    thresholds = {"bleu": args.bleu_threshold, "rouge_l": args.rouge_threshold}

    overall_pass = True
    for dataset in datasets:
        dataset_pass = dataset.bleu >= thresholds["bleu"] and dataset.rouge_l >= thresholds["rouge_l"]
        if not dataset_pass:
            overall_pass = False

    if overall_bleu < thresholds["bleu"] or overall_rouge < thresholds["rouge_l"]:
        overall_pass = False

    if not datasets:
        overall_pass = False

    print("Evaluación de respuestas RAG")
    print("============================")
    print(f"Umbrales -> BLEU ≥ {thresholds['bleu']:.2f}, ROUGE-L ≥ {thresholds['rouge_l']:.2f}")
    print()

    for dataset in datasets:
        dataset_pass = dataset.bleu >= thresholds["bleu"] and dataset.rouge_l >= thresholds["rouge_l"]
        status = "OK" if dataset_pass else "FALLO"
        print(
            f"- {dataset.path.name} [{dataset.language}] (n={dataset.size}): "
            f"BLEU={format_metric(dataset.bleu)}, ROUGE-L={format_metric(dataset.rouge_l)} -> {status}"
        )

    print()
    overall_status = "OK" if overall_pass else "FALLO"
    print(
        f"Promedio global (n={total_items}): BLEU={format_metric(overall_bleu)}, "
        f"ROUGE-L={format_metric(overall_rouge)} -> {overall_status}"
    )

    if args.save_report:
        report = {
            "thresholds": thresholds,
            "datasets": [
                {
                    "path": str(dataset.path),
                    "language": dataset.language,
                    "size": dataset.size,
                    "bleu": dataset.bleu,
                    "rouge_l": dataset.rouge_l,
                    "items": [
                        {
                            "question": item.question,
                            "reference": item.reference,
                            "candidate": item.candidate,
                            "bleu": item.bleu,
                            "rouge_l": item.rouge_l,
                        }
                        for item in dataset.items
                    ],
                }
                for dataset in datasets
            ],
            "overall": {"bleu": overall_bleu, "rouge_l": overall_rouge, "items": total_items},
            "passed": overall_pass,
        }
        args.save_report.parent.mkdir(parents=True, exist_ok=True)
        with args.save_report.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        print(f"\nInforme guardado en {args.save_report}")

    if not overall_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
