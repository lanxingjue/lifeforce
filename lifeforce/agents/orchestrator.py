"""Orchestrator Agent。"""

from typing import Any, Dict, List

import httpx

from lifeforce.core.agent import Agent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem


class Orchestrator(Agent):
    """负责意图理解与回复生成。"""

    def __init__(self, memory: MemorySystem, budget_guard: BudgetGuard, config: Any) -> None:
        super().__init__(
            name="Orchestrator",
            role="任务分解与调度",
            memory=memory,
            budget_guard=budget_guard,
        )
        self.config = config
        self.base_url = config.llm.base_url
        self.user_id = getattr(config.memory, "default_user_id", "default")
        self.system_prompt = (
            "你是 Lifeforce 的 Orchestrator Agent。"
            "你需要理解用户意图并给出简洁友好的回复。"
        )

    def handle_user_message(self, user_message: str) -> str:
        self.log_action("receive_message", {"message": user_message})
        retrieval_limit = getattr(self.config.memory, "retrieval_limit", 5)
        relevant_memories = self.memory.search(
            query=user_message,
            user_id=self.user_id,
            limit=retrieval_limit,
        )
        memory_context = self._format_memories(relevant_memories)
        enhanced_user_message = (
            f"{memory_context}\n\n"
            f"用户问题：{user_message}\n\n"
            "请优先依据相关记忆回答；若记忆中没有足够信息，请明确说明。"
        )

        estimated_tokens = max(120, len(enhanced_user_message) // 4 + 100)
        if not self.request_tokens(estimated_tokens, "process_user_message"):
            return "预算不足，无法处理请求。"

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.llm.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.llm.model,
                    "max_tokens": 500,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": enhanced_user_message},
                    ],
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            reply = data["choices"][0]["message"]["content"]
            self.memory.add(
                messages=[
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": reply},
                ],
                user_id=self.user_id,
                metadata={"source": "chat_turn"},
            )
            self.log_action("send_reply", {"reply": reply})
            return reply
        except Exception as exc:
            self.logger.error("Error calling LLM: %s", exc)
            return f"处理消息时出错: {exc}"

    def _format_memories(self, memories: List[Dict[str, Any]]) -> str:
        if not memories:
            return "（没有检索到相关记忆）"
        lines = ["相关记忆："]
        for idx, memory in enumerate(memories, start=1):
            text = memory.get("memory") or memory.get("content") or ""
            score = float(memory.get("score", 0.0))
            decay = float(memory.get("decay_factor", 1.0))
            lines.append(f"{idx}. {text} (相关性: {score:.2f}, 新鲜度: {decay:.2f})")
        return "\n".join(lines)

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        text = message if isinstance(message, str) else message.get("content", "")
        return {"reply": self.handle_user_message(text)}
