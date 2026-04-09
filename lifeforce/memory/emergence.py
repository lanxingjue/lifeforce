import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from lifeforce.utils.logger import setup_logger


@dataclass
class EmergenceEvent:
    event_id: str
    event_type: str
    description: str
    agents_involved: List[str]
    expected_outcome: str
    actual_outcome: str
    surprise_score: float
    value_score: float
    discovered_at: datetime
    crystallized: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["discovered_at"] = self.discovered_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmergenceEvent":
        copied = dict(data)
        copied["discovered_at"] = datetime.fromisoformat(copied["discovered_at"])
        return cls(**copied)


class EmergenceDetector:
    def __init__(self, data_dir: Path, genome: Any) -> None:
        self.logger = setup_logger("EmergenceDetector")
        self.data_dir = data_dir
        self.genome = genome
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = self.data_dir / "emergence_events.json"
        gene = genome.behavioral_genes.get("emergence_detection", {})
        params = gene.get("initial_parameters", {})
        self.surprise_threshold = float(params.get("surprise_threshold", 0.7))
        self.synergy_detection = bool(params.get("synergy_detection", True))
        self._events: List[EmergenceEvent] = []
        self._load_events()

    def _load_events(self) -> None:
        if self.events_file.exists():
            raw = json.loads(self.events_file.read_text(encoding="utf-8"))
            self._events = [EmergenceEvent.from_dict(item) for item in raw]

    def _save_events(self) -> None:
        payload = [item.to_dict() for item in self._events]
        self.events_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def detect(
        self,
        agents_involved: List[str],
        expected_outcome: str,
        actual_outcome: str,
        context: Dict[str, Any],
    ) -> Optional[EmergenceEvent]:
        surprise_score = self._calculate_surprise(expected_outcome, actual_outcome)
        if surprise_score < self.surprise_threshold:
            return None
        event_type = self._classify_emergence(agents_involved, context)
        value_score = self._evaluate_value(context)
        event = EmergenceEvent(
            event_id=f"emergence_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            event_type=event_type,
            description=f"意外发现：{actual_outcome}",
            agents_involved=agents_involved,
            expected_outcome=expected_outcome,
            actual_outcome=actual_outcome,
            surprise_score=surprise_score,
            value_score=value_score,
            discovered_at=datetime.now(),
        )
        self._events.append(event)
        self._save_events()
        self.logger.info(
            "✨ Emergence detected! Type: %s, Surprise: %.2f, Value: %.2f",
            event_type,
            surprise_score,
            value_score,
        )
        return event

    def _calculate_surprise(self, expected: str, actual: str) -> float:
        if expected == actual:
            return 0.0
        max_len = max(len(expected), len(actual), 1)
        diff = abs(len(expected) - len(actual))
        return min(1.0, diff / max_len)

    def _classify_emergence(self, agents: List[str], context: Dict[str, Any]) -> str:
        if len(agents) > 1 and self.synergy_detection:
            return "synergy"
        if context.get("is_novel"):
            return "novel_behavior"
        return "self_organization"

    def _evaluate_value(self, context: Dict[str, Any]) -> float:
        if context.get("success"):
            return 0.9
        if context.get("partial_success"):
            return 0.6
        return 0.3

    def get_recent_emergences(self, limit: int = 10) -> List[EmergenceEvent]:
        return sorted(self._events, key=lambda item: item.discovered_at, reverse=True)[:limit]

    def get_valuable_emergences(self, min_value: float = 0.7) -> List[EmergenceEvent]:
        return [item for item in self._events if item.value_score >= min_value]

    def crystallize_emergence(self, event_id: str) -> bool:
        event = next((item for item in self._events if item.event_id == event_id), None)
        if event is None or event.crystallized:
            return False
        event.crystallized = True
        self._save_events()
        return True
