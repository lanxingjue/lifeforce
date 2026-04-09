"""Shell 执行 Skill。"""

import subprocess
from typing import Any, Dict, List

from lifeforce.skills.base import Skill


class ShellExecSkill(Skill):
    """执行 shell 命令并返回结果。"""

    def __init__(self, config: Any) -> None:
        super().__init__("shell_exec")
        self.config = config
        skills_cfg = getattr(config, "skills", {}) or {}
        shell_cfg = skills_cfg.get("shell_exec", {}) if isinstance(skills_cfg, dict) else {}
        self.safety_check = shell_cfg.get("safety_check", True)
        self.dangerous_commands: List[str] = [
            "rm -rf",
            "mkfs",
            "dd if=",
            "> /dev/",
            ":(){ :|:& };:",
        ]

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        command = params.get("command")
        require_approval = params.get("require_approval", self.safety_check)
        timeout = int(params.get("timeout", 30))
        if not command:
            raise ValueError("No command specified")

        if self.is_dangerous(command) and require_approval:
            self.logger.warning("Dangerous command blocked: %s", command)
            raise PermissionError(f"Dangerous command blocked: {command}")

        self.logger.info("Executing shell command: %s", command)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                shell=True,
                timeout=timeout,
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"Command timeout after {timeout} seconds") from exc

    def is_dangerous(self, command: str) -> bool:
        command_lower = command.lower()
        return any(token in command_lower for token in self.dangerous_commands)

