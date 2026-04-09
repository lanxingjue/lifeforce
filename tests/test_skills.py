from pathlib import Path

from lifeforce.core.memory import MemorySystem
from lifeforce.skills.memory_write import MemoryWriteSkill
from lifeforce.skills.shell_exec import ShellExecSkill


class MockConfig:
    skills = {"shell_exec": {"safety_check": True}}


def test_memory_write_skill() -> None:
    db_path = Path(".lifeforce/test_skill_memory.db")
    db_path.parent.mkdir(exist_ok=True)
    memory = MemorySystem(str(db_path))
    try:
        skill = MemoryWriteSkill(memory)
        result = skill.execute({"type": "note", "content": {"message": "hello"}})
        assert result["memory_id"] > 0
    finally:
        memory.close()
        db_path.unlink(missing_ok=True)


def test_shell_exec_skill_blocks_dangerous_command() -> None:
    skill = ShellExecSkill(MockConfig())
    try:
        skill.execute({"command": "rm -rf /", "require_approval": True})
        assert False, "Expected PermissionError"
    except PermissionError:
        assert True

