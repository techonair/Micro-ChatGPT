from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class LLMResult:
    output_text: str
    model: str
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class BaseLLMProvider(ABC):
    provider_name: str

    @abstractmethod
    async def generate(self, *, model: str, messages: list[ChatMessage]) -> LLMResult:
        raise NotImplementedError
