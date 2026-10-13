import os
from openai import OpenAI


class LLMClient:
    """
    Centralized LLM interface.
    All LLM calls go through this class.
    """

    def __init__(self, model: str, temperature: float = 0.0):
        api_key = os.getenv("OPENAI_API")
        if not api_key:
            raise RuntimeError("OPENAI_API environment variable not set")

        self.model = model
        self.temperature = temperature
        self.client = OpenAI(api_key=api_key)
        self.reset_usage()

    def reset_usage(self) -> None:
        self.usage = {"prompt_tokens": 0, "completion_tokens": 0,
                      "total_tokens": 0, "llm_calls": 0}

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
        )
        usage = getattr(response, "usage", None)
        prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion = int(getattr(usage, "completion_tokens", 0) or 0)
        self.usage["prompt_tokens"] += prompt
        self.usage["completion_tokens"] += completion
        self.usage["total_tokens"] += prompt + completion
        self.usage["llm_calls"] += 1
        return response.choices[0].message.content.strip()

