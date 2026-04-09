"""Observer Agent - 观察者。"""

from datetime import datetime
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer as WatchdogObserver

from lifeforce.core.agent import Agent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem
from lifeforce.memory.emergence import EmergenceDetector, EmergenceEvent
from lifeforce.utils.logger import setup_logger


class FileChangeHandler(FileSystemEventHandler):
    """将文件系统事件转发给 ObserverAgent。"""

    def __init__(self, observer_agent: "ObserverAgent") -> None:
        self.observer_agent = observer_agent
        self.logger = setup_logger("FileChangeHandler")

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        if self.observer_agent.should_ignore(event.src_path):
            return
        self.logger.info("File created: %s", event.src_path)
        self.observer_agent.handle_file_change("created", event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        if self.observer_agent.should_ignore(event.src_path):
            return
        self.logger.debug("File modified: %s", event.src_path)
        self.observer_agent.handle_file_change("modified", event.src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        if self.observer_agent.should_ignore(event.src_path):
            return
        self.logger.info("File deleted: %s", event.src_path)
        self.observer_agent.handle_file_change("deleted", event.src_path)


class ObserverAgent(Agent):
    """负责环境感知与变化记录。"""

    def __init__(
        self,
        memory: MemorySystem,
        budget_guard: BudgetGuard,
        watch_paths: Optional[List[str]] = None,
    ) -> None:
        super().__init__(
            name="Observer",
            role="环境感知与信息收集",
            memory=memory,
            budget_guard=budget_guard,
        )
        self.watch_paths = watch_paths or []
        self.watchdog_observer = WatchdogObserver()
        self.is_watching = False
        self.last_events: Dict[str, float] = {}
        self.debounce_seconds = 2.0
        project_internal = str(Path(".lifeforce").resolve()).lower()
        self.ignore_paths = [project_internal]
        self.ignore_suffixes = [".db-journal", ".log"]
        self.emergence_detector = EmergenceDetector(Path(".lifeforce/emergence"), self.genome)

    def start_watching(self, paths: Optional[List[str]] = None) -> None:
        if self.is_watching:
            self.logger.warning("Already watching")
            return

        target_paths = paths or self.watch_paths
        if not target_paths:
            self.logger.warning("No paths to watch")
            return

        event_handler = FileChangeHandler(self)
        scheduled_count = 0
        for path_str in target_paths:
            path = Path(path_str).expanduser()
            if not path.exists():
                self.logger.warning("Path does not exist: %s", path)
                continue
            self.watchdog_observer.schedule(event_handler, str(path), recursive=True)
            self.logger.info("Watching: %s", path)
            scheduled_count += 1

        if scheduled_count == 0:
            self.logger.warning("No valid paths were scheduled")
            return

        self.watchdog_observer.start()
        self.is_watching = True
        self.log_action("start_watching", {"paths": target_paths})

    def stop_watching(self) -> None:
        if not self.is_watching:
            return
        self.watchdog_observer.stop()
        self.watchdog_observer.join()
        self.is_watching = False
        self.log_action("stop_watching", {})
        self.logger.info("Stopped watching")

    def handle_file_change(self, event_type: str, file_path: str) -> None:
        now = time.time()
        key = f"{event_type}:{file_path}"
        if key in self.last_events and (now - self.last_events[key]) < self.debounce_seconds:
            return
        self.last_events[key] = now

        self.memory.write(
            {
                "type": "file_change",
                "event_type": event_type,
                "file_path": file_path,
                "timestamp": datetime.now().isoformat(),
                "importance": 0.7 if event_type == "created" else 0.5,
            }
        )
        self.logger.info("Recorded file change: %s %s", event_type, file_path)

    def should_ignore(self, file_path: str) -> bool:
        normalized = str(Path(file_path)).lower()
        if any(normalized.startswith(ignore_path) for ignore_path in self.ignore_paths):
            return True
        if any(normalized.endswith(suffix) for suffix in self.ignore_suffixes):
            return True
        return False

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        command = message.get("command")
        if command == "start_watching":
            paths = message.get("paths", [])
            self.start_watching(paths)
            return {"status": "watching", "paths": paths}
        if command == "stop_watching":
            self.stop_watching()
            return {"status": "stopped"}
        if command == "get_recent_changes":
            limit = message.get("limit", 10)
            changes = self.memory.read(memory_type="file_change", limit=limit)
            return {"changes": changes}
        if command == "observe_task_result":
            emergence = self.observe_task_result(
                task_id=message.get("task_id", "unknown"),
                agents_involved=message.get("agents_involved", []),
                expected_outcome=message.get("expected_outcome", ""),
                actual_outcome=message.get("actual_outcome", ""),
                context=message.get("context", {}),
            )
            return {"emergence": emergence.to_dict() if emergence else None}
        return {"error": f"Unknown command: {command}"}

    def observe_task_result(
        self,
        task_id: str,
        agents_involved: List[str],
        expected_outcome: str,
        actual_outcome: str,
        context: Dict[str, Any],
    ) -> Optional[EmergenceEvent]:
        emergence = self.emergence_detector.detect(
            agents_involved=agents_involved,
            expected_outcome=expected_outcome,
            actual_outcome=actual_outcome,
            context=context,
        )
        if emergence is not None:
            self.memory.write(
                {
                    "type": "emergence",
                    "task_id": task_id,
                    "emergence": emergence.to_dict(),
                    "importance": 0.8,
                }
            )
        return emergence


# Backward-compatible alias
Observer = ObserverAgent
