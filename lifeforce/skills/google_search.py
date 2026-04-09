"""Google 搜索 Skill。"""

from typing import Any, Dict

from lifeforce.skills.base import Skill
from lifeforce.tools.google_search import GoogleSearchTool


class GoogleSearchSkill(Skill):
    """将 Google 搜索能力接入 Executor 的 Skill 包装。"""

    def __init__(self) -> None:
        super().__init__(name="google_search")
        self.tool = GoogleSearchTool()

    def execute(self, params: Dict[str, Any]) -> Any:
        query = str(params.get("query", "")).strip()
        if not query:
            return {"error": "query 不能为空"}
        num_results = int(params.get("num_results", 5))
        mode = str(params.get("mode", "web")).lower()
        if mode == "news":
            return self.tool.search_news(query, num_results=num_results)
        if mode == "papers":
            return self.tool.search_papers(query, num_results=num_results)
        return self.tool.search(query, num_results=num_results)
