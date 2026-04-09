"""搜索管理器：意图分类、评分、洞察提取、记忆写入。"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from lifeforce.memory.world_model import WorldModel
from lifeforce.tools.google_search import GoogleSearchTool
from lifeforce.utils.logger import setup_logger


SearchIntent = Literal["fact", "trend", "learning", "task", "survival"]


class SearchManager:
    """统一管理外部搜索并输出结构化洞察。"""

    def __init__(
        self,
        memory: Any = None,
        vitals: Any = None,
        world_model: Optional[WorldModel] = None,
        data_dir: str = "data",
    ) -> None:
        self.memory = memory
        self.vitals = vitals
        self.world_model = world_model
        self.logger = setup_logger("SearchManager")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.stats_file = self.data_dir / "search_stats.json"
        self.search_stats = self._load_search_stats()
        self.intent_keywords: Dict[str, List[str]] = {
            "fact": ["什么是", "定义", "解释", "what is", "definition"],
            "trend": ["最新", "趋势", "发展", "变化", "news", "recent"],
            "learning": ["学习", "教程", "入门", "深入", "tutorial", "guide"],
            "task": ["如何", "解决", "实现", "方法", "solve", "implement"],
            "survival": ["成本", "收入", "机会", "市场", "cost", "revenue"],
        }

    def classify_intent(self, query: str) -> SearchIntent:
        query_lower = query.lower()
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return intent  # type: ignore[return-value]
        return "learning"

    def search(
        self,
        query: str,
        intent: Optional[str] = None,
        num_results: int = 5,
    ) -> Dict[str, Any]:
        inferred_intent = (intent or self.classify_intent(query))  # type: ignore[assignment]
        try:
            tool = GoogleSearchTool()
            raw_results = tool.search(query=query, num_results=num_results)
        except Exception as exc:
            self.logger.error("搜索失败: %s", exc)
            return {"query": query, "intent": inferred_intent, "success": False, "error": str(exc)}

        if raw_results and isinstance(raw_results[0], dict) and raw_results[0].get("error"):
            return {
                "query": query,
                "intent": inferred_intent,
                "success": False,
                "error": str(raw_results[0].get("error")),
                "raw_results": raw_results,
            }

        scored_results = self._score_results(raw_results, str(inferred_intent))
        insights = self._extract_insights(scored_results, query, str(inferred_intent))
        self._record_search(query=query, intent=str(inferred_intent))
        return {
            "query": query,
            "intent": inferred_intent,
            "success": True,
            "raw_results": raw_results,
            "scored_results": scored_results,
            "insights": insights,
            "timestamp": datetime.now().isoformat(),
        }

    def _score_results(self, results: List[Dict[str, Any]], intent: str) -> List[Dict[str, Any]]:
        trusted_domains = [
            "arxiv.org",
            "github.com",
            "stackoverflow.com",
            "openai.com",
            "anthropic.com",
            "deepmind.com",
        ]
        scored: List[Dict[str, Any]] = []
        for result in results:
            score = 0.5
            link = str(result.get("link", ""))
            title = str(result.get("title", "")).lower()
            snippet = str(result.get("snippet", "")).lower()
            if any(domain in link for domain in trusted_domains):
                score += 0.3
            if intent == "trend" and any(word in (title + snippet) for word in ["2026", "latest", "new", "recent"]):
                score += 0.2
            if intent == "learning" and any(word in (title + snippet) for word in ["tutorial", "guide", "introduction"]):
                score += 0.2
            copied = dict(result)
            copied["score"] = min(score, 1.0)
            scored.append(copied)
        scored.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)
        return scored

    def _extract_insights(self, results: List[Dict[str, Any]], query: str, intent: str) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        for result in results[:3]:
            if float(result.get("score", 0.0)) < 0.5:
                continue
            insight: Dict[str, Any] = {
                "type": intent,
                "query": query,
                "source": result.get("link"),
                "title": result.get("title"),
                "summary": str(result.get("snippet", ""))[:200],
                "relevance": float(result.get("score", 0.5)),
                "extracted_at": datetime.now().isoformat(),
            }
            insights.append(insight)
        return insights

    def save_insights_to_memory(self, insights: List[Dict[str, Any]], query: str) -> None:
        if self.memory and hasattr(self.memory, "write"):
            for insight in insights:
                record = {
                    "type": "search_insight",
                    "query": query,
                    "content": insight,
                    "importance": max(0.6, float(insight.get("relevance", 0.6))),
                    "metadata": {
                        "intent": insight.get("type"),
                        "source": insight.get("source"),
                    },
                }
                self.memory.write(record)
            print(f"✅ 已将 {len(insights)} 条洞察写入记忆")

        if self.world_model is not None:
            self.world_model.update_from_insights(insights)
            print(f"✅ 已将 {len(insights)} 条洞察更新到世界模型")

    def get_search_stats(self) -> Dict[str, Any]:
        self.search_stats = self._load_search_stats()
        return self.search_stats

    def _load_search_stats(self) -> Dict[str, Any]:
        default = {"total_searches": 0, "recent_queries": [], "intent_distribution": {}}
        if not self.stats_file.exists():
            return default
        try:
            raw = json.loads(self.stats_file.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                total = int(raw.get("total_searches", 0) or 0)
                recent_raw = raw.get("recent_queries", [])
                recent = [str(item) for item in recent_raw][-5:] if isinstance(recent_raw, list) else []
                dist_raw = raw.get("intent_distribution", {})
                distribution: Dict[str, int] = {}
                if isinstance(dist_raw, dict):
                    for key, value in dist_raw.items():
                        distribution[str(key)] = int(value or 0)
                return {"total_searches": total, "recent_queries": recent, "intent_distribution": distribution}
        except Exception as exc:
            self.logger.warning("读取 search_stats 失败，回退默认值: %s", exc)
        return default

    def _save_search_stats(self) -> None:
        self.stats_file.write_text(json.dumps(self.search_stats, ensure_ascii=False, indent=2), encoding="utf-8")

    def _record_search(self, query: str, intent: str) -> None:
        self.search_stats["total_searches"] = int(self.search_stats.get("total_searches", 0)) + 1
        recent = self.search_stats.get("recent_queries", [])
        if not isinstance(recent, list):
            recent = []
        recent.append(query)
        self.search_stats["recent_queries"] = [str(item) for item in recent][-5:]
        dist = self.search_stats.get("intent_distribution", {})
        if not isinstance(dist, dict):
            dist = {}
        dist[intent] = int(dist.get(intent, 0)) + 1
        self.search_stats["intent_distribution"] = dist
        self._save_search_stats()
