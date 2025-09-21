"""Utility script to benchmark embedding backends used by the RAG stack."""

from __future__ import annotations

import argparse
import os
import statistics
import time
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from sentence_transformers import SentenceTransformer, util
from tabulate import tabulate


# Representative multilingual queries paired with a relevant answer and challenging negatives.
BENCHMARK_ITEMS = [
    {
        "query": "¿Cuál es la capital de Francia?",
        "positive": "La capital de Francia es París.",
        "negatives": [
            "La capital de Italia es Roma.",
            "Francia está en Europa y limita con Alemania.",
        ],
    },
    {
        "query": "How do I reset my account password?",
        "positive": "To reset your password, click on 'Forgot password' and follow the instructions.",
        "negatives": [
            "You can update your email address from the profile page.",
            "Resetting the router will restore factory settings.",
        ],
    },
    {
        "query": "Qual é o horário de funcionamento do suporte?",
        "positive": "O suporte funciona de segunda a sexta das 9h às 18h (BRT).",
        "negatives": [
            "O suporte fornece treinamento sob demanda aos sábados.",
            "O suporte opera 24 horas, incluindo feriados.",
        ],
    },
    {
        "query": "Quels documents sont nécessaires pour voyager en Argentine?",
        "positive": "Il faut un passeport valide et, pour certains pays, un visa.",
        "negatives": [
            "Les documents requis pour voyager en Espagne sont les mêmes qu'en Italie.",
            "Un permis de conduire international est obligatoire au Canada.",
        ],
    },
]


@dataclass
class EvaluationResult:
    model_name: str
    encode_seconds: float
    mean_positive_similarity: float
    mean_negative_similarity: float
    accuracy: float

    def as_row(self) -> List[str]:
        return [
            self.model_name,
            f"{self.encode_seconds:.2f}s",
            f"{self.mean_positive_similarity:.3f}",
            f"{self.mean_negative_similarity:.3f}",
            f"{self.accuracy * 100:.1f}%",
        ]


def _flatten_texts(items: Sequence[dict]) -> List[str]:
    unique_texts: list[str] = []
    seen = set()
    for item in items:
        for text in [item["query"], item["positive"], *item["negatives"]]:
            if text not in seen:
                unique_texts.append(text)
                seen.add(text)
    return unique_texts


def _batched(iterable: Iterable[str], batch_size: int) -> Iterable[List[str]]:
    batch: list[str] = []
    for element in iterable:
        batch.append(element)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def evaluate_model(model_name: str, batch_size: int) -> EvaluationResult:
    model = SentenceTransformer(model_name)
    texts = _flatten_texts(BENCHMARK_ITEMS)

    start = time.perf_counter()
    embeddings = {}
    for batch in _batched(texts, batch_size):
        vectors = model.encode(batch, convert_to_tensor=True, show_progress_bar=False, normalize_embeddings=True)
        for text, vector in zip(batch, vectors):
            embeddings[text] = vector
    encode_seconds = time.perf_counter() - start

    positive_scores: list[float] = []
    negative_scores: list[float] = []
    correct = 0

    for item in BENCHMARK_ITEMS:
        query_vec = embeddings[item["query"]]
        positive_vec = embeddings[item["positive"]]
        positive_score = float(util.pytorch_cos_sim(query_vec, positive_vec))
        negative_vecs = [embeddings[text] for text in item["negatives"]]
        # Evaluate the hardest negative (the most similar to the query)
        hard_negative_score = max(float(util.pytorch_cos_sim(query_vec, neg_vec)) for neg_vec in negative_vecs)

        positive_scores.append(positive_score)
        negative_scores.append(hard_negative_score)
        if positive_score > hard_negative_score:
            correct += 1

    return EvaluationResult(
        model_name=model_name,
        encode_seconds=encode_seconds,
        mean_positive_similarity=statistics.fmean(positive_scores),
        mean_negative_similarity=statistics.fmean(negative_scores),
        accuracy=correct / len(BENCHMARK_ITEMS),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark embedding models used by Anclora AI RAG")
    parser.add_argument(
        "--models",
        nargs="*",
        help=(
            "Embedding models to benchmark. Defaults to the model defined in the EMBEDDINGS_MODEL_NAME "
            "environment variable or 'sentence-transformers/all-mpnet-base-v2'."
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Batch size for encoding texts. Increasing the value can speed up evaluation if enough memory is available.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.models:
        models_to_test = args.models
    else:
        env_model = os.environ.get("EMBEDDINGS_MODEL_NAME")
        if env_model:
            models_to_test = [env_model]
        else:
            models_to_test = ["sentence-transformers/all-mpnet-base-v2"]

    results = [evaluate_model(model_name, args.batch_size) for model_name in models_to_test]

    headers = [
        "Model",
        "Encoding time",
        "Mean positive cos-sim",
        "Mean hardest negative cos-sim",
        "Accuracy",
    ]
    table = [result.as_row() for result in results]
    print(tabulate(table, headers=headers, tablefmt="github"))


if __name__ == "__main__":
    main()
