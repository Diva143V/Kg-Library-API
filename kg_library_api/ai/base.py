"""
Unified AIProvider abstract base class for KG Library.
"""

from abc import ABC, abstractmethod
from typing import Optional


class AIProvider(ABC):
    """
    Contract interface for all AI reasoning providers (AnythingLLM, Cloud, and Mock).
    """

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Executes LLM generation on target provider."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Counts or estimates the number of tokens in the given text."""
        pass

    @abstractmethod
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculates estimated transaction cost in USD."""
        pass
