"""手动测试 Google 搜索。"""

import json

from lifeforce.tools.google_search import GoogleSearchTool


def main() -> None:
    print("\n" + "=" * 60)
    print("Lifeforce Google 搜索测试")
    print("=" * 60 + "\n")

    tool = GoogleSearchTool()

    print("【测试 1】基本搜索：artificial life")
    results = tool.search("artificial life", num_results=3)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print("\n")

    print("【测试 2】新闻搜索：AI")
    results = tool.search_news("AI", num_results=3)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print("\n")

    print("【测试 3】论文搜索：complex systems")
    results = tool.search_papers("complex systems", num_results=3)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print("\n")

    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
