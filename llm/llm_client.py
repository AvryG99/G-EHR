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

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
        )
        return response.choices[0].message.content.strip()

