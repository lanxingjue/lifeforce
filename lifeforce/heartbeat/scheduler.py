import threading
import time
from typing import Optional

from lifeforce.heartbeat.core import CoreHeartbeat
from lifeforce.heartbeat.vitals import Vitals
from lifeforce.utils.logger import setup_logger


class HeartbeatScheduler:
    def __init__(self, heartbeat: CoreHeartbeat) -> None:
        self.heartbeat = heartbeat
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self.logger = setup_logger("HeartbeatScheduler")

    def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self.heartbeat.start()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.logger.info("🚀 Heartbeat scheduler started")

    def stop(self) -> None:
        if not self.is_running:
            return
        self.is_running = False
        self.heartbeat.stop()
        if self._thread:
            self._thread.join(timeout=5.0)
        self.logger.info("🛑 Heartbeat scheduler stopped")

    def _run(self) -> None:
        while self.is_running:
            try:
                self.heartbeat.beat()
            except Exception as exc:
                self.logger.error("Heartbeat loop error: %s", exc)
            time.sleep(1.0)

    def get_vitals(self) -> Vitals:
        return self.heartbeat.get_vitals()
