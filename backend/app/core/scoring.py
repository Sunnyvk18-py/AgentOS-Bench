import logging
import os
import re
from functools import lru_cache

from app.schemas.run import ScoreWeights
from app.utils.llm_judge import LLMJudge

logger = logging.getLogger(__name__)

_judge = LLMJudge()
_semantic_enabled = os.getenv("USE_SEMANTIC_SCORING", "false").lower() == "true"


def normalize_latency(latency_ms: int) -> float:
    if latency_ms <= 500:
        return 1.0
    if latency_ms >= 10000:
        return 0.0
    return max(0.0, 1.0 - (latency_ms - 500) / 9500)


def normalize_cost(cost_usd: float) -> float:
    if cost_usd <= 0.001:
        return 1.0
    if cost_usd >= 0.10:
        return 0.0
    return max(0.0, 1.0 - (cost_usd - 0.001) / 0.099)


def compute_composite_score(
    accuracy: float,
    hallucination: float,
    tool_precision: float,
    latency_ms: int,
    cost_usd: float,
    weights: ScoreWeights | None = None,
) -> float:
    weights = weights or ScoreWeights()
    norm_latency = normalize_latency(latency_ms)
    norm_cost = normalize_cost(cost_usd)
    hallucination_inverted = 1.0 - min(max(hallucination, 0.0), 1.0)

    composite = (
        weights.accuracy_weight * accuracy
        + weights.hallucination_weight * hallucination_inverted
        + weights.tool_precision_weight * tool_precision
        + weights.latency_weight * norm_latency
        + weights.cost_weight * norm_cost
    )
    return round(min(max(composite, 0.0), 1.0), 4)


def _token_overlap(expected: str, actual: str) -> float:
    expected_tokens = set(re.findall(r"\w+", expected.lower()))
    actual_tokens = set(re.findall(r"\w+", actual.lower()))
    if not expected_tokens:
        return 1.0 if not actual_tokens else 0.0
    overlap = len(expected_tokens & actual_tokens)
    return overlap / len(expected_tokens)


@lru_cache(maxsize=1)
def _get_sentence_model():
    if not _semantic_enabled:
        return None
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as exc:
        logger.warning("sentence-transformers unavailable: %s", exc)
        return None


def _semantic_similarity(expected: str, actual: str) -> float:
    model = _get_sentence_model()
    if model is None:
        return _token_overlap(expected, actual)
    try:
        embeddings = model.encode([expected, actual])
        dot = float(embeddings[0] @ embeddings[1])
        norm = float(
            (embeddings[0] @ embeddings[0]) ** 0.5 * (embeddings[1] @ embeddings[1]) ** 0.5
        )
        if norm == 0:
            return 0.0
        cosine = dot / norm
        return max(0.0, min(1.0, (cosine + 1) / 2))
    except Exception as exc:
        logger.warning("Semantic similarity failed, using token overlap: %s", exc)
        return _token_overlap(expected, actual)


def compute_accuracy_score(expected_output: str, actual_output: str) -> float:
    token_score = _token_overlap(expected_output, actual_output)
    semantic_score = _semantic_similarity(expected_output, actual_output)
    return round(0.4 * token_score + 0.6 * semantic_score, 4)


async def compute_hallucination_score(output: str, context: str) -> float:
    return await _judge.score_hallucination(output, context)


def compute_tool_precision(expected_tools: list[str], actual_tools: list[str]) -> float:
    expected_set = set(expected_tools)
    actual_set = set(actual_tools)
    if not expected_set and not actual_set:
        return 1.0
    if not expected_set or not actual_set:
        return 0.0
    true_positives = len(expected_set & actual_set)
    precision = true_positives / len(actual_set) if actual_set else 0.0
    recall = true_positives / len(expected_set) if expected_set else 0.0
    if precision + recall == 0:
        return 0.0
    f1 = 2 * precision * recall / (precision + recall)
    return round(f1, 4)
