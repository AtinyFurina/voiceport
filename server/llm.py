"""LLM provider：DeepSeek 官方 API（OpenAI 兼容 /v1/chat/completions）。"""
import requests

from config import config


class DeepseekLlm:
    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def chat(self, messages: list[dict]) -> str:
        r = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "messages": messages, "stream": False},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def get_llm() -> DeepseekLlm:
    return DeepseekLlm(config.deepseek_api_key, config.deepseek_model, config.deepseek_base_url)
