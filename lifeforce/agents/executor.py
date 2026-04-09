"""Executor Agent - 执行者。"""

from typing import Any, Dict

from lifeforce.core.agent import Agent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem
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
        skill_name = message.get("skill")
        params = message.get("params", {})
        if not skill_name:
            return {"error": "No skill specified"}
        if skill_name not in self.skills:
            return {"error": f"Unknown skill: {skill_name}"}

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

    def execute_shell(self, command: str, require_approval: bool = True) -> Dict[str, Any]:
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
