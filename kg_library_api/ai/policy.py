"""
AI Escalation Policy schema and rules for credit control.
"""

from pydantic import BaseModel, Field, ConfigDict


class AIEscalationPolicy(BaseModel):
    """
    Per-request AI budget and behaviour policy.
    Explicitly marked as mutable so per-request overrides can be applied
    on a model_copy() without mutating the shared default policy.
    """

    model_config = ConfigDict(frozen=False)

    traversal_mode: str = Field("hybrid", description="Traversal mode: 'manual', 'ai', or 'hybrid'")
    ai_enabled: bool = Field(True, description="Toggle AI capabilities entirely")
    max_ai_calls: int = Field(2, description="Upper bound of API invocations per query session")
    ai_budget: float = Field(0.01, description="Strict budget ceiling in USD per query session")
    semantic_threshold: float = Field(0.70, description="Semantic pruning threshold")
    local_first: bool = Field(True, description="Prefer local Ollama/AnythingLLM deployment over cloud")
    cloud_fallback: bool = Field(False, description="Attempt cloud API if local fails")
