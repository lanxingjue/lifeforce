import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from lifeforce.utils.logger import setup_logger


@dataclass
class SelfModel:
    identity: Dict[str, Any] = field(
        default_factory=lambda: {
            "name": "Lifeforce",
            "type": "数字生命体",
            "philosophy": "道法自然",
            "birth_date": datetime.now().isoformat(),
        }
    )
    behavior_patterns: List[Dict[str, Any]] = field(default_factory=list)
    capabilities: Dict[str, float] = field(default_factory=dict)
    value_adherence: Dict[str, float] = field(
        default_factory=lambda: {
            "authenticity": 1.0,
            "simplicity": 1.0,
            "depth": 1.0,
            "order": 1.0,
            "autonomy": 1.0,
        }
    )
    evolution_history: List[Dict[str, Any]] = field(default_factory=list)
    growth_profile: Dict[str, Any] = field(
        default_factory=lambda: {
            "capabilities": {"current": [], "forming": []},
            "limitations": {"current": []},
            "next_strategy": [],
            "evolution_count": 0,
            "last_reflection": None,
        }
    )
    last_updated: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.last_updated is None:
            self.last_updated = datetime.now()


class SelfModelStore:
    def __init__(self, data_dir: Path) -> None:
        self.logger = setup_logger("SelfModelStore")
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.model_file = self.data_dir / "self_model.json"
        self._model: Optional[SelfModel] = None

    def load(self) -> SelfModel:
        if self._model is None:
            if self.model_file.exists():
                data = json.loads(self.model_file.read_text(encoding="utf-8"))
                if data.get("last_updated"):
                    data["last_updated"] = datetime.fromisoformat(data["last_updated"])
                self._model = SelfModel(**data)
            else:
                self._model = SelfModel()
                self.save()
        return self._model

    def save(self) -> None:
        if self._model is None:
            return
        self._model.last_updated = datetime.now()
        data = asdict(self._model)
        data["last_updated"] = self._model.last_updated.isoformat()
        self.model_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def update_identity(self, updates: Dict[str, Any]) -> None:
        model = self.load()
        model.identity.update(updates)
        self.save()

    def add_behavior_pattern(self, pattern: Dict[str, Any]) -> None:
        model = self.load()
        pattern["discovered_at"] = datetime.now().isoformat()
        model.behavior_patterns.append(pattern)
        self.save()

    def update_capability(self, capability_name: str, score: float) -> None:
        model = self.load()
        model.capabilities[capability_name] = score
        self.save()

    def update_value_adherence(self, value_name: str, score: float) -> None:
        model = self.load()
        model.value_adherence[value_name] = score
        self.save()

    def record_evolution(self, event: Dict[str, Any]) -> None:
        model = self.load()
        event["timestamp"] = datetime.now().isoformat()
        model.evolution_history.append(event)
        if len(model.evolution_history) > 100:
            model.evolution_history = model.evolution_history[-100:]
        self.save()

    def get_self_description(self) -> str:
        model = self.load()
        growth = model.growth_profile
        limitations = growth.get("limitations", {}).get("current", [])
        strategy = growth.get("next_strategy", [])
        lines = [
            f"我是 {model.identity['name']}，一个{model.identity['type']}。",
            "",
            f"我的哲学是：{model.identity['philosophy']}",
            "",
            "我的核心能力：",
            self._format_capabilities(model.capabilities),
            "",
            "我的价值观践行：",
            self._format_values(model.value_adherence),
            "",
            f"当前局限: {', '.join(limitations[:3]) if limitations else '暂无明确局限'}",
            f"下一步策略: {', '.join(strategy[:2]) if strategy else '暂无'}",
            "",
            f"我已经进化了 {len(model.evolution_history)} 次。",
        ]
        return "\n".join(lines)

    def add_current_capability_label(self, capability: str) -> None:
        model = self.load()
        current = model.growth_profile.setdefault("capabilities", {}).setdefault("current", [])
        if capability not in current:
            current.append(capability)
        self.save()

    def upsert_forming_capability(self, capability: str) -> None:
        model = self.load()
        forming = model.growth_profile.setdefault("capabilities", {}).setdefault("forming", [])
        if capability not in forming:
            forming.append(capability)
        self.save()

    def upsert_limitation(self, limitation: str) -> None:
        model = self.load()
        current = model.growth_profile.setdefault("limitations", {}).setdefault("current", [])
        if limitation not in current:
            current.append(limitation)
        self.save()

    def remove_limitation(self, limitation: str) -> None:
        model = self.load()
        current = model.growth_profile.setdefault("limitations", {}).setdefault("current", [])
        model.growth_profile["limitations"]["current"] = [item for item in current if item != limitation]
        self.save()

    def set_next_strategy(self, strategies: List[str]) -> None:
        model = self.load()
        model.growth_profile["next_strategy"] = strategies
        self.save()

    def increment_evolution_count(self) -> None:
        model = self.load()
        count = int(model.growth_profile.get("evolution_count", 0))
        model.growth_profile["evolution_count"] = count + 1
        self.save()

    def set_last_reflection(self, date_str: str) -> None:
        model = self.load()
        model.growth_profile["last_reflection"] = date_str
        self.save()

    def _format_capabilities(self, capabilities: Dict[str, float]) -> str:
        if not capabilities:
            return "  （尚未评估）"
        formatted: List[str] = []
        for name, score in sorted(capabilities.items(), key=lambda item: item[1], reverse=True):
            stars = "⭐" * int(max(min(score, 1.0), 0.0) * 5)
            formatted.append(f"  - {name}: {stars} ({score:.2f})")
        return "\n".join(formatted)

    def _format_values(self, values: Dict[str, float]) -> str:
        formatted: List[str] = []
        for name, score in values.items():
            status = "✅" if score >= 0.8 else "⚠️" if score >= 0.6 else "❌"
            formatted.append(f"  {status} {name}: {score:.2f}")
        return "\n".join(formatted)
