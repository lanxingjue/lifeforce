"""记忆写入 Skill。"""

from typing import Any, Dict

from lifeforce.core.memory import MemorySystem
from lifeforce.skills.base import Skill


class MemoryWriteSkill(Skill):
    """将结构化信息写入记忆系统。"""

    def __init__(self, memory: MemorySystem) -> None:
        super().__init__("memory_write")
        self.memory = memory

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        memory_type = params.get("type")
        content = params.get("content")
        importance = params.get("importance", 0.5)
        if not memory_type or content is None:
            raise ValueError("Type and content are required")

        memory_id = self.memory.write(
            {
                "type": memory_type,
                "content": content,
                "importance": importance,
            }
        )
        self.logger.info("Memory written: id=%s type=%s", memory_id, memory_type)
        return {"memory_id": memory_id}
