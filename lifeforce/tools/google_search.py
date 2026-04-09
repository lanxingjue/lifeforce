"""SerpApi 搜索工具（Google 结果）。"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

from lifeforce.utils.logger import setup_logger


class GoogleSearchTool:
    """基于 SerpApi 的 Google 搜索工具。"""

    def __init__(self) -> None:
        self.logger = setup_logger("GoogleSearchTool")
        # 支持独立脚本场景：在未经过 config 初始化时主动加载项目根目录 .env
        load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)
        self.api_key = os.getenv("SERPAPI_API_KEY") or os.getenv("GOOGLE_SEARCH_API_KEY")
        self.base_url = "https://serpapi.com/search.json"

        if not self.api_key:
            self.logger.warning(
                "SerpApi 未配置，请设置 SERPAPI_API_KEY（兼容 GOOGLE_SEARCH_API_KEY）"
            )
            return
        self.logger.info("SerpApi 初始化成功")

    def search(
        self,
        query: str,
        num_results: int = 5,
        date_restrict: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """执行 Google 搜索（通过 SerpApi）。"""
        if not self.api_key:
            return [
                {
                    "error": "SerpApi 未配置",
                    "suggestion": "请在 .env 配置 SERPAPI_API_KEY",
                }
            ]
        try:
            params: Dict[str, str | int] = {
                "engine": "google",
                "q": query,
                "api_key": self.api_key,
                "num": min(num_results, 10),  # SerpApi 也支持 num
            }
            if date_restrict:
                params["tbs"] = self._to_tbs(date_restrict)
            response = httpx.get(self.base_url, params=params, timeout=20.0)
            response.raise_for_status()
            result = response.json()
            items = result.get("organic_results", [])
            results: List[Dict[str, Any]] = [
                {
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                }
                for item in items
            ]
            self.logger.info("搜索成功：query=%s results=%s", query, len(results))
            return results
        except Exception as exc:
            error_msg = f"搜索失败: {exc}"
            self.logger.error(error_msg)
            return [{"error": error_msg, "query": query}]

    def search_news(self, topic: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """搜索近一周新闻。"""
        if not self.api_key:
            return self.search(query=f"{topic} news", num_results=num_results, date_restrict="w1")
        try:
            params: Dict[str, str | int] = {
                "engine": "google",
                "q": f"{topic} news",
                "tbm": "nws",
                "api_key": self.api_key,
                "num": min(num_results, 10),
            }
            response = httpx.get(self.base_url, params=params, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            items = data.get("news_results", [])
            return [
                {
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                }
                for item in items
            ]
        except Exception as exc:
            self.logger.error("新闻搜索失败: %s", exc)
            return [{"error": f"新闻搜索失败: {exc}", "query": topic}]

    def search_papers(self, topic: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """搜索论文/学术资料。"""
        return self.search(
            query=f"{topic} site:arxiv.org OR site:scholar.google.com",
            num_results=num_results,
        )

    @staticmethod
    def _to_tbs(value: str) -> str:
        mapping = {"d1": "qdr:d", "w1": "qdr:w", "m1": "qdr:m", "y1": "qdr:y"}
        return mapping.get(value.strip(), "qdr:w")


def search_google(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """便捷搜索函数。"""
    tool = GoogleSearchTool()
    return tool.search(query=query, num_results=num_results)
