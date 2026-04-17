from anthropic import AsyncAnthropic

from app.services.llm.base import BaseLLMProvider, ChatMessage, LLMResult


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class AnthropicProvider(BaseLLMProvider):
    provider_name = "anthropic"

    def __init__(self, *, api_key: str | None) -> None:
        self.client = AsyncAnthropic(api_key=api_key) if api_key else None

    async def generate(self, *, model: str, messages: list[ChatMessage]) -> LLMResult:
        effective_model = model or "claude-3-5-haiku-latest"
        user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")

        if self.client is None:
            output = f"[anthropic-stub] {user_msg}".strip()
            return LLMResult(
                output_text=output,
                model=effective_model,
                prompt_tokens=sum(_estimate_tokens(m.content) for m in messages),
                completion_tokens=_estimate_tokens(output),
            )

        response = await self.client.messages.create(
            model=effective_model,
            max_tokens=800,
            messages=[{"role": m.role, "content": m.content} for m in messages if m.role in {"user", "assistant"}],
        )

        output = ""
        if response.content:
            part = response.content[0]
            output = getattr(part, "text", "")

        return LLMResult(
            output_text=output,
            model=response.model,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
        )
