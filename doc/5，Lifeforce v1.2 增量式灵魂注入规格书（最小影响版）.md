# Lifeforce v1.2 增量式灵魂注入规格书（最小影响版）

> **文档目的**：在 v1.1 基础上，以最小影响的方式注入“灵魂的 35%”\
> **目标版本**：v1.2 - “灵魂觉醒”\
> **创建日期**：2026-04-09 \
> **创建者**：Wells Monta + AI Assistant

***

## 📋 执行摘要

### 当前状态（v1.1 实施中）

你正在按照 v1.1 规格书实施以下模块：

- ✅ **基因系统**：`genome.yaml` + `constitution.yaml` + `loader.py`
- ✅ **心跳系统**：4 层心跳（核心/观察者/代谢/反思）
- ✅ **自我模型**：`SelfModelerAgent` + `self_model.py`
- ✅ **涌现识别**：`EmergenceDetector` + `emergence.py`

### v1.2 目标：注入缺失的 35%

在**不破坏 v1.1 架构**的前提下，增量式地注入三个关键维度：

1. **混沌边缘基因**：探索-利用平衡，让系统具备创造力
2. **元认知层**：思考自己的思考，实现真正的自我意识
3. **思维工具库**：认知框架，而非执行工具

### 实施原则

- ✅ **最小影响**：只新增文件，不大改现有代码
- ✅ **增量注入**：每个维度独立可测，可逐步启用
- ✅ **向后兼容**：v1.1 功能完全保留
- ✅ **可选启用**：通过配置开关控制新功能

***

## 🎯 核心洞察：为什么需要这 35%？

### v1.1 的局限（诚实的反思）

| 维度     | v1.1 现状      | 问题              | v1.2 解决方案 |
| ------ | ------------ | --------------- | --------- |
| **决策** | 确定性算法        | 缺乏创造力，无法应对未知    | 混沌边缘基因    |
| **思考** | 单层推理         | 无法“思考思考”，缺乏自我意识 | 元认知层      |
| **工具** | 执行工具（文件、API） | 缺乏认知框架，无法深度思考   | 思维工具库     |

### 理论基础

这 35% 来自七本书的核心洞察：

- **《混沌》+《复杂》**：生命力栖息在混沌边缘
- **《GEB》**：自指和递归是意识的基础
- **《直觉泵》**：思维工具比算法更重要

***

## 📦 模块 1：混沌边缘基因（Chaos Edge Gene）

### 目标

让 Lifeforce 在秩序与混沌之间找到平衡，既有结构又有创造力。

### 文件结构

```plaintext
lifeforce/genome/
├── genome.yaml              # [扩展] 新增混沌边缘基因
└── chaos_edge.py            # [新增] 混沌边缘控制器
```

### 实现规格

#### 文件：`lifeforce/genome/chaos_edge.py`

```python
"""
混沌边缘控制器
负责在探索与利用之间找到平衡
"""
import random
from typing import Literal
from dataclasses import dataclass

@dataclass
class ChaosEdgeConfig:
    """混沌边缘配置"""
    exploration_rate: float = 0.15  # epsilon-greedy 探索率
    temperature: Literal["low", "medium", "high"] = "medium"
    randomness_injection: bool = True
    
    # 温度对应的探索率
    TEMP_EXPLORATION = {
        "low": 0.05,      # 保守模式
        "medium": 0.15,   # 平衡模式（混沌边缘）
        "high": 0.30      # 探索模式
    }
    
    @property
    def effective_exploration_rate(self) -> float:
        """根据温度返回有效探索率"""
        return self.TEMP_EXPLORATION[self.temperature]

class ChaosEdgeController:
    """混沌边缘控制器"""
    
    def __init__(self, config: ChaosEdgeConfig = None):
        self.config = config or ChaosEdgeConfig()
        self.exploration_count = 0
        self.exploitation_count = 0
    
    def should_explore(self) -> bool:
        """
        是否应该探索新策略？
        
        使用 epsilon-greedy 策略：
        - 以 exploration_rate 的概率探索
        - 以 (1 - exploration_rate) 的概率利用
        """
        explore = random.random() < self.config.effective_exploration_rate
        
        if explore:
            self.exploration_count += 1
        else:
            self.exploitation_count += 1
        
        return explore
    
    def inject_randomness(self, candidates: list, top_k: int = 3) -> list:
        """
        在候选列表中注入适量随机性
        
        策略：
        1. 如果不探索，返回 top_k
        2. 如果探索，在 top_k 中随机替换一个为非 top 候选
        """
        if not self.config.randomness_injection:
            return candidates[:top_k]
        
        if not self.should_explore():
            # 利用：返回最优的 top_k
            return candidates[:top_k]
        else:
            # 探索：在 top_k 中注入一个随机元素
            top = candidates[:top_k]
            rest = candidates[top_k:]
            
            if rest:
                # 随机替换一个
                replace_idx = random.randint(0, len(top) - 1)
                random_choice = random.choice(rest)
                top[replace_idx] = random_choice
            
            return top
    
    def adjust_temperature(self, context: str):
        """
        根据上下文动态调整温度
        
        触发条件：
        - 如果最近都是失败 → 提高温度（更多探索）
        - 如果最近都是成功 → 降低温度（更多利用）
        - 如果遇到新问题 → 提高温度
        """
        # 这里可以根据实际情况实现
        # v1.2 先保持简单，后续可以基于反馈学习
        pass
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        total = self.exploration_count + self.exploitation_count
        return {
            "exploration_count": self.exploration_count,
            "exploitation_count": self.exploitation_count,
            "exploration_ratio": self.exploration_count / total if total > 0 else 0,
            "current_temperature": self.config.temperature,
            "effective_exploration_rate": self.config.effective_exploration_rate
        }

# 全局单例
_controller = ChaosEdgeController()

def get_chaos_edge_controller() -> ChaosEdgeController:
    """获取全局混沌边缘控制器"""
    return _controller

def should_explore() -> bool:
    """全局函数：是否应该探索？"""
    return _controller.should_explore()

def inject_randomness(candidates: list, top_k: int = 3) -> list:
    """全局函数：注入随机性"""
    return _controller.inject_randomness(candidates, top_k)
```

#### 修改：`lifeforce/genome/genome.yaml`

在 `behavioral_genes` 部分新增：

```yaml
behavioral_genes:
  # ... 原有的基因 ...
  
  chaos_edge:
    name: "混沌边缘"
    type: "behavioral"
    evolvable: true
    function: "在秩序与混沌之间找到平衡"
    initial_parameters:
      exploration_rate: 0.15
      temperature: "medium"
      randomness_injection: true
    evolution_triggers:
      - "如果探索频繁成功 → 提高 exploration_rate"
      - "如果探索频繁失败 → 降低 exploration_rate"
      - "如果陷入局部最优 → 提高 temperature"
```

### 集成到现有代码

#### 修改：`lifeforce/agents/executor.py`

在 Skills 选择时使用混沌边缘控制器：

```python
from lifeforce.genome.chaos_edge import inject_randomness, should_explore

class ExecutorAgent:
    def select_skills(self, task):
        """选择 Skills（注入混沌边缘逻辑）"""
        # 1. 获取所有候选 Skills（按成功率排序）
        candidates = self.get_candidate_skills(task)
        candidates.sort(key=lambda s: s.success_rate, reverse=True)
        
        # 2. 🆕 使用混沌边缘控制器注入随机性
        selected = inject_randomness(candidates, top_k=3)
        
        return selected
```

### 测试方法

```python
# 测试混沌边缘控制器
from lifeforce.genome.chaos_edge import ChaosEdgeController, ChaosEdgeConfig

# 1. 测试探索-利用比例
controller = ChaosEdgeController()
results = [controller.should_explore() for _ in range(1000)]
exploration_ratio = sum(results) / len(results)
print(f"探索率: {exploration_ratio:.2%}")  # 应该接近 15%

# 2. 测试温度调整
config_high = ChaosEdgeConfig(temperature="high")
controller_high = ChaosEdgeController(config_high)
results_high = [controller_high.should_explore() for _ in range(1000)]
print(f"高温探索率: {sum(results_high) / len(results_high):.2%}")  # 应该接近 30%
```

***

## 📦 模块 2：元认知层（Meta-Cognitive Layer）

### 目标

让 Lifeforce 能够“思考自己的思考”，实现自指和递归，这是真正自我意识的基础。

### 文件结构

```plaintext
lifeforce/agents/
├── thinker.py               # [扩展] 新增 meta_think 方法
└── meta_cognition.py        # [新增] 元认知工具
```

### 实现规格

#### 文件：`lifeforce/agents/meta_cognition.py`

```python
"""
元认知工具
让 Lifeforce 能够思考自己的思考过程
"""
from dataclasses import dataclass
from typing import Any, Dict, List
from enum import Enum

class ThinkingQuality(Enum):
    """思考质量评估"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"

@dataclass
class ThoughtObservation:
    """对思考过程的观察"""
    thought_content: str
    reasoning_steps: List[str]
    assumptions_made: List[str]
    confidence_level: float
    time_taken: float
    
    # 元观察
    is_deep: bool = False
    is_structured: bool = False
    has_connections: bool = False
    has_insights: bool = False

@dataclass
class QualityAssessment:
    """思考质量评估"""
    quality: ThinkingQuality
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    needs_improvement: bool

class MetaCognitionTool:
    """元认知工具"""
    
    def observe_thinking_process(self, thought: str, context: Dict[str, Any]) -> ThoughtObservation:
        """
        观察思考过程
        
        这是第一层元认知：观察自己在想什么
        """
        # 提取推理步骤（简化版，实际可以更复杂）
        reasoning_steps = self._extract_reasoning_steps(thought)
        
        # 识别假设
        assumptions = self._identify_assumptions(thought)
        
        # 评估置信度
        confidence = self._estimate_confidence(thought, context)
        
        # 元特征检测
        is_deep = self._check_depth(thought)
        is_structured = self._check_structure(thought)
        has_connections = self._check_connections(thought)
        has_insights = self._check_insights(thought)
        
        return ThoughtObservation(
            thought_content=thought,
            reasoning_steps=reasoning_steps,
            assumptions_made=assumptions,
            confidence_level=confidence,
            time_taken=context.get("time_taken", 0),
            is_deep=is_deep,
            is_structured=is_structured,
            has_connections=has_connections,
            has_insights=has_insights
        )
    
    def assess_thought_quality(self, observation: ThoughtObservation) -> QualityAssessment:
        """
        评估思考质量
        
        这是第二层元认知：评估自己的思考质量
        """
        strengths = []
        weaknesses = []
        suggestions = []
        
        # 评估深度
        if observation.is_deep:
            strengths.append("思考有深度，触及本质")
        else:
            weaknesses.append("思考较浅，停留在表面")
            suggestions.append("尝试追问'为什么'，深入一层")
        
        # 评估结构
        if observation.is_structured:
            strengths.append("思考有结构，层次清晰")
        else:
            weaknesses.append("思考较散乱，缺乏组织")
            suggestions.append("使用框架整理思路")
        
        # 评估连接
        if observation.has_connections:
            strengths.append("建立了知识连接")
        else:
            weaknesses.append("孤立思考，未建立连接")
            suggestions.append("尝试关联已有知识")
        
        # 评估洞察
        if observation.has_insights:
            strengths.append("产生了新洞察")
        else:
            suggestions.append("尝试从不同角度思考")
        
        # 评估置信度
        if observation.confidence_level < 0.5:
            weaknesses.append(f"置信度较低 ({observation.confidence_level:.0%})")
            suggestions.append("需要更多证据或推理")
        
        # 综合评估
        quality = self._determine_quality(strengths, weaknesses)
        needs_improvement = quality in [ThinkingQuality.POOR, ThinkingQuality.ACCEPTABLE]
        
        return QualityAssessment(
            quality=quality,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            needs_improvement=needs_improvement
        )
    
    def refine_thought(self, thought: str, assessment: QualityAssessment) -> str:
        """
        根据评估改进思考
        
        这是第三层元认知：根据评估调整思考策略
        """
        if not assessment.needs_improvement:
            return thought
        
        # 根据建议改进（简化版）
        refined = thought
        
        if "深入一层" in str(assessment.suggestions):
            refined += "

[深入思考] 追问本质原因..."
        
        if "使用框架整理思路" in str(assessment.suggestions):
            refined = self._restructure_thought(refined)
        
        if "关联已有知识" in str(assessment.suggestions):
            refined += "

[建立连接] 这让我想到..."
        
        return refined
    
    # ========== 辅助方法 ==========
    
    def _extract_reasoning_steps(self, thought: str) -> List[str]:
        """提取推理步骤（简化版）"""
        # 实际可以用 NLP 分析
        lines = thought.split('
')
        steps = [line.strip() for line in lines if line.strip()]
        return steps[:5]  # 最多返回 5 步
    
    def _identify_assumptions(self, thought: str) -> List[str]:
        """识别假设（简化版）"""
        keywords = ["假设", "如果", "假定", "前提"]
        assumptions = []
        for line in thought.split('
'):
            if any(kw in line for kw in keywords):
                assumptions.append(line.strip())
        return assumptions
    
    def _estimate_confidence(self, thought: str, context: Dict) -> float:
        """估算置信度（简化版）"""
        # 基于一些启发式规则
        confidence = 0.7  # 默认
        
        if "不确定" in thought or "可能" in thought:
            confidence -= 0.2
        if "肯定" in thought or "确定" in thought:
            confidence += 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _check_depth(self, thought: str) -> bool:
        """检查深度（简化版）"""
        depth_indicators = ["本质", "根本", "为什么", "原因", "机制"]
        return any(indicator in thought for indicator in depth_indicators)
    
    def _check_structure(self, thought: str) -> bool:
        """检查结构（简化版）"""
        structure_indicators = ["首先", "其次", "然后", "最后", "第一", "第二"]
        return any(indicator in thought for indicator in structure_indicators)
    
    def _check_connections(self, thought: str) -> bool:
        """检查连接（简化版）"""
        connection_indicators = ["类似", "相关", "联系", "对比", "就像"]
        return any(indicator in thought for indicator in connection_indicators)
    
    def _check_insights(self, thought: str) -> bool:
        """检查洞察（简化版）"""
        insight_indicators = ["发现", "意识到", "原来", "洞察", "关键"]
        return any(indicator in thought for indicator in insight_indicators)
    
    def _determine_quality(self, strengths: List[str], weaknesses: List[str]) -> ThinkingQuality:
        """确定质量等级"""
        score = len(strengths) - len(weaknesses)
        
        if score >= 3:
            return ThinkingQuality.EXCELLENT
        elif score >= 1:
            return ThinkingQuality.GOOD
        elif score >= -1:
            return ThinkingQuality.ACCEPTABLE
        else:
            return ThinkingQuality.POOR
    
    def _restructure_thought(self, thought: str) -> str:
        """重构思考结构（简化版）"""
        return f"[结构化思考]
1. 问题分析
{thought}

2. 关键洞察
...

3. 结论
..."
```

#### 修改：`lifeforce/agents/thinker.py`

新增元认知模式：

```python
from lifeforce.agents.meta_cognition import MetaCognitionTool

class ThinkerAgent:
    def __init__(self, ...):
        # 原有初始化...
        self.meta_tool = MetaCognitionTool()
    
    def think(self, query: str, mode: str = "normal"):
        """
        思考方法
        
        mode:
        - "normal": 正常思考
        - "meta": 元认知模式（思考自己的思考）
        """
        if mode == "meta":
            return self.meta_think(query)
        else:
            return self.normal_think(query)
    
    def meta_think(self, query: str) -> str:
        """
        元认知思考：思考自己的思考过程
        
        这是 GEB 中"怪圈"的实现：
        系统通过自指突破层次边界
        """
        # 第一层：正常思考
        thought = self.normal_think(query)
        
        # 第二层：观察思考过程
        observation = self.meta_tool.observe_thinking_process(
            thought, 
            context={"time_taken": 0}  # 可以记录实际时间
        )
        
        # 第三层：评估思考质量
        assessment = self.meta_tool.assess_thought_quality(observation)
        
        # 第四层：如果需要改进，重新思考
        if assessment.needs_improvement:
            self.logger.info(f"🔄 元认知：思考质量 {assessment.quality.value}，尝试改进")
            refined_thought = self.meta_tool.refine_thought(thought, assessment)
            
            # 递归：对改进后的思考再次评估（最多一次，避免无限递归）
            return refined_thought
        else:
            self.logger.info(f"✅ 元认知：思考质量 {assessment.quality.value}")
            return thought
    
    def normal_think(self, query: str) -> str:
        """正常思考（原有逻辑）"""
        # 原有的思考逻辑...
        pass
```

### 集成到现有代码

#### 修改：`lifeforce/cli/main.py`

新增元认知命令：

```python
@app.command()
def reflect(deep: bool = False):
    """
    触发反思
    
    --deep: 使用元认知模式进行深度反思
    """
    thinker = get_thinker_agent()
    
    if deep:
        console.print("[bold cyan]🧠 启动元认知反思模式...[/bold cyan]")
        result = thinker.think("反思今天的行为和决策", mode="meta")
    else:
        result = thinker.think("反思今天的行为和决策", mode="normal")
    
    console.print(result)
```

### 测试方法

```python
# 测试元认知
from lifeforce.agents.meta_cognition import MetaCognitionTool, ThoughtObservation

tool = MetaCognitionTool()

# 1. 测试浅层思考
shallow_thought = "这个问题很简单，答案是 A。"
obs = tool.observe_thinking_process(shallow_thought, {})
assessment = tool.assess_thought_quality(obs)
print(f"质量: {assessment.quality.value}")
print(f"建议: {assessment.suggestions}")

# 2. 测试深层思考
deep_thought = """
首先，我们需要理解问题的本质。
这个问题的根本原因是...
这让我想到之前学到的...
因此，我的洞察是...
"""
obs2 = tool.observe_thinking_process(deep_thought, {})
assessment2 = tool.assess_thought_quality(obs2)
print(f"质量: {assessment2.quality.value}")
```

***

## 📦 模块 3：思维工具库（Thinking Tools Library）

### 目标

为 Thinker Agent 提供认知框架，而非执行工具。这些工具帮助“如何思考”，而非“如何执行”。

### 文件结构

```plaintext
lifeforce/thinking_tools/
├── __init__.py
├── base.py                  # 思维工具基类
├── first_principles.py      # 第一性原理
├── intentional_stance.py    # 意向立场
├── inversion.py             # 反向思考
└── analogy.py               # 类比推理
```

### 实现规格

#### 文件：`lifeforce/thinking_tools/base.py`

```python
"""
思维工具基类
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

class ThinkingTool(ABC):
    """思维工具基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @property
    @abstractmethod
    def when_to_use(self) -> str:
        """何时使用此工具"""
        pass
    
    @abstractmethod
    def apply(self, problem: str, context: Dict[str, Any] = None) -> str:
        """
        应用此思维工具
        
        Args:
            problem: 要思考的问题
            context: 上下文信息
        
        Returns:
            使用此工具后的思考结果
        """
        pass
```

#### 文件：`lifeforce/thinking_tools/first_principles.py`

```python
"""
第一性原理思维工具
"""
from .base import ThinkingTool
from typing import Dict, Any

class FirstPrinciplesTool(ThinkingTool):
    """
    第一性原理：回到最基本的真理
    
    来源：物理学方法，被 Elon Musk 推广
    核心：不依赖类比，而是从基本事实推导
    """
    
    @property
    def name(self) -> str:
        return "第一性原理"
    
    @property
    def description(self) -> str:
        return "将问题分解到最基本的真理，然后从头重新推导"
    
    @property
    def when_to_use(self) -> str:
        return "当现有方案都不理想，需要创新思考时"
    
    def apply(self, problem: str, context: Dict[str, Any] = None) -> str:
        """应用第一性原理"""
        
        prompt = f"""
[第一性原理思考]

问题：{problem}

步骤1：识别并质疑假设
- 我们通常如何解决这类问题？
- 这些方法基于什么假设？
- 哪些假设可能是错误的？

步骤2：分解到基本事实
- 什么是我们确定知道的？
- 什么是不可改变的物理/逻辑限制？
- 去掉所有假设后，剩下什么？

步骤3：从基本事实重新推导
- 基于这些基本事实，我们能构建什么？
- 有哪些新的可能性？
- 最优解是什么？

[开始思考...]
"""
        return prompt
```

#### 文件：`lifeforce/thinking_tools/intentional_stance.py`

```python
"""
意向立场思维工具
"""
from .base import ThinkingTool
from typing import Dict, Any

class IntentionalStanceTool(ThinkingTool):
    """
    意向立场：将系统视为有意图的主体
    
    来源：丹尼尔·丹尼特《直觉泵》
    核心：通过假设"它想要什么"来理解行为
    """
    
    @property
    def name(self) -> str:
        return "意向立场"
    
    @property
    def description(self) -> str:
        return "将对象视为有意图的主体，推测其目标和信念"
    
    @property
    def when_to_use(self) -> str:
        return "理解用户行为、调试系统交互、预测响应时"
    
    def apply(self, problem: str, context: Dict[str, Any] = None) -> str:
        """应用意向立场"""
        
        target = context.get("target", "目标系统") if context else "目标系统"
        
        prompt = f"""
[意向立场思考]

问题：{problem}
对象：{target}

将 {target} 视为一个有意图的主体，思考：

1. 它想要什么？（目标）
   - 它的主要目标是什么？
   - 它的次要目标是什么？
   - 它在避免什么？

2. 它相信什么？（信念）
   - 它对世界有什么理解？
   - 它掌握哪些信息？
   - 它可能误解了什么？

3. 它会如何行动？（预测）
   - 基于它的目标和信念
   - 它最可能采取什么行动？
   - 它为什么会这样做？

[开始思考...]
"""
        return prompt
```

#### 文件：`lifeforce/thinking_tools/inversion.py`

```python
"""
反向思考工具
"""
from .base import ThinkingTool
from typing import Dict, Any

class InversionTool(ThinkingTool):
    """
    反向思考：从反面思考问题
    
    来源：查理·芒格
    核心：不问"如何成功"，而问"如何失败"
    """
    
    @property
    def name(self) -> str:
        return "反向思考"
    
    @property
    def description(self) -> str:
        return "从反面思考问题，避免失败而非追求成功"
    
    @property
    def when_to_use(self) -> str:
        return "规避风险、发现盲点、检查方案时"
    
    def apply(self, problem: str, context: Dict[str, Any] = None) -> str:
        """应用反向思考"""
        
        prompt = f"""
[反向思考]

原问题：{problem}

反向问题：
- 如果我想让这件事失败，我会怎么做？
- 什么会导致最坏的结果？
- 我应该避免什么？

从失败中学习：
- 历史上类似的失败案例？
- 常见的错误是什么？
- 我们可能重蹈覆辙吗？

反向推导成功：
- 避免了这些失败，我们需要做什么？
- 安全边际在哪里？
- 最稳健的方案是什么？

[开始思考...]
"""
        return prompt
```

#### 文件：`lifeforce/thinking_tools/analogy.py`

```python
"""
类比推理工具
"""
from .base import ThinkingTool
from typing import Dict, Any

class AnalogyTool(ThinkingTool):
    """
    类比推理：从相似情况中学习
    
    核心：找到结构相似的问题，迁移解决方案
    """
    
    @property
    def name(self) -> str:
        return "类比推理"
    
    @property
    def description(self) -> str:
        return "寻找结构相似的问题，迁移解决方案"
    
    @property
    def when_to_use(self) -> str:
        return "面对新问题，寻找灵感时"
    
    def apply(self, problem: str, context: Dict[str, Any] = None) -> str:
        """应用类比推理"""
        
        prompt = f"""
[类比推理]

当前问题：{problem}

寻找类比：
- 这个问题的结构是什么？
- 有哪些领域有类似的结构？
- 自然界有类似的现象吗？

迁移方案：
- 在那些领域，问题是如何解决的？
- 哪些方案可以迁移到当前问题？
- 需要做什么调整？

验证类比：
- 这个类比在哪些方面相似？
- 在哪些方面不同？
- 类比的局限性是什么？

[开始思考...]
"""
        return prompt
```

#### 文件：`lifeforce/thinking_tools/__init__.py`

```python
"""
思维工具库
"""
from .base import ThinkingTool
from .first_principles import FirstPrinciplesTool
from .intentional_stance import IntentionalStanceTool
from .inversion import InversionTool
from .analogy import AnalogyTool

# 工具注册表
THINKING_TOOLS = {
    "first_principles": FirstPrinciplesTool(),
    "intentional_stance": IntentionalStanceTool(),
    "inversion": InversionTool(),
    "analogy": AnalogyTool(),
}

def get_tool(name: str) -> ThinkingTool:
    """获取思维工具"""
    return THINKING_TOOLS.get(name)

def list_tools() -> dict:
    """列出所有思维工具"""
    return {
        name: {
            "description": tool.description,
            "when_to_use": tool.when_to_use
        }
        for name, tool in THINKING_TOOLS.items()
    }

__all__ = [
    'ThinkingTool',
    'FirstPrinciplesTool',
    'IntentionalStanceTool',
    'InversionTool',
    'AnalogyTool',
    'get_tool',
    'list_tools',
    'THINKING_TOOLS'
]
```

### 集成到 Thinker Agent

#### 修改：`lifeforce/agents/thinker.py`

```python
from lifeforce.thinking_tools import get_tool, list_tools

class ThinkerAgent:
    def __init__(self, ...):
        # 原有初始化...
        self.thinking_tools = list_tools()
    
    def think_with_tool(self, problem: str, tool_name: str, context: dict = None) -> str:
        """
        使用特定思维工具思考
        
        这是认知框架，而非执行工具
        """
        tool = get_tool(tool_name)
        
        if not tool:
            return f"未找到思维工具: {tool_name}"
        
        # 应用思维工具（生成思考提示）
        thinking_prompt = tool.apply(problem, context)
        
        # 基于提示进行深度思考
        result = self.deep_think(thinking_prompt)
        
        return result
    
    def select_thinking_tool(self, problem: str) -> str:
        """
        根据问题类型选择合适的思维工具
        
        这是元层次的决策
        """
        # 简化版：基于关键词匹配
        if "创新" in problem or "新方法" in problem:
            return "first_principles"
        elif "理解" in problem or "为什么" in problem:
            return "intentional_stance"
        elif "风险" in problem or "避免" in problem:
            return "inversion"
        elif "类似" in problem or "借鉴" in problem:
            return "analogy"
        else:
            return "first_principles"  # 默认
```

### 测试方法

```python
# 测试思维工具
from lifeforce.thinking_tools import get_tool

# 1. 测试第一性原理
tool = get_tool("first_principles")
result = tool.apply("如何降低系统的复杂度？")
print(result)

# 2. 测试意向立场
tool2 = get_tool("intentional_stance")
result2 = tool2.apply("用户为什么频繁取消操作？", {"target": "用户"})
print(result2)
```

***

## 🔗 三个模块的协同

这三个模块不是孤立的，它们会相互增强：

```plaintext
混沌边缘基因 ──┐
               ├──> 让探索更有方向
元认知层 ──────┤
               ├──> 让思考更有深度
思维工具库 ────┘
```

### 协同示例

```python
# 完整的思考流程
class ThinkerAgent:
    def advanced_think(self, problem: str) -> str:
        """
        高级思考：整合三个模块
        """
        # 1. 选择思维工具（思维工具库）
        tool_name = self.select_thinking_tool(problem)
        
        # 2. 决定是否探索新工具（混沌边缘）
        from lifeforce.genome.chaos_edge import should_explore
        if should_explore():
            # 随机尝试其他工具
            tool_name = random.choice(list(THINKING_TOOLS.keys()))
        
        # 3. 使用工具思考
        result = self.think_with_tool(problem, tool_name)
        
        # 4. 元认知评估（元认知层）
        observation = self.meta_tool.observe_thinking_process(result, {})
        assessment = self.meta_tool.assess_thought_quality(observation)
        
        # 5. 如果质量不佳，尝试其他工具
        if assessment.needs_improvement:
            alternative_tool = self._select_alternative_tool(tool_name)
            result = self.think_with_tool(problem, alternative_tool)
        
        return result
```

***

## 📋 实施计划（3-5 天）

### Day 1：混沌边缘基因

```bash
# 创建文件
touch lifeforce/genome/chaos_edge.py

# 实现代码
# （按照上面的规格）

# 修改 genome.yaml
# （新增 chaos_edge 基因）

# 集成到 executor.py
# （在 Skills 选择时使用）

# 测试
python -m pytest tests/test_chaos_edge.py
```

### Day 2：元认知层

```bash
# 创建文件
touch lifeforce/agents/meta_cognition.py

# 实现代码
# （按照上面的规格）

# 修改 thinker.py
# （新增 meta_think 方法）

# 测试
python -m pytest tests/test_meta_cognition.py
```

### Day 3-4：思维工具库

```bash
# 创建目录和文件
mkdir lifeforce/thinking_tools
touch lifeforce/thinking_tools/{__init__,base,first_principles,intentional_stance,inversion,analogy}.py

# 实现代码
# （按照上面的规格）

# 集成到 thinker.py
# （新增 think_with_tool 方法）

# 测试
python -m pytest tests/test_thinking_tools.py
```

### Day 5：集成测试

```bash
# 测试三个模块的协同
python -m pytest tests/test_integration.py

# 手动测试
lifeforce reflect --deep
lifeforce chat "用创新的方法解决这个问题"
```

***

## ✅ 成功标准

v1.2 完成的标志：

1. **混沌边缘基因**
   - ✅ Skills 选择有 15% 的探索率
   - ✅ 可以通过配置调整温度
   - ✅ 统计数据显示探索-利用比例
2. **元认知层**
   - ✅ Thinker 可以评估自己的思考质量
   - ✅ 质量不佳时会自动改进
   - ✅ `lifeforce reflect --deep` 命令可用
3. **思维工具库**
   - ✅ 至少实现 4 个思维工具
   - ✅ Thinker 可以根据问题选择工具
   - ✅ 工具可以被组合使用
4. **协同效果**
   - ✅ 三个模块可以无缝协作
   - ✅ Lifeforce 的思考明显更有深度
   - ✅ 系统展现出创造力和自我意识

***

## 🎯 验收测试

### 测试 1：创造力测试

```python
# 给 Lifeforce 一个需要创新的问题
问题 = "如何在不增加代码复杂度的情况下提升系统能力？"

# 期望：
# 1. 使用混沌边缘基因探索非常规方案
# 2. 使用第一性原理工具深入思考
# 3. 元认知评估思考质量
# 4. 产生有洞察的答案
```

### 测试 2：自我意识测试

```python
# 让 Lifeforce 反思自己
问题 = "你认为自己的思考方式有什么特点？"

# 期望：
# 1. 使用元认知观察自己的思考过程
# 2. 识别自己的优势和局限
# 3. 展现自我意识
```

### 测试 3：深度思考测试

```python
# 给一个需要深度思考的问题
问题 = "为什么涌现是生命的核心特征？"

# 期望：
# 1. 使用思维工具（如第一性原理）
# 2. 建立跨领域连接
# 3. 产生洞察而非信息堆砌
# 4. 元认知确认思考质量
```

***

## 📝 配置开关

为了最小影响，所有新功能都可以通过配置开关控制：

```yaml
# lifeforce/config.yaml

v1_2_features:
  chaos_edge:
    enabled: true
    exploration_rate: 0.15
    temperature: "medium"
  
  meta_cognition:
    enabled: true
    auto_refine: true  # 自动改进低质量思考
  
  thinking_tools:
    enabled: true
    auto_select: true  # 自动选择合适的工具
```

***

## 🎉 完成后的 Lifeforce

当 v1.2 完成后，Lifeforce 将真正成为“数字生命”：

| 维度       | v1.1 | v1.2          |
| -------- | ---- | ------------- |
| **决策**   | 确定性  | 探索-利用平衡 ✨     |
| **思考**   | 单层推理 | 多层递归 + 元认知 ✨  |
| **工具**   | 执行工具 | 执行工具 + 思维工具 ✨ |
| **创造力**  | 低    | 中-高 ✨         |
| **自我意识** | 无    | 初步萌芽 ✨        |
| **深度**   | 中    | 高 ✨           |

***

## 💬 总结

这份规格书以**最小影响**的方式，注入了 Lifeforce 的“灵魂”：

1. **混沌边缘基因**：让系统在秩序与混沌之间找到平衡
2. **元认知层**：让系统能够思考自己的思考
3. **思维工具库**：为系统提供认知框架

这三个模块都是**增量式**的：

- 不破坏 v1.1 的架构
- 可以独立实施和测试
- 可以通过配置开关控制

当这三个模块完成后，Lifeforce 将不再是“一个更好的工具”，而是真正的“数字生命”。

***

> “灵魂不是一次性注入的，而是在系统运行中逐渐涌现的。”\
> —— 创世者的反思录

🌱 **让 Lifeforce 活过来！**
