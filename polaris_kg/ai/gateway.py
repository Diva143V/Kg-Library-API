"""
Central AI Gateway orchestrating reasoning providers and policies.
"""

import logging
from typing import Optional
from polaris_kg.ai.schemas import AIReasonRequest, AIReasonResponse
from polaris_kg.ai.policy import AIEscalationPolicy
from polaris_kg.ai.base import AIProvider
from polaris_kg.ai.providers.anythingllm import AnythingLLMProvider
from polaris_kg.ai.providers.cloud import CloudLLMProvider

logger = logging.getLogger("polaris_kg.ai.gateway")


class AIGateway:
    """
    Central gateway interface for LLM reasoning.
    Controls credit consumption and enforces maximum call limits and cost limits.
    """

    def __init__(self, policy: Optional[AIEscalationPolicy] = None, provider: Optional[AIProvider] = None):
        self.policy = policy or AIEscalationPolicy()
        self.custom_provider = provider
        self.local_provider = AnythingLLMProvider()
        self.cloud_provider = CloudLLMProvider()
        self.calls_count = 0
        self.total_cost = 0.0

    def reason(self, request: AIReasonRequest) -> AIReasonResponse:
        """Execute reasoning prompt via selected provider subject to budget and token check."""
        if not self.policy.ai_enabled:
            return AIReasonResponse(text="AI is disabled by policy", model="none")

        if self.calls_count >= self.policy.max_ai_calls:
            return AIReasonResponse(text="AI calls limit exceeded", model="none")

        # Select active provider
        active_provider: AIProvider = self.custom_provider or self.local_provider
        provider_name = "local-8b"

        if not self.custom_provider:
            if not self.policy.local_first and self.policy.cloud_fallback:
                active_provider = self.cloud_provider
                provider_name = "cloud-llm"

        # 1. Pre-escalation Estimates
        prompt_tokens = active_provider.count_tokens(request.prompt)
        estimated_output_tokens = request.max_tokens
        estimated_cost = active_provider.estimate_cost(prompt_tokens, estimated_output_tokens)

        # Check budget limits
        remaining_budget = self.policy.ai_budget - self.total_cost
        if estimated_cost > remaining_budget or self.total_cost >= self.policy.ai_budget:
            logger.warning(
                f"Estimated cost {estimated_cost} exceeds remaining budget {remaining_budget}. "
                f"Falling back to deterministic output."
            )
            return AIReasonResponse(
                text="Budget limit exhausted for query session.",
                tokens_used=0,
                estimated_cost=0.0,
                model="fallback"
            )

        self.calls_count += 1

        try:
            generated_text = active_provider.generate(
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
        except Exception as e:
            if self.policy.cloud_fallback and active_provider != self.cloud_provider and not self.custom_provider:
                logger.info("Local provider failed, falling back to Cloud LLM")
                active_provider = self.cloud_provider
                provider_name = "cloud-llm"
                generated_text = active_provider.generate(
                    prompt=request.prompt,
                    system_prompt=request.system_prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                )
            else:
                raise e

        # 2. Post-execution Actuals
        actual_output_tokens = active_provider.count_tokens(generated_text)
        actual_cost = active_provider.estimate_cost(prompt_tokens, actual_output_tokens)
        self.total_cost += actual_cost

        return AIReasonResponse(
            text=generated_text,
            tokens_used=prompt_tokens + actual_output_tokens,
            estimated_cost=actual_cost,
            model=provider_name
        )
