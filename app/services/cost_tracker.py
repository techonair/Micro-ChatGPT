class CostTracker:
    # USD per 1K tokens (illustrative defaults)
    PROMPT_RATES = {
        "openai": 0.00015,
        "anthropic": 0.00025,
        "llama3": 0.00005,
    }
    COMPLETION_RATES = {
        "openai": 0.0006,
        "anthropic": 0.00125,
        "llama3": 0.00007,
    }

    def estimate(self, *, provider: str, prompt_tokens: int, completion_tokens: int) -> float:
        prompt_rate = self.PROMPT_RATES.get(provider, 0.0002)
        completion_rate = self.COMPLETION_RATES.get(provider, 0.0008)
        return round((prompt_tokens / 1000 * prompt_rate) + (completion_tokens / 1000 * completion_rate), 8)
