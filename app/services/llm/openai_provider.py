from openai import AsyncOpenAI

from app.services.llm.base import BaseLLMProvider, ChatMessage, LLMResult


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"

    def __init__(self, *, api_key: str | None, default_model: str) -> None:
        self.default_model = default_model
        self.api_key = api_key
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None

    async def generate(self, *, model: str, messages: list[ChatMessage]) -> LLMResult:
        effective_model = model or self.default_model

        if self.client is None:
            user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")
            output = f"[openai-stub] {user_msg}".strip()
            prompt_tokens = sum(_estimate_tokens(m.content) for m in messages)
            completion_tokens = _estimate_tokens(output)
            return LLMResult(
                output_text=output,
                model=effective_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

        response = await self.client.chat.completions.create(
            model=effective_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=0.2,
        )
        choice = response.choices[0]
        usage = response.usage

        content = choice.message.content or ""
        return LLMResult(
            output_text=content,
            model=response.model,
            prompt_tokens=usage.prompt_tokens if usage else _estimate_tokens(str(messages)),
            completion_tokens=usage.completion_tokens if usage else _estimate_tokens(content),
        )
