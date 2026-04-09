"""LLM 调用 Skill。"""

import httpx
from typing import Any, Dict

from lifeforce.skills.base import Skill


class LLMCallSkill(Skill):
    """通过 OpenAI 兼容接口调用模型。"""

    def __init__(self, config: Any) -> None:
        super().__init__("llm_call")
        self.config = config

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        prompt = params.get("prompt")
        system = params.get("system", "You are a helpful assistant.")
        max_tokens = int(params.get("max_tokens", 500))
        if not prompt:
            raise ValueError("No prompt specified")

        response = httpx.post(
            f"{self.config.llm.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.config.llm.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.config.llm.model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        usage = data.get("usage", {})
        return {
            "response": data["choices"][0]["message"]["content"],
            "usage": {
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
            },
        }
