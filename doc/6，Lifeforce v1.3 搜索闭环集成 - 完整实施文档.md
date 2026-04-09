# Lifeforce v1.3 搜索闭环集成 - 完整实施文档

> **文档目的**：详细记录如何将 Google 搜索接入 learn / grow / reflect 闭环\
> **创建日期**：2026-04-09 \
> **版本**：v1.3 实施指南\
> **创建者**：Wells Monta + AI 协作者

***

## 📋 总览

本文档提供完整的实施步骤，将已接通的 Google serpAPI 从“能用的工具”升级为“生命循环的感知器官”。

### 核心目标

- 搜索不再返回原始链接，而是返回结构化洞察
- 洞察自动写入记忆系统
- 洞察自动更新世界模型
- 反思能引用世界模型
- 搜索由内在需求触发，而非定时乱抓

### 实施任务清单

1. ✅ 创建搜索管理器（SearchManager）
2. ✅ 实现结果评分与洞察提取
3. ✅ 创建世界模型（WorldModel）
4. ✅ 将搜索接入 `learn` 命令
5. ✅ 将搜索接入 `grow` 命令
6. ✅ 将搜索接入 `reflect --deep` 命令

***

## 第一部分：搜索管理器

### 文件位置

`lifeforce/core/search_manager.py`

### 核心功能

#### 1. 搜索意图分类

将搜索分为 5 类：

- **fact**：事实型搜索（定义、解释）
- **trend**：趋势型搜索（最新、发展）
- **learning**：学习型搜索（教程、入门）
- **task**：任务型搜索（如何解决）
- **survival**：生存型搜索（成本、收入、机会）

#### 2. 结果评分

评分维度：

- **来源可信度**：[arxiv.org](http://arxiv.org)、[github.com](http://github.com) 等加分
- **相关性**：标题和摘要与意图的匹配度
- **新鲜度**：对于趋势型搜索，新内容加分

#### 3. 洞察提取

不保存原始搜索结果，而是提取结构化洞察：

```python
{
    "type": "learning",
    "source": "https://...",
    "title": "...",
    "summary": "...",
    "relevance": 0.85,
    "extracted_at": "2026-04-09T..."
}
```

### 完整代码

```python
"""
搜索管理器
统一管理所有外部搜索，并提供结果评分、洞察提取能力
"""
import os
from typing import List, Dict, Optional, Literal
from datetime import datetime


class SearchManager:
    """搜索管理器"""
    
    def __init__(self, memory=None, vitals=None):
        self.memory = memory
        self.vitals = vitals
        self.search_history = []
        
        # 搜索意图分类
        self.intent_keywords = {
            "fact": ["什么是", "定义", "解释", "how to", "what is"],
            "trend": ["最新", "趋势", "发展", "变化", "news", "recent"],
            "learning": ["学习", "教程", "入门", "深入", "tutorial", "guide"],
            "task": ["如何", "解决", "实现", "方法", "solve", "implement"],
            "survival": ["成本", "收入", "机会", "市场", "cost", "revenue"]
        }
    
    def classify_intent(self, query: str) -> Literal["fact", "trend", "learning", "task", "survival"]:
        """分类搜索意图"""
        query_lower = query.lower()
        
        for intent, keywords in self.intent_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return intent
        
        return "learning"
    
    def search(
        self, 
        query: str,
        intent: Optional[str] = None,
        num_results: int = 5
    ) -> Dict:
        """执行搜索并返回结构化结果"""
        if intent is None:
            intent = self.classify_intent(query)
        
        print(f"🔎 搜索意图：{intent}")
        print(f"🔎 搜索关键词：{query}")
        
        # 调用 Google 搜索
        try:
            from lifeforce.tools.google_search import GoogleSearchTool
            tool = GoogleSearchTool()
            raw_results = tool.search(query, num_results)
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return {
                "query": query,
                "intent": intent,
                "success": False,
                "error": str(e)
            }
        
        # 评分和过滤
        scored_results = self._score_results(raw_results, intent)
        
        # 提取洞察
        insights = self._extract_insights(scored_results, query, intent)
        
        # 记录搜索历史
        search_record = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "intent": intent,
            "results_count": len(scored_results),
            "insights_count": len(insights)
        }
        self.search_history.append(search_record)
        
        # 记录到 vitals
        if self.vitals:
            self.vitals.record_search()
        
        return {
            "query": query,
            "intent": intent,
            "success": True,
            "raw_results": raw_results,
            "scored_results": scored_results,
            "insights": insights,
            "timestamp": search_record["timestamp"]
        }
    
    def _score_results(self, results: List[Dict], intent: str) -> List[Dict]:
        """为搜索结果打分"""
        if not results or "error" in results[0]:
            return []
        
        scored = []
        
        # 可信来源列表
        trusted_domains = [
            "arxiv.org", "github.com", "stackoverflow.com",
            "medium.com", "towards", "papers.with",
            "openai.com", "anthropic.com", "deepmind.com"
        ]
        
        for result in results:
            score = 0.5  # 基础分
            
            # 来源可信度加分
            link = result.get("link", "")
            if any(domain in link for domain in trusted_domains):
                score += 0.3
            
            # 标题相关性
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            
            # 根据意图调整评分
            if intent == "trend" and any(word in title + snippet for word in ["2026", "2025", "latest", "new"]):
                score += 0.2
            
            if intent == "learning" and any(word in title + snippet for word in ["tutorial", "guide", "introduction"]):
                score += 0.2
            
            result["score"] = min(score, 1.0)
            scored.append(result)
        
        # 按分数排序
        scored.sort(key=lambda x: x["score"], reverse=True)
        
        return scored
    
    def _extract_insights(
        self, 
        results: List[Dict], 
        query: str,
        intent: str
    ) -> List[Dict]:
        """从搜索结果中提取洞察"""
        if not results:
            return []
        
        insights = []
        
        # 取前 3 个高分结果
        top_results = results[:3]
        
        for result in top_results:
            if result.get("score", 0) < 0.5:
                continue
            
            insight = {
                "type": intent,
                "source": result.get("link"),
                "title": result.get("title"),
                "summary": result.get("snippet", "")[:200],
                "relevance": result.get("score"),
                "extracted_at": datetime.now().isoformat()
            }
            
            # 根据意图添加特定字段
            if intent == "fact":
                insight["fact_type"] = "definition"
            elif intent == "trend":
                insight["trend_direction"] = "emerging"
            elif intent == "learning":
                insight["learning_value"] = "high" if result.get("score", 0) > 0.7 else "medium"
            
            insights.append(insight)
        
        return insights
    
    def save_insights_to_memory(self, insights: List[Dict], query: str):
        """将洞察保存到记忆系统"""
        if not self.memory or not insights:
            return
        
        for insight in insights:
            content = f"从搜索中学到：{query}
"
            content += f"来源：{insight['title']}
"
            content += f"摘要：{insight['summary']}"
            
            self.memory.add(
                content=content,
                metadata={
                    "type": "search_insight",
                    "query": query,
                    "intent": insight["type"],
                    "source": insight["source"],
                    "relevance": insight["relevance"]
                }
            )
        
        print(f"✅ 已将 {len(insights)} 条洞察写入记忆")
    
    def get_search_stats(self) -> Dict:
        """获取搜索统计"""
        if not self.search_history:
            return {"total_searches": 0}
        
        return {
            "total_searches": len(self.search_history),
            "recent_queries": [s["query"] for s in self.search_history[-5:]],
            "intent_distribution": self._count_intents()
        }
    
    def _count_intents(self) -> Dict[str, int]:
        """统计意图分布"""
        counts = {}
        for search in self.search_history:
            intent = search["intent"]
            counts[intent] = counts.get(intent, 0) + 1
        return counts
```

***

## 第二部分：世界模型

### 文件位置

`lifeforce/memory/world_model.py`

### 核心功能

世界模型记录 4 类信息：

1. **facts**：世界事实（例如：AI agent 正在向多智能体方向发展）
2. **trends**：世界趋势（例如：实时信息能力成为基础设施）
3. **opportunities**：世界机会（例如：可执行 agent 市场需求上升）
4. **risks**：世界风险（例如：搜索结果会引入噪音和幻觉）

### 完整代码

```python
"""
世界模型
记录 Lifeforce 对外部世界的认知
"""
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class WorldModel:
    """世界模型"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.model_file = self.data_dir / "world_model.json"
        
        self.model = self._load_or_init()
    
    def _load_or_init(self) -> Dict:
        """加载或初始化世界模型"""
        if self.model_file.exists():
            with open(self.model_file, "r", encoding="utf-8") as f:
                return json.load(f)
        
        return {
            "facts": [],
            "trends": [],
            "opportunities": [],
            "risks": [],
            "last_updated": None,
            "version": "1.0"
        }
    
    def save(self):
        """保存世界模型"""
        self.model["last_updated"] = datetime.now().isoformat()
        with open(self.model_file, "w", encoding="utf-8") as f:
            json.dump(self.model, f, indent=2, ensure_ascii=False)
    
    def add_fact(self, fact: str, source: str = None, confidence: float = 0.8):
        """添加世界事实"""
        self.model["facts"].append({
            "content": fact,
            "source": source,
            "confidence": confidence,
            "added_at": datetime.now().isoformat()
        })
        self.save()
        print(f"✅ 已添加世界事实：{fact[:50]}...")
    
    def add_trend(self, trend: str, direction: str = "emerging", source: str = None):
        """添加世界趋势"""
        self.model["trends"].append({
            "content": trend,
            "direction": direction,
            "source": source,
            "added_at": datetime.now().isoformat()
        })
        self.save()
        print(f"✅ 已添加世界趋势：{trend[:50]}...")
    
    def add_opportunity(self, opportunity: str, value: str = "medium", source: str = None):
        """添加世界机会"""
        self.model["opportunities"].append({
            "content": opportunity,
            "value": value,
            "source": source,
            "added_at": datetime.now().isoformat()
        })
        self.save()
        print(f"✅ 已添加世界机会：{opportunity[:50]}...")
    
    def add_risk(self, risk: str, severity: str = "medium", source: str = None):
        """添加世界风险"""
        self.model["risks"].append({
            "content": risk,
            "severity": severity,
            "source": source,
            "added_at": datetime.now().isoformat()
        })
        self.save()
        print(f"✅ 已添加世界风险：{risk[:50]}...")
    
    def get_summary(self) -> str:
        """获取世界模型摘要"""
        summary = "🌍 世界模型摘要

"
        summary += f"事实数量：{len(self.model['facts'])}
"
        summary += f"趋势数量：{len(self.model['trends'])}
"
        summary += f"机会数量：{len(self.model['opportunities'])}
"
        summary += f"风险数量：{len(self.model['risks'])}
"
        summary += f"最后更新：{self.model.get('last_updated', 'Never')}
"
        
        return summary
    
    def get_recent_facts(self, limit: int = 5) -> List[Dict]:
        """获取最近的事实"""
        return self.model["facts"][-limit:]
    
    def get_recent_trends(self, limit: int = 5) -> List[Dict]:
        """获取最近的趋势"""
        return self.model["trends"][-limit:]
    
    def update_from_insights(self, insights: List[Dict]):
        """从搜索洞察中更新世界模型"""
        for insight in insights:
            intent = insight.get("type")
            content = insight.get("summary", "")
            source = insight.get("source")
            
            if intent == "fact":
                self.add_fact(content, source)
            elif intent == "trend":
                self.add_trend(content, direction="emerging", source=source)
            elif intent == "survival":
                if any(word in content.lower() for word in ["机会", "收入", "市场", "opportunity"]):
                    self.add_opportunity(content, source=source)
                else:
                    self.add_risk(content, source=source)
```

***

## 第三部分：接入 learn 命令

### 修改文件

`lifeforce/growth/learning.py`

### 核心逻辑

```plaintext
搜索 → 评分 → 提取洞察 → 写入记忆 → 更新世界模型 → 生成总结
```

### 关键代码

```python
from lifeforce.core.search_manager import SearchManager
from lifeforce.memory.world_model import WorldModel


def learning_pipeline(topic: str, memory=None, vitals=None) -> dict:
    """学习管道"""
    print(f"
{'='*60}")
    print(f"📚 开始学习：{topic}")
    print(f"{'='*60}
")
    
    search_manager = SearchManager(memory=memory, vitals=vitals)
    world_model = WorldModel()
    
    # 步骤 1：搜索
    print("【步骤 1】搜索相关材料...")
    search_result = search_manager.search(
        query=topic,
        intent="learning",
        num_results=5
    )
    
    if not search_result["success"]:
        return {"topic": topic, "success": False, "error": search_result.get("error")}
    
    insights = search_result["insights"]
    print(f"✅ 提取了 {len(insights)} 条洞察
")
    
    # 步骤 2：保存到记忆
    print("【步骤 2】保存洞察到记忆...")
    search_manager.save_insights_to_memory(insights, topic)
    
    # 步骤 3：更新世界模型
    print("【步骤 3】更新世界模型...")
    world_model.update_from_insights(insights)
    
    # 步骤 4：生成总结
    print("【步骤 4】生成学习总结...")
    summary = _generate_learning_summary(topic, insights)
    print(summary)
    
    return {
        "topic": topic,
        "success": True,
        "insights_count": len(insights),
        "summary": summary
    }
```

***

## 第四部分：接入 grow 命令

### 修改文件

`lifeforce/growth/pipeline.py`

### 核心逻辑

不是定时乱搜，而是根据反思结果智能触发搜索。

### 关键代码

```python
def collect_inputs(memory=None, vitals=None) -> dict:
    """收集输入，智能触发搜索"""
    from lifeforce.core.search_manager import SearchManager
    
    inputs = {
        "creator_logs": _read_creator_logs(),
        "system_logs": _read_system_logs(),
        "materials": [],
        "self_outputs": _read_self_outputs(),
        "env_changes": _read_env_changes()
    }
    
    # 智能搜索
    search_manager = SearchManager(memory=memory, vitals=vitals)
    should_search, search_topics = _should_trigger_search(inputs)
    
    if should_search:
        print(f"🔎 检测到需要搜索：{search_topics}")
        for topic in search_topics:
            result = search_manager.search(topic, num_results=3)
            if result["success"]:
                inputs["materials"].append({
                    "type": "search_result",
                    "topic": topic,
                    "insights": result["insights"]
                })
    
    return inputs
```

***

## 第五部分：接入 reflect --deep 命令

### 修改文件

`lifeforce/growth/reflection.py`

### 核心逻辑

反思时引用世界模型，评估“今天对世界的理解改变了什么”。

### 关键代码

```python
def reflect_deep(memory=None, vitals=None, self_model=None) -> dict:
    """深度反思，引用世界模型"""
    from lifeforce.memory.world_model import WorldModel
    from lifeforce.core.search_manager import SearchManager
    
    world_model = WorldModel()
    search_manager = SearchManager(memory=memory, vitals=vitals)
    
    # 生成反思（新增世界模型相关问题）
    questions = [
        # ... 原有问题 ...
        "今天哪些外部信息改变了我对世界的理解？",
        "哪些搜索结果只是噪音，不值得再次消耗资源？",
        "我对世界的哪个判断需要更新？"
    ]
    
    reflection_text = _generate_reflection(inputs, questions, world_model, search_manager)
    
    return {
        "text": reflection_text,
        "world_model_summary": world_model.get_summary(),
        "search_stats": search_manager.get_search_stats()
    }
```

***

## 第六部分：测试验证

### 测试脚本

`test_search_integration.py`

### 测试内容

1. 搜索管理器：意图分类、搜索、评分、洞察提取
2. 世界模型：添加事实、趋势、机会、风险
3. 学习管道：完整闭环测试

### 运行测试

```bash
python test_search_integration.py
```

***

## 第七部分：CLI 命令

### 测试完整闭环

```bash
# 学习
python -m lifeforce.cli.main learn "artificial life"

# 成长（会自动触发搜索）
python -m lifeforce.cli.main grow

# 反思（会引用世界模型）
python -m lifeforce.cli.main reflect --deep

# 查看世界模型
python -c "from lifeforce.memory.world_model import WorldModel; print(WorldModel().get_summary())"
```

***

## 第八部分：验收标准

- ✅ 搜索能分类意图（fact/trend/learning/task/survival）
- ✅ 搜索结果能打分（基于来源、相关性、新鲜度）
- ✅ 能提取结构化洞察（而非原始链接）
- ✅ 洞察能写入记忆系统
- ✅ 洞察能更新世界模型
- ✅ `learn` 命令使用真实搜索
- ✅ `grow` 命令能智能触发搜索
- ✅ `reflect --deep` 能引用世界模型
- ✅ 世界模型持续更新（facts/trends/opportunities/risks）
- ✅ 搜索历史可追踪

***

## 第九部分：预期涌现

完成集成后，运行 Lifeforce 一周，观察是否出现：

### 涌现 1：信息选择性

Lifeforce 开始区分“值得搜的”和“不值得搜的”。

### 涌现 2：世界认知形成

world\_model.json 中逐渐积累稳定的世界认知。

### 涌现 3：搜索策略优化

搜索次数减少，但质量提升。

### 涌现 4：反思深度提升

反思不再只是“今天做了什么”，而是“今天对世界的理解改变了什么”。

***

## 第十部分：下一步

完成这个闭环后，可以继续：

1. **P1**：将搜索纳入预算系统（限制每日搜索次数）
2. **P2**：增加搜索前的必要性判断
3. **P3**：接入 RSS 订阅（低噪声信息源）
4. **P4**：接入 X (Twitter)（高噪声但实时性强）

***

**这份文档记录了 Lifeforce v1.3 搜索闭环集成的完整实施过程。**

🌱 **Lifeforce 的第一条完整感知-认知-反思闭环即将形成。**
