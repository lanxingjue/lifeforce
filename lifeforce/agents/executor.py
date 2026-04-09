"""Executor Agent - 执行者。"""

from typing import Any, Dict, List

from lifeforce.core.agent import Agent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem
from lifeforce.genome.chaos_edge import inject_randomness
from lifeforce.skills.llm_call import LLMCallSkill
from lifeforce.skills.memory_write import MemoryWriteSkill
from lifeforce.skills.shell_exec import ShellExecSkill


class ExecutorAgent(Agent):
    """负责执行具体任务并记录执行经验。"""

    def __init__(
        self,
        memory: MemorySystem,
        budget_guard: BudgetGuard,
        config: Any,
    ) -> None:
        """初始化执行器并注册内置技能。"""
        super().__init__(
            name="Executor",
            role="具体任务执行",
            memory=memory,
            budget_guard=budget_guard,
        )
        self.config = config
        self.skills = {
            "shell_exec": ShellExecSkill(config),
            "llm_call": LLMCallSkill(config),
            "memory_write": MemoryWriteSkill(memory),
        }
        self.logger.info("Executor initialized with %s skills", len(self.skills))

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理执行请求并选择最终技能。"""
        skill_name = message.get("skill")
        params = message.get("params", {})
        if skill_name and skill_name not in self.skills:
            return {"error": f"Unknown skill: {skill_name}"}
        if not skill_name:
            selected_skills = self.select_skills(message)
            if not selected_skills:
                return {"error": "No available skill selected"}
            skill_name = selected_skills[0]
            self.logger.info("ChaosEdge selected skill=%s", skill_name)

        self.log_action("execute_skill", {"skill": skill_name, "params": params})
        try:
            result = self.skills[skill_name].execute(params)
            self.log_action("skill_completed", {"skill": skill_name, "result": result})
            # Reflective memory: capture successful execution pattern as experience.
            self.memory.write(
                {
                    "type": "execution_experience",
                    "skill": skill_name,
                    "status": "success",
                    "summary": f"Skill {skill_name} executed successfully",
                    "importance": 0.6,
                }
            )
            return {"status": "success", "result": result}
        except Exception as exc:
            self.logger.error("Error executing skill %s: %s", skill_name, exc)
            self.log_action("skill_failed", {"skill": skill_name, "error": str(exc)})
            self.memory.write(
                {
                    "type": "execution_experience",
                    "skill": skill_name,
                    "status": "failed",
                    "summary": str(exc),
                    "importance": 0.7,
                }
            )
            return {"status": "error", "error": str(exc)}

    def select_skills(self, task: Dict[str, Any]) -> List[str]:
        """根据任务候选并注入随机性，返回按优先级排列的技能列表。"""
        explicit_candidates = task.get("candidate_skills", [])
        selected_candidates: List[str]
        if explicit_candidates:
            selected_candidates = [name for name in explicit_candidates if name in self.skills]
        else:
            text = str(task.get("intent", "") or task.get("content", "") or "").lower()
            selected_candidates = []
            if any(token in text for token in ["shell", "command", "cmd", "terminal"]):
                selected_candidates.append("shell_exec")
            if any(token in text for token in ["remember", "memory", "记录", "记忆"]):
                selected_candidates.append("memory_write")
            if any(token in text for token in ["llm", "chat", "reply", "模型", "对话"]):
                selected_candidates.append("llm_call")
            if not selected_candidates:
                selected_candidates = list(self.skills.keys())
        ordered = inject_randomness(selected_candidates, top_k=3)
        return ordered

    def execute_shell(self, command: str, require_approval: bool = True) -> Dict[str, Any]:
        """快捷执行 shell 命令。"""
        return self.process(
            {
                "skill": "shell_exec",
                "params": {
                    "command": command,
                    "require_approval": require_approval,
                },
            }
        )


# Backward-compatible alias
Executor = ExecutorAgent
