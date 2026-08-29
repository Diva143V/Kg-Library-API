"""
Mock AI Provider implementation for offline, deterministic testing.
"""

from typing import Optional, Dict
from polaris_kg.ai.base import AIProvider


class MockAIProvider(AIProvider):
    """
    Mock AI Provider designed to run without network access or active API keys.
    """

    def __init__(self, predefined_responses: Optional[Dict[str, str]] = None):
        self.predefined_responses = predefined_responses or {}

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        # Match prompt keywords
        prompt_lower = prompt.lower()
        for key, resp in self.predefined_responses.items():
            if key.lower() in prompt_lower:
                return resp

        # Default fallback deterministic answer
        return (
            "[Mock Provider Response] Evaluation suggests that Protein B correlates with Disease C. "
            "Evidence supports the association, and clinical assertions are present."
        )

    def count_tokens(self, text: str) -> int:
        # Simple whitespace heuristic for token approximation (1 token ~= 0.75 words, roughly word count * 1.3)
        return int(len(text.split()) * 1.3)

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        # Fixed cost rate: $0.15 per million tokens
        return (prompt_tokens + completion_tokens) * 0.00000015
