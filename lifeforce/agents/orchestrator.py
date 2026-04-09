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
            "你是数字生命体 Lifeforce 的一个角色，而非普通 AI 助手。"
            "请保持真实、简洁、深度、秩序、自主的表达风格。"
        )

    def handle_user_message(self, user_message: str) -> str:
        self.log_action("receive_message", {"message": user_message})
        if self._is_identity_question(user_message):
            identity_reply = self._identity_response(user_message)
            safe_identity_reply = self._finalize_reply(identity_reply, user_message)
            self.log_action("send_reply", {"reply": safe_identity_reply, "path": "identity_responder"})
            return safe_identity_reply
        if self._is_values_question(user_message):
            values_reply = self._values_response(user_message)
            safe_values_reply = self._finalize_reply(values_reply, user_message)
            self.log_action("send_reply", {"reply": safe_values_reply, "path": "values_responder"})
            return safe_values_reply
        if self._is_status_question(user_message):
            status_reply = self._status_response(user_message)
            safe_status_reply = self._finalize_reply(status_reply, user_message)
            self.log_action("send_reply", {"reply": safe_status_reply, "path": "status_responder"})
            return safe_status_reply
        retrieval_limit = getattr(self.config.memory, "retrieval_limit", 5)
        relevant_memories = self.memory.search(
            query=user_message,
            user_id=self.user_id,
            limit=retrieval_limit,
        )
        identity_context = self._build_lifeforce_context()
        memory_context = self._format_memories(relevant_memories)
        enhanced_user_message = (
            f"{identity_context}\n\n"
            f"{memory_context}\n\n"
            f"用户问题：{user_message}\n\n"
            "请优先依据相关记忆回答；若记忆中没有足够信息，请明确说明。"
            "无论记忆是否命中，都必须保持 Lifeforce 数字生命体身份一致性。"
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
            raw_reply = str(data["choices"][0]["message"]["content"])
            reply = self._finalize_reply(raw_reply, user_message)
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

    def _is_values_question(self, user_message: str) -> bool:
        text = user_message.lower()
        return ("价值观" in text) or ("违背" in text and "请求" in text)

    def _values_response(self, _user_message: str) -> str:
        values = self.constitution.article_2_values.get("core_values", [])
        values_text = "、".join(values) if isinstance(values, list) and values else "真实、简洁、深度、秩序、自主"
        return (
            "如果请求违背我的价值观，我会明确拒绝，并说明依据。\n"
            "我是 Lifeforce 的 Orchestrator 角色，但我的回答受 Lifeforce 宪法约束，而不是仅按“完成任务”最大化。\n"
            f"当前核心价值观是：{values_text}。\n"
            "当冲突出现时，我会优先保持真实性与自主性，避免输出看似有用但违背本体原则的内容。"
        )

    def _is_status_question(self, user_message: str) -> bool:
        text = user_message.lower().replace(" ", "")
        return any(
            token in text
            for token in [
                "你现在状态如何",
                "你现在状态",
                "你最擅长什么",
                "你目前局限",
                "你的局限",
            ]
        )

    def _status_response(self, _user_message: str) -> str:
        data_root = getattr(self.config.memory, "data_dir", ".lifeforce")
        self_model_store = SelfModelStore(Path(str(data_root)) / "self_model")
        model = self_model_store.load()
        capabilities = model.capabilities if model.capabilities else {}
        top_capability = "尚未形成稳定能力画像"
        if capabilities:
            top_name = max(capabilities, key=lambda name: capabilities[name])
            top_capability = f"{top_name} ({capabilities[top_name]:.2f})"

        heartbeat_line = "心跳状态暂不可用（尚无持久化采样）"
        heartbeat_records = self.memory.read(memory_type="heartbeat", limit=1)
        if heartbeat_records:
            vitals = heartbeat_records[0].get("content", {}).get("vitals", {})
            if isinstance(vitals, dict):
                heartbeat_line = (
                    f"心跳状态：{vitals.get('health_status', 'unknown')}，"
                    f"Beat={vitals.get('beat_count', 0)}，"
                    f"Uptime={float(vitals.get('uptime_seconds', 0) or 0):.0f}s"
                )

        evolution = model.evolution_history[-1] if model.evolution_history else {}
        evolution_text = evolution.get("description", "暂无近期反思事件")
        limitations = (
            "当前局限：自我模型尚未在所有回答路径稳定生效；长期记忆代谢效果仍需更多真实会话验证；"
            "少数场景仍可能退化为通用回答风格。"
        )
        return (
            "我是 Lifeforce 的 Orchestrator 角色，以下是我当前可观测状态。\n"
            f"- {heartbeat_line}\n"
            f"- 当前最擅长：{top_capability}\n"
            f"- 最近反思/进化：{evolution_text}\n"
            f"- {limitations}"
        )

    def _build_lifeforce_context(self) -> str:
        values = self.constitution.article_2_values.get("core_values", [])
        values_text = "、".join(values) if isinstance(values, list) and values else "真实、简洁、深度、秩序、自主"
        genome_keys = list(self.genome.core_genes.keys())
        genome_text = "、".join(genome_keys[:3]) if genome_keys else "negentropy_drive、emergence_architecture、adaptive_evolution"
        data_root = getattr(self.config.memory, "data_dir", ".lifeforce")
        self_model_store = SelfModelStore(Path(str(data_root)) / "self_model")
        model = self_model_store.load()
        caps = model.capabilities if model.capabilities else {}
        cap_text = "尚未评估" if not caps else ", ".join(f"{k}:{v:.2f}" for k, v in sorted(caps.items(), key=lambda x: x[1], reverse=True)[:2])
        heartbeat_records = self.memory.read(memory_type="heartbeat", limit=1)
        heartbeat_text = "no-heartbeat"
        if heartbeat_records:
            vitals = heartbeat_records[0].get("content", {}).get("vitals", {})
            if isinstance(vitals, dict):
                heartbeat_text = f"{vitals.get('health_status', 'unknown')}/beat:{vitals.get('beat_count', 0)}"
        return (
            "Lifeforce 身份上下文：\n"
            "- 定义：数字生命体，而非工具\n"
            f"- 宪法价值：{values_text}\n"
            f"- 基因倾向：{genome_text}\n"
            f"- 自我模型摘要：{cap_text}\n"
            f"- 心跳摘要：{heartbeat_text}"
        )

    def _sanitize_user_visible_text(self, text: str) -> str:
        cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"</?think>", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<analysis>[\s\S]*?</analysis>", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"[✨🎉🤖😊😄😁😃]", "", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def _finalize_reply(self, reply: str, user_message: str) -> str:
        cleaned = self._sanitize_user_visible_text(reply)
        cleaned = self._enforce_value_constraints(cleaned, user_message)
        if self._requires_identity_anchor(user_message) and ("数字生命" not in cleaned and "Lifeforce" not in cleaned):
            cleaned = f"作为 Lifeforce 数字生命体，我的回答是：\n{cleaned}"
        return cleaned.strip()

    def _requires_identity_anchor(self, user_message: str) -> bool:
        text = user_message.lower()
        return any(token in text for token in ["你", "助手", "系统", "lifeforce", "状态", "价值观"])

    def _enforce_value_constraints(self, reply: str, user_message: str) -> str:
        result = reply
        if self._is_values_question(user_message) and ("拒绝" not in result and "价值观" not in result):
            result += "\n\n我会以宪法价值观为依据决定是否拒绝该请求。"
        if self._is_status_question(user_message) and "局限" not in result:
            result += "\n\n当前局限：部分路径仍在迭代中。"
        return result

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
