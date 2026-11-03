"""Groq provider implementation via Groq's high-speed OpenAI-compatible API."""

import os
from typing import Optional
from agentic_shx.providers.openai_provider import OpenAIProvider

class GroqProvider(OpenAIProvider):
    """Groq provider supporting ultra-fast inference with Llama 3.3, DeepSeek-R1, Mixtral, etc."""

    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        clean_model = model.replace("groq/", "")
        actual_key = api_key or os.getenv("GROQ_API_KEY")
        if not actual_key:
            raise ValueError(
                f"Groq API key not found. Please set GROQ_API_KEY environment variable, "
                f"or configure it in ~/.agentic_shx/config.yaml or your .env file."
            )
        actual_base = base_url or os.getenv("GROQ_BASE_URL") or "https://api.groq.com/openai/v1"
        super().__init__(model=clean_model, api_key=actual_key, base_url=actual_base)
