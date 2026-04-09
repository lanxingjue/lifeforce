"""世界模型：记录外部认知（facts/trends/opportunities/risks）。"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List


class WorldModel:
    """Lifeforce 的世界认知模型。"""

    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.model_file = self.data_dir / "world_model.json"
        self.model = self._load_or_init()

    def _load_or_init(self) -> Dict[str, Any]:
        if self.model_file.exists():
            raw = json.loads(self.model_file.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return raw
        return {
            "facts": [],
            "trends": [],
            "opportunities": [],
            "risks": [],
            "last_updated": None,
            "version": "1.0",
        }

    def save(self) -> None:
        self.model["last_updated"] = datetime.now().isoformat()
        self.model_file.write_text(json.dumps(self.model, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_fact(self, fact: str, source: str | None = None, confidence: float = 0.8) -> None:
        self.model["facts"].append(
            {"content": fact, "source": source, "confidence": confidence, "added_at": datetime.now().isoformat()}
        )
        self.save()

    def add_trend(self, trend: str, direction: str = "emerging", source: str | None = None) -> None:
        self.model["trends"].append(
            {"content": trend, "direction": direction, "source": source, "added_at": datetime.now().isoformat()}
        )
        self.save()

    def add_opportunity(self, opportunity: str, value: str = "medium", source: str | None = None) -> None:
        self.model["opportunities"].append(
            {"content": opportunity, "value": value, "source": source, "added_at": datetime.now().isoformat()}
        )
        self.save()

    def add_risk(self, risk: str, severity: str = "medium", source: str | None = None) -> None:
        self.model["risks"].append(
            {"content": risk, "severity": severity, "source": source, "added_at": datetime.now().isoformat()}
        )
        self.save()

    def update_from_insights(self, insights: List[Dict[str, Any]]) -> None:
        for insight in insights:
            intent = str(insight.get("type", "learning"))
            content = str(insight.get("summary") or insight.get("title") or "").strip()
            source = str(insight.get("source")) if insight.get("source") else None
            relevance = float(insight.get("relevance", 0.5) or 0.5)
            if not content:
                continue

            if intent == "trend":
                self.add_trend(content, source=source)
            elif intent == "survival":
                lower = content.lower()
                if any(word in lower for word in ["opportunity", "growth", "market", "demand", "机会", "增长", "需求"]):
                    self.add_opportunity(content, source=source)
                elif any(word in lower for word in ["risk", "threat", "cost", "危机", "风险", "成本"]):
                    self.add_risk(content, source=source)
                else:
                    self.add_fact(content, source=source, confidence=relevance)
            else:
                self.add_fact(content, source=source, confidence=relevance)

    def get_summary(self) -> str:
        self.model = self._load_or_init()
        return (
            "世界模型摘要\n"
            f"- facts: {len(self.model['facts'])}\n"
            f"- trends: {len(self.model['trends'])}\n"
            f"- opportunities: {len(self.model['opportunities'])}\n"
            f"- risks: {len(self.model['risks'])}\n"
            f"- last_updated: {self.model.get('last_updated')}"
        )

    def get_recent_facts(self, limit: int = 5) -> List[Dict[str, Any]]:
        raw = self.model.get("facts", [])
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)][-limit:]
        return []

    def get_recent_trends(self, limit: int = 5) -> List[Dict[str, Any]]:
        raw = self.model.get("trends", [])
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)][-limit:]
        return []
