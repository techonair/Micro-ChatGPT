from app.core.errors import AppError
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.base import BaseLLMProvider
from app.services.llm.llama_provider import LlamaProvider
from app.services.llm.openai_provider import OpenAIProvider


class LLMProviderFactory:
    def __init__(self, settings) -> None:
        self.settings = settings

    def get(self, provider: str) -> BaseLLMProvider:
        if provider == "openai":
            return OpenAIProvider(
                api_key=self.settings.openai_api_key,
                default_model=self.settings.openai_default_model,
            )
        if provider == "anthropic":
            return AnthropicProvider(api_key=self.settings.anthropic_api_key)
        if provider == "llama3":
            return LlamaProvider(
                base_url=self.settings.llama_api_base_url,
                api_key=self.settings.llama_api_key,
            )

        raise AppError(
            f"Unsupported provider: {provider}",
            status_code=400,
            code="unsupported_provider",
        )
