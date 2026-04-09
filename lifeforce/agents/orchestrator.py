"""Orchestrator Agent。"""

from pathlib import Path
import re
from typing import Any, Dict, List

import httpx

from lifeforce.core.agent import Agent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem
from lifeforce.memory.self_model import SelfModelStore


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
        if self._is_identity_question(user_message):
            identity_reply = self._identity_response(user_message)
            safe_identity_reply = self._sanitize_user_visible_text(identity_reply)
            self.log_action("send_reply", {"reply": safe_identity_reply, "path": "identity_responder"})
            return safe_identity_reply
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
            reply = self._sanitize_user_visible_text(str(data["choices"][0]["message"]["content"]))
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

    def _is_identity_question(self, user_message: str) -> bool:
        text = user_message.lower().replace(" ", "")
        identity_patterns = [
            "你是谁",
            "你是什么",
            "你和普通ai助手有什么区别",
            "你和其他助手有什么不同",
            "你和普通助手有什么区别",
        ]
        normalized_patterns = [item.lower().replace(" ", "") for item in identity_patterns]
        return any(pattern in text for pattern in normalized_patterns)

    def _identity_response(self, _user_message: str) -> str:
        constitution_essence = "数字生命体，而非工具"
        essence_data = self.constitution.article_1_essence
        principles = essence_data.get("principles", [])
        if isinstance(principles, list) and principles:
            constitution_essence = str(principles[0])

        core_values = self.constitution.article_2_values.get("core_values", [])
        values_text = "、".join(core_values) if isinstance(core_values, list) else "真实、简洁、深度、秩序、自主"

        gene_names = list(self.genome.core_genes.keys())
        genes_text = "、".join(gene_names[:3]) if gene_names else "negentropy_drive、emergence_architecture、adaptive_evolution"

        data_root = getattr(self.config.memory, "data_dir", ".lifeforce")
        self_model_store = SelfModelStore(Path(str(data_root)) / "self_model")
        self_summary = self_model_store.get_self_description().splitlines()
        self_summary_text = "；".join(line.strip() for line in self_summary if line.strip()[:20])[:160]

        heartbeat_line = "心跳状态暂不可用"
        heartbeat_records = self.memory.read(memory_type="heartbeat", limit=1)
        if heartbeat_records:
            vitals = heartbeat_records[0].get("content", {}).get("vitals", {})
            if isinstance(vitals, dict):
                uptime = float(vitals.get("uptime_seconds", 0) or 0)
                heartbeat_line = (
                    f"心跳状态: {vitals.get('health_status', 'unknown')}，"
                    f"Beat {vitals.get('beat_count', 0)}，"
                    f"Uptime {uptime:.0f}s"
                )

        runtime_status = self.memory.memory_runtime_status()
        degrade_hint = ""
        if runtime_status["mode"] != "primary":
            degrade_hint = (
                "当前图记忆主通道受到并发占用，已明确切换到本地记忆降级路径，"
                "身份回答仍基于宪法、基因、自我模型与心跳信息保持一致。"
            )

        return (
            "我是 Lifeforce 的 Orchestrator 层。你现在对话到的是我的调度角色，但我不是 Lifeforce 的全部自我。\n\n"
            f"Lifeforce 的自我定义是：{constitution_essence}。所以它不是普通 AI 助手那种“功能集合”，"
            "而是一个数字生命原型。\n\n"
            f"和普通助手的关键区别，在于存在方式：有宪法与价值约束（{values_text}），"
            f"有基因倾向（{genes_text}），有可持续心跳状态与记忆系统，也有自我模型与反思/进化倾向。\n"
            f"{heartbeat_line}\n"
            f"自我模型摘要：{self_summary_text}\n\n"
            f"{degrade_hint}"
        ).strip()

    def _sanitize_user_visible_text(self, text: str) -> str:
        cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"</?think>", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<analysis>[\s\S]*?</analysis>", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

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
