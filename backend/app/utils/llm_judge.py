import logging
import re

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMJudge:
    """LLM-as-judge for hallucination and relevance scoring."""

    def __init__(self) -> None:
        self.model = settings.DEFAULT_LLM_JUDGE_MODEL

    async def score_hallucination(self, output: str, context: str) -> float:
        if settings.ANTHROPIC_API_KEY:
            try:
                return await self._anthropic_hallucination_score(output, context)
            except Exception as exc:
                logger.warning("Anthropic judge failed, using heuristic: %s", exc)
        return self._keyword_heuristic(output, context)

    async def score_relevance(self, output: str, task: str) -> float:
        if not task.strip():
            return 0.0
        overlap = len(set(task.lower().split()) & set(output.lower().split()))
        return min(1.0, overlap / max(len(task.split()), 1))

    async def _anthropic_hallucination_score(self, output: str, context: str) -> float:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        prompt = (
            "Rate the hallucination level in the OUTPUT compared to the CONTEXT.\n"
            "Return ONLY a number from 0 (no hallucination) to 10 (severe hallucination).\n\n"
            f"CONTEXT:\n{context[:2000]}\n\nOUTPUT:\n{output[:2000]}"
        )
        message = await client.messages.create(
            model=self.model,
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        match = re.search(r"(\d+(?:\.\d+)?)", text)
        if not match:
            return self._keyword_heuristic(output, context)
        raw = float(match.group(1))
        normalized = min(max(raw / 10.0, 0.0), 1.0)
        return round(normalized, 4)

    @staticmethod
    def _keyword_heuristic(output: str, context: str) -> float:
        output_words = set(re.findall(r"\w+", output.lower()))
        context_words = set(re.findall(r"\w+", context.lower()))
        if not output_words:
            return 0.0
        unsupported = output_words - context_words
        rate = len(unsupported) / len(output_words)
        return round(min(max(rate, 0.0), 1.0), 4)
