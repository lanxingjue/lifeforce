"""SerpApi 搜索工具测试。"""

from typing import Any, Dict, List

from lifeforce.tools.google_search import GoogleSearchTool, search_google


def test_google_search_tool_init() -> None:
    tool = GoogleSearchTool()
    assert tool is not None


def test_google_search_without_config_returns_hint(monkeypatch) -> None:
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_SEARCH_API_KEY", raising=False)
    tool = GoogleSearchTool()
    results = tool.search("artificial life", num_results=3)
    assert isinstance(results, list)
    assert "error" in results[0]


def test_google_search_with_mock_service(monkeypatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")

    class _Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> Dict[str, List[Dict[str, str]]]:
            return {
                "organic_results": [
                    {"title": "A", "link": "https://a", "snippet": "sa"},
                    {"title": "B", "link": "https://b", "snippet": "sb"},
                ]
            }

    monkeypatch.setattr("lifeforce.tools.google_search.httpx.get", lambda *args, **kwargs: _Response())
    tool = GoogleSearchTool()
    results = tool.search("digital life", num_results=2)
    assert len(results) == 2
    assert "title" in results[0]
    assert "link" in results[0]
    assert "snippet" in results[0]


def test_google_search_news_and_papers(monkeypatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")

    class _Response:
        def __init__(self, payload: Dict[str, List[Dict[str, str]]]) -> None:
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> Dict[str, List[Dict[str, str]]]:
            return self._payload

    def _mock_get(*args: Any, **kwargs: Any) -> _Response:
        params = kwargs.get("params", {})
        if params.get("tbm") == "nws":
            return _Response({"news_results": [{"title": "N", "link": "https://n", "snippet": "sn"}]})
        return _Response({"organic_results": [{"title": "P", "link": "https://p", "snippet": "sp"}]})

    monkeypatch.setattr("lifeforce.tools.google_search.httpx.get", _mock_get)
    tool = GoogleSearchTool()
    assert tool.search_news("AI", num_results=1)
    assert tool.search_papers("complex systems", num_results=1)


def test_search_google_convenience_function(monkeypatch) -> None:
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_SEARCH_API_KEY", raising=False)
    results = search_google("digital life", num_results=2)
    assert isinstance(results, list)
    assert len(results) > 0
