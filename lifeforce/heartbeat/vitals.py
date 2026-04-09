from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Vitals:
    uptime_seconds: float = 0.0
    beat_count: int = 0
    last_beat: Optional[datetime] = None
    health_status: str = "healthy"
    tokens_used: int = 0
    tokens_available: int = 0
    memory_usage_mb: float = 0.0
    tasks_completed: int = 0
    tasks_failed: int = 0
    skills_executed: int = 0
    memories_count: int = 0
    memories_added_today: int = 0
    emergences_detected: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uptime_seconds": self.uptime_seconds,
            "beat_count": self.beat_count,
            "last_beat": self.last_beat.isoformat() if self.last_beat else None,
            "health_status": self.health_status,
            "tokens_used": self.tokens_used,
            "tokens_available": self.tokens_available,
            "memory_usage_mb": self.memory_usage_mb,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "skills_executed": self.skills_executed,
            "memories_count": self.memories_count,
            "memories_added_today": self.memories_added_today,
            "emergences_detected": self.emergences_detected,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Vitals":
        copied = dict(data)
        if copied.get("last_beat"):
            copied["last_beat"] = datetime.fromisoformat(copied["last_beat"])
        return cls(**copied)
