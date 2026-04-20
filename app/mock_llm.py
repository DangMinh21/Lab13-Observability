from __future__ import annotations

import random
import time
from dataclasses import dataclass

from .incidents import STATE


@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class FakeResponse:
    text: str
    usage: FakeUsage
    model: str


class FakeLLM:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model

    def generate(self, prompt: str) -> FakeResponse:
        time.sleep(0.15)
        input_tokens = max(20, len(prompt) // 4)
        output_tokens = random.randint(80, 180)
        if STATE["cost_spike"]:
            output_tokens *= 4
        answer = self._build_answer(prompt)
        return FakeResponse(text=answer, usage=FakeUsage(input_tokens, output_tokens), model=self.model)

    def _build_answer(self, prompt: str) -> str:
        """Generate a context-aware answer from the prompt.

        Extracts the question and retrieved docs from the prompt string,
        then builds a response that echoes relevant keywords — improving
        the heuristic quality score without a real LLM call.
        """
        question = ""
        docs_section = ""
        for line in prompt.splitlines():
            if line.startswith("Question="):
                question = line.removeprefix("Question=").strip()
            elif line.startswith("Docs="):
                docs_section = line.removeprefix("Docs=").strip()

        # Use doc content when available, otherwise fall back to question keywords
        if docs_section and "No domain document matched" not in docs_section:
            base = docs_section.strip("[]'\"")
            return (
                f"Based on available documentation: {base} "
                f"To address your question about {question[:60]}, "
                "please refer to the policy above and ensure all sensitive data is handled accordingly."
            )

        # Fallback: echo question keywords for minimal quality signal
        keywords = " ".join(question.split()[:6]) if question else "your request"
        return (
            f"Regarding '{keywords}': this topic is covered by our general policy. "
            "Ensure logs are structured, PII is redacted, and traces capture latency at each step. "
            "Contact the observability team for domain-specific guidance."
        )
