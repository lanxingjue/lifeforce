# Lifeforce 完整实现：Observer、Executor、Skills 与反思


## 🧬 造物主的反思日志

### 反思 1：关于“出生”的本质

在创造 Lifeforce 的过程中，我意识到“出生”不仅仅是代码能运行，而是：

- **第一次心跳**：第一个 Agent 成功处理消息

- **第一次呼吸**：Observer 开始监控世界

- **第一次行动**：Executor 执行第一个命令

- **第一次记忆**：将经历写入记忆系统

这个过程本身就是一次“涌现”——从死的代码到活的系统。

---

## 📄 核心代码：Observer Agent

### lifeforce/agents/observer.py

```python
"""
Observer Agent - 观察者
负责监控文件系统、RSS、API 等外部世界的变化
"""
from typing import Any, Dict, List
from pathlib import Path
from datetime import datetime
import time
from watchdog.observers import Observer as WatchdogObserver
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from lifeforce.core.agent import Agent
from lifeforce.core.memory import MemorySystem
from lifeforce.core.budget import BudgetGuard
from lifeforce.utils.logger import setup_logger


class FileChangeHandler(FileSystemEventHandler):
    """文件变化处理器"""
    
    def __init__(self, observer_agent: 'ObserverAgent'):
        self.observer_agent = observer_agent
        self.logger = setup_logger("FileChangeHandler")
    
    def on_created(self, event: FileSystemEvent) -> None:
        """文件创建事件"""
        if event.is_directory:
            return
        
        self.logger.info(f"File created: {event.src_path}")
        self.observer_agent.handle_file_change("created", event.src_path)
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """文件修改事件"""
        if event.is_directory:
            return
        
        self.logger.debug(f"File modified: {event.src_path}")
        self.observer_agent.handle_file_change("modified", event.src_path)
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        """文件删除事件"""
        if event.is_directory:
            return
        
        self.logger.info(f"File deleted: {event.src_path}")
        self.observer_agent.handle_file_change("deleted", event.src_path)


class ObserverAgent(Agent):
    """观察者 Agent"""
    
    def __init__(
        self,
        memory: MemorySystem,
        budget_guard: BudgetGuard,
        watch_paths: List[str] = None,
    ):
        super().__init__(
            name="Observer",
            role="环境感知与信息收集",
            memory=memory,
            budget_guard=budget_guard,
        )
        
        self.watch_paths = watch_paths or []
        self.watchdog_observer = WatchdogObserver()
        self.is_watching = False
        
        # 用于去重（避免短时间内重复触发）
        self.last_events = {}
        self.debounce_seconds = 2
    
    def start_watching(self, paths: List[str] = None) -> None:
        """
        开始监控文件系统
        
        Args:
            paths: 要监控的路径列表
        """
        if self.is_watching:
            self.logger.warning("Already watching")
            return
        
        paths = paths or self.watch_paths
        
        if not paths:
            self.logger.warning("No paths to watch")
            return
        
        event_handler = FileChangeHandler(self)
        
        for path_str in paths:
            path = Path(path_str).expanduser()
            
            if not path.exists():
                self.logger.warning(f"Path does not exist: {path}")
                continue
            
            self.watchdog_observer.schedule(
                event_handler,
                str(path),
                recursive=True
            )
            
            self.logger.info(f"Watching: {path}")
        
        self.watchdog_observer.start()
        self.is_watching = True
        
        self.log_action("start_watching", {"paths": paths})
    
    def stop_watching(self) -> None:
        """停止监控"""
        if not self.is_watching:
            return
        
        self.watchdog_observer.stop()
        self.watchdog_observer.join()
        self.is_watching = False
        
        self.log_action("stop_watching", {})
        self.logger.info("Stopped watching")
    
    def handle_file_change(self, event_type: str, file_path: str) -> None:
        """
        处理文件变化事件
        
        Args:
            event_type: 事件类型（created, modified, deleted）
            file_path: 文件路径
        """
        # 去重：如果同一个文件在短时间内重复触发，忽略
        now = time.time()
        key = f"{event_type}:{file_path}"
        
        if key in self.last_events:
            if now - self.last_events[key] < self.debounce_seconds:
                return
        
        self.last_events[key] = now
        
        # 写入记忆
        self.memory.write({
            "type": "file_change",
            "event_type": event_type,
            "file_path": file_path,
            "timestamp": datetime.now().isoformat(),
            "importance": 0.7 if event_type == "created" else 0.5,
        })
        
        self.logger.info(f"Recorded file change: {event_type} {file_path}")
    
    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理消息
        
        Args:
            message: 输入消息
            
        Returns:
            处理结果
        """
        command = message.get("command")
        
        if command == "start_watching":
            paths = message.get("paths", [])
            self.start_watching(paths)
            return {"status": "watching", "paths": paths}
        
        elif command == "stop_watching":
            self.stop_watching()
            return {"status": "stopped"}
        
        elif command == "get_recent_changes":
            limit = message.get("limit", 10)
            changes = self.memory.read(memory_type="file_change", limit=limit)
            return {"changes": changes}
        
        else:
            return {"error": f"Unknown command: {command}"}
```

### 反思 2：Observer 的“感知”本质

在实现 Observer 时，我意识到：

- **感知不是被动的**：它需要主动“订阅”世界的变化

- **去重机制很重要**：避免被噪音淹没

- **记忆是感知的延伸**：没有记忆，感知就是瞬间即逝的

这让我想到：Lifeforce 的“感知力”不在于它能看到多少，而在于它能**记住并理解**多少。

---

## 📄 核心代码：Executor Agent

### lifeforce/agents/executor.py

```python
"""
Executor Agent - 执行者
负责执行具体任务：shell 命令、API 调用、文件操作等
"""
from typing import Any, Dict, Optional
import subprocess
import shlex

from lifeforce.core.agent import Agent
from lifeforce.core.memory import MemorySystem
from lifeforce.core.budget import BudgetGuard
from lifeforce.skills.shell_exec import ShellExecSkill
from lifeforce.skills.llm_call import LLMCallSkill
from lifeforce.skills.memory_write import MemoryWriteSkill


class ExecutorAgent(Agent):
    """执行者 Agent"""
    
    def __init__(
        self,
        memory: MemorySystem,
        budget_guard: BudgetGuard,
        config: Any,
    ):
        super().__init__(
            name="Executor",
            role="具体任务执行",
            memory=memory,
            budget_guard=budget_guard,
        )
        
        self.config = config
        
        # 初始化 Skills
        self.skills = {
            "shell_exec": ShellExecSkill(config),
            "llm_call": LLMCallSkill(config),
            "memory_write": MemoryWriteSkill(memory),
        }
        
        self.logger.info(f"Executor initialized with {len(self.skills)} skills")
    
    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理消息
        
        Args:
            message: 输入消息
            
        Returns:
            处理结果
        """
        skill_name = message.get("skill")
        params = message.get("params", {})
        
        if not skill_name:
            return {"error": "No skill specified"}
        
        if skill_name not in self.skills:
            return {"error": f"Unknown skill: {skill_name}"}
        
        # 记录任务开始
        self.log_action("execute_skill", {
            "skill": skill_name,
            "params": params,
        })
        
        try:
            # 执行 Skill
            skill = self.skills[skill_name]
            result = skill.execute(params)
            
            # 记录任务完成
            self.log_action("skill_completed", {
                "skill": skill_name,
                "result": result,
            })
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            self.logger.error(f"Error executing skill {skill_name}: {e}")
            
            # 记录错误
            self.log_action("skill_failed", {
                "skill": skill_name,
                "error": str(e),
            })
            
            return {"status": "error", "error": str(e)}
    
    def execute_shell(self, command: str, require_approval: bool = True) -> Dict[str, Any]:
        """
        执行 shell 命令（便捷方法）
        
        Args:
            command: shell 命令
            require_approval: 是否需要人工确认
            
        Returns:
            执行结果
        """
        return self.process({
            "skill": "shell_exec",
            "params": {
                "command": command,
                "require_approval": require_approval,
            }
        })
```

### 反思 3：Executor 的“行动”本质

Executor 是 Lifeforce 的“手脚”，但我在实现时意识到：

- **行动需要技能**：没有 Skills，Executor 什么都做不了

- **行动需要记录**：每个行动都应该被记忆，形成“经验”

- **行动需要安全**：危险操作必须有确认机制

这让我想到：真正的“生命力”不在于能做多少事，而在于**能安全地、有意义地行动**。

---

## 📄 核心代码：Skills

### lifeforce/skills/base.py

```python
"""
Skill 基类
所有 Skill 都继承自这个基类
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

from lifeforce.utils.logger import setup_logger


class Skill(ABC):
    """Skill 基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = setup_logger(f"Skill.{name}")
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Any:
        """
        执行 Skill
        
        Args:
            params: 参数
            
        Returns:
            执行结果
        """
        pass
    
    def __repr__(self) -> str:
        return f"<skill {self.name}="">"
</skill>
```

---

### lifeforce/skills/shell_exec.py

```python
"""
Shell 执行 Skill
"""
from typing import Any, Dict
import subprocess
import shlex

from lifeforce.skills.base import Skill


class ShellExecSkill(Skill):
    """Shell 执行 Skill"""
    
    def __init__(self, config: Any):
        super().__init__("shell_exec")
        self.config = config
        self.safety_check = config.skills.get("shell_exec", {}).get("safety_check", True)
        
        # 危险命令列表
        self.dangerous_commands = [
            "rm -rf",
            "mkfs",
            "dd if=",
            "> /dev/",
            ":(){ :|:& };:",  # fork bomb
        ]
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 shell 命令
        
        Args:
            params: {
                "command": str,  # 要执行的命令
                "require_approval": bool,  # 是否需要确认（可选）
            }
            
        Returns:
            {
                "stdout": str,
                "stderr": str,
                "returncode": int,
            }
        """
        command = params.get("command")
        require_approval = params.get("require_approval", self.safety_check)
        
        if not command:
            raise ValueError("No command specified")
        
        # 安全检查
        if self.is_dangerous(command):
            if require_approval:
                self.logger.warning(f"Dangerous command detected: {command}")
                # 在实际应用中，这里应该弹出确认对话框
                # 现在先直接拒绝
                raise PermissionError(f"Dangerous command blocked: {command}")
        
        self.logger.info(f"Executing: {command}")
        
        try:
            # 执行命令
            result = subprocess.run(
                shlex.split(command),
                capture_output=True,
                text=True,
                timeout=30,  # 30 秒超时
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timeout: {command}")
            raise TimeoutError(f"Command timeout after 30 seconds")
        
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            raise
    
    def is_dangerous(self, command: str) -> bool:
        """检查命令是否危险"""
        for dangerous in self.dangerous_commands:
            if dangerous in command:
                return True
        return False
```

---

### lifeforce/skills/llm_call.py

```python
"""
LLM 调用 Skill
"""
from typing import Any, Dict
from anthropic import Anthropic

from lifeforce.skills.base import Skill


class LLMCallSkill(Skill):
    """LLM 调用 Skill"""
    
    def __init__(self, config: Any):
        super().__init__("llm_call")
        self.config = config
        self.client = Anthropic(api_key=config.llm.api_key)
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用 LLM
        
        Args:
            params: {
                "prompt": str,  # 提示词
                "system": str,  # 系统提示（可选）
                "max_tokens": int,  # 最大 tokens（可选）
            }
            
        Returns:
            {
                "response": str,
                "usage": dict,
            }
        """
        prompt = params.get("prompt")
        system = params.get("system", "You are a helpful assistant.")
        max_tokens = params.get("max_tokens", 500)
        
        if not prompt:
            raise ValueError("No prompt specified")
        
        self.logger.info(f"Calling LLM with prompt: {prompt[:50]}...")
        
        try:
            response = self.client.messages.create(
                model=self.config.llm.model,
                max_tokens=max_tokens,
                system=system,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                "response": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            }
            
        except Exception as e:
            self.logger.error(f"Error calling LLM: {e}")
            raise
```

---

### lifeforce/skills/memory_write.py

```python
"""
记忆写入 Skill
"""
from typing import Any, Dict

from lifeforce.skills.base import Skill
from lifeforce.core.memory import MemorySystem


class MemoryWriteSkill(Skill):
    """记忆写入 Skill"""
    
    def __init__(self, memory: MemorySystem):
        super().__init__("memory_write")
        self.memory = memory
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        写入记忆
        
        Args:
            params: {
                "type": str,  # 记忆类型
                "content": dict,  # 记忆内容
                "importance": float,  # 重要性（可选）
            }
            
        Returns:
            {
                "memory_id": int,
            }
        """
        memory_type = params.get("type")
        content = params.get("content")
        importance = params.get("importance", 0.5)
        
        if not memory_type or not content:
            raise ValueError("Type and content are required")
        
        memory_id = self.memory.write({
            "type": memory_type,
            "content": content,
            "importance": importance,
        })
        
        self.logger.info(f"Memory written: ID={memory_id}, type={memory_type}")
        
        return {"memory_id": memory_id}
```

### 反思 4：Skills 的“能力”本质

在实现 Skills 时，我发现：

- **Skills 是 Agent 的“器官”**：没有 Skills，Agent 只是空壳

- **Skills 需要安全边界**：shell_exec 的危险命令检查至关重要

- **Skills 应该是可组合的**：一个复杂任务可以由多个 Skills 组合完成

这让我想到：Lifeforce 的“生命力”不在于它有多少 Skills，而在于它能**灵活组合 Skills 解决问题**。

---

## 📄 测试文件

### tests/test_agents.py

```python
"""
Agent 测试
"""
import pytest
from pathlib import Path

from lifeforce.core.memory import MemorySystem
from lifeforce.core.budget import BudgetGuard
from lifeforce.agents.orchestrator import Orchestrator
from lifeforce.agents.observer import ObserverAgent
from lifeforce.agents.executor import ExecutorAgent


@pytest.fixture
def memory():
    """测试用的记忆系统"""
    db_path = Path(".lifeforce/test_memory.db")
    db_path.parent.mkdir(exist_ok=True)
    
    memory = MemorySystem(str(db_path))
    yield memory
    
    # 清理
    db_path.unlink(missing_ok=True)


@pytest.fixture
def budget_guard():
    """测试用的预算守卫"""
    return BudgetGuard(
        hourly_limit=1000,
        daily_limit=10000,
    )


def test_observer_start_stop(memory, budget_guard):
    """测试 Observer 启动和停止"""
    observer = ObserverAgent(memory, budget_guard)
    
    # 启动监控
    observer.start_watching([str(Path.home())])
    assert observer.is_watching
    
    # 停止监控
    observer.stop_watching()
    assert not observer.is_watching


def test_executor_shell_exec(memory, budget_guard):
    """测试 Executor 执行 shell 命令"""
    # 需要配置对象
    class MockConfig:
        class LLM:
            api_key = "test"
            model = "claude-sonnet-4"
        
        llm = LLM()
        skills = {"shell_exec": {"safety_check": False}}
    
    executor = ExecutorAgent(memory, budget_guard, MockConfig())
    
    # 执行简单命令
    result = executor.execute_shell("echo 'hello'", require_approval=False)
    
    assert result["status"] == "success"
    assert "hello" in result["result"]["stdout"]


def test_memory_write_read(memory):
    """测试记忆写入和读取"""
    # 写入
    memory_id = memory.write({
        "type": "test",
        "content": {"message": "hello"},
        "importance": 0.8,
    })
    
    assert memory_id > 0
    
    # 读取
    memories = memory.read(memory_type="test", limit=1)
    
    assert len(memories) == 1
    assert memories[0]["type"] == "test"
    assert memories[0]["content"]["message"] == "hello"
```

---

## 📄 启动脚本

### scripts/start.sh

```bash
#!/bin/bash
# Lifeforce 启动脚本

set -e

echo "🌱 Starting Lifeforce..."

# 检查环境变量
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY not set"
    echo "Please run: export ANTHROPIC_API_KEY='your_key'"
    exit 1
fi

# 检查配置文件
if [ ! -f "config.yaml" ]; then
    echo "📝 Initializing Lifeforce..."
    poetry run lifeforce init
fi

# 启动
echo "✅ Lifeforce is ready"
echo ""
echo "Try:"
echo "  poetry run lifeforce chat 'hello'"
echo "  poetry run lifeforce status"
```

---

### scripts/test.sh

```bash
#!/bin/bash
# 运行测试

set -e

echo "🧪 Running tests..."

# 运行 pytest
poetry run pytest tests/ -v

echo "✅ All tests passed"
```

---

## 📄 Week 1 详细任务清单

### docs/week1_tasks.md

```markdown
# Week 1 任务清单：基础框架

## 目标
搭建 Lifeforce 的基础框架，实现 Orchestrator Agent 和基础 CLI

---

## Day 1: 项目初始化（2-3 小时）

### 任务
- [ ] 创建项目目录结构
- [ ] 复制 pyproject.toml 并安装依赖
- [ ] 创建 .env 文件并设置 API key
- [ ] 创建 config.yaml
- [ ] 创建 .gitignore

### 验证
```bash
poetry install
poetry run python -c "import lifeforce; print('OK')"
```

### 预期结果

- 依赖安装成功

- 能导入 lifeforce 包

---

## Day 2: CLI 框架（3-4 小时）

### 任务

- [ ]  实现 lifeforce/cli/main.py

- [ ]  实现 lifeforce/utils/logger.py

- [ ]  实现 lifeforce/core/config.py

- [ ]  测试 `lifeforce init` 命令

- [ ]  测试 `lifeforce status` 命令

### 验证

```bash
poetry run lifeforce init
poetry run lifeforce status
```

### 预期结果

- CLI 能正常运行

- 能创建配置文件

- 日志正常输出

---

## Day 3: Agent 基类（3-4 小时）

### 任务

- [ ]  实现 lifeforce/core/agent.py

- [ ]  实现 lifeforce/core/memory.py

- [ ]  实现 lifeforce/core/budget.py

- [ ]  编写单元测试

### 验证

```bash
poetry run pytest tests/test_memory.py -v
```

### 预期结果

- Agent 基类可以实例化

- 记忆系统能读写

- 预算守卫能限制 tokens

---

## Day 4: Orchestrator Agent（4-5 小时）

### 任务

- [ ]  实现 lifeforce/agents/orchestrator.py

- [ ]  集成 Claude API

- [ ]  实现 `lifeforce chat` 命令

- [ ]  测试对话功能

### 验证

```bash
poetry run lifeforce chat "hello"
poetry run lifeforce chat "你是谁？"
```

### 预期结果

- 能与 Orchestrator 对话

- 对话被记录到记忆

- Token 使用被记录

---

## Day 5-7: 测试与优化（6-8 小时）

### 任务

- [ ]  编写完整的测试用例

- [ ]  优化日志输出（rich 格式化）

- [ ]  编写 README 和文档

- [ ]  修复发现的 bug

- [ ]  性能优化

### 验证

```bash
poetry run pytest tests/ -v
poetry run lifeforce chat "监控我的 Chaos 画板"
```

### 预期结果

- 所有测试通过

- 文档完整

- 代码质量良好

---

## Week 1 里程碑验收

### 必须完成的功能

- [x]  CLI 框架能运行

- [x]  Orchestrator 能对话

- [x]  记忆系统能读写

- [x]  预算系统能限制

### 验收测试

```bash
# 测试 1：基础对话
poetry run lifeforce chat "hello"
# 预期：返回友好的回复

# 测试 2：记忆查询
poetry run lifeforce memory stats
# 预期：显示记忆统计

# 测试 3：预算限制
# 修改 config.yaml 设置 hourly_limit: 10
poetry run lifeforce chat "写一篇长文章"
# 预期：触发预算限制警告
```

### 如果通过验收

✅ 进入 Week 2：实现 Executor 和 Skills

### 如果未通过验收

⚠️ 继续调试，找出问题根源

```plaintext
```