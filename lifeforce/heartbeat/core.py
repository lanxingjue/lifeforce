from datetime import datetime
from typing import Any

from lifeforce.heartbeat.vitals import Vitals
from lifeforce.utils.logger import setup_logger


class CoreHeartbeat:
    def __init__(self, memory_system: Any, budget_guard: Any) -> None:
        self.memory = memory_system
        self.budget_guard = budget_guard
        self.vitals = Vitals()
        self.start_time = datetime.now()
        self.is_running = False
        self.logger = setup_logger("Heartbeat")

    def beat(self) -> None:
        self.vitals.beat_count += 1
        self.vitals.last_beat = datetime.now()
        self.vitals.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        self._refresh_health()
        if self.vitals.beat_count % 60 == 0:
            self._persist_vitals()
            self.logger.info(
                "💓 Beat #%s | Health: %s | Uptime: %.0fs",
                self.vitals.beat_count,
                self.vitals.health_status,
                self.vitals.uptime_seconds,
            )

    def _refresh_health(self) -> None:
        try:
            self.memory.read(limit=1)
            usage = self.budget_guard.get_usage()
            remaining = usage["hourly"]["remaining"]
            self.vitals.tokens_used = usage["hourly"]["used"]
            self.vitals.tokens_available = remaining
            self.vitals.health_status = "healthy" if remaining > 50 else "degraded"
        except Exception:
            self.vitals.health_status = "critical"

    def _persist_vitals(self) -> None:
        self.memory.write(
            {
                "type": "heartbeat",
                "vitals": self.vitals.to_dict(),
                "timestamp": datetime.now().isoformat(),
                "importance": 0.4,
            }
        )

    def start(self) -> None:
        self.is_running = True
        self.start_time = datetime.now()
        self.logger.info("💚 Heartbeat started")

    def stop(self) -> None:
        self.is_running = False
        self.logger.info("💔 Heartbeat stopped")

    def get_vitals(self) -> Vitals:
        return self.vitals
