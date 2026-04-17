import httpx

from app.services.llm.base import BaseLLMProvider, ChatMessage, LLMResult


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class LlamaProvider(BaseLLMProvider):
    provider_name = "llama3"

    def __init__(self, *, base_url: str | None, api_key: str | None) -> None:
        self.base_url = base_url
        self.api_key = api_key

    async def generate(self, *, model: str, messages: list[ChatMessage]) -> LLMResult:
        effective_model = model or "llama3-8b"
        user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")

        if not self.base_url:
            output = f"[llama3-stub] {user_msg}".strip()
            return LLMResult(
                output_text=output,
                model=effective_model,
                prompt_tokens=sum(_estimate_tokens(m.content) for m in messages),
                completion_tokens=_estimate_tokens(output),
            )

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            res = await client.post(
                "/chat/completions",
                headers=headers,
                json={
                    "model": effective_model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": 0.2,
                },
            )
            res.raise_for_status()
            payload = res.json()

        text = payload["choices"][0]["message"]["content"]
        usage = payload.get("usage", {})
        return LLMResult(
            output_text=text,
            model=payload.get("model", effective_model),
            prompt_tokens=int(usage.get("prompt_tokens", _estimate_tokens(str(messages)))),
            completion_tokens=int(usage.get("completion_tokens", _estimate_tokens(text))),
        )
