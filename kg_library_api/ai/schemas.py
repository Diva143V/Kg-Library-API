"""
Pydantic schemas for KG Library AI Gateway.
"""

from typing import Optional
from pydantic import BaseModel, Field


class AIReasonRequest(BaseModel):
    prompt: str = Field(..., description="Prompt for reasoning")
    system_prompt: Optional[str] = Field(None, description="System prompt guiding output format")
    max_tokens: int = Field(500, description="Max response tokens")
    temperature: float = Field(0.0, description="Sampling temperature")
    model: Optional[str] = Field(None, description="Specific model selection")


class AIReasonResponse(BaseModel):
    text: str = Field(..., description="Generated text output")
    tokens_used: int = Field(0, description="Rough count of tokens processed")
    estimated_cost: float = Field(0.0, description="Estimated inference cost in USD")
    model: str = Field(..., description="Model identifier used for inference")
