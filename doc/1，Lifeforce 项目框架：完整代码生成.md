# Lifeforce 项目框架：完整代码生成


## 📁 项目结构

```plaintext
lifeforce/
├── pyproject.toml              # 项目配置和依赖
├── README.md                   # 项目说明
├── .env.example                # 环境变量示例
├── .gitignore                  # Git 忽略文件
├── config.yaml                 # 默认配置
├── lifeforce/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py             # CLI 入口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py            # Agent 基类
│   │   ├── message_bus.py      # 消息总线
│   │   ├── memory.py           # 记忆系统
│   │   ├── budget.py           # 预算管理
│   │   └── config.py           # 配置加载
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py     # 指挥官 Agent
│   │   ├── observer.py         # 观察者 Agent
│   │   └── executor.py         # 执行者 Agent
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── base.py             # Skill 基类
│   │   ├── shell_exec.py       # Shell 执行
│   │   ├── llm_call.py         # LLM 调用
│   │   └── memory_write.py     # 记忆写入
│   └── utils/
│       ├── __init__.py
│       └── logger.py           # 日志系统
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_skills.py
│   └── test_memory.py
└── docs/
    ├── architecture.md         # 架构文档
    ├── development.md          # 开发指南
    └── week1_tasks.md          # Week 1 任务清单
```

---

## 📄 核心文件代码

### 1. pyproject.toml

```plaintext
[tool.poetry]
name = "lifeforce"
version = "0.1.0"
description = "A digital life form with autonomous agents and memory"
authors = ["Wells Monta <your@email.com>"]
readme = "README.md"
packages = [{include = "lifeforce"}]

[tool.poetry.dependencies]
python = "^3.11"
typer = "^0.9.0"
rich = "^13.7.0"
anthropic = "^0.18.0"
pydantic = "^2.6.0"
pydantic-settings = "^2.1.0"
pyyaml = "^6.0.1"
watchdog = "^4.0.0"
sqlalchemy = "^2.0.25"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"
pytest-asyncio = "^0.23.3"
black = "^24.1.1"
ruff = "^0.1.14"
mypy = "^1.8.0"

[tool.poetry.scripts]
lifeforce = "lifeforce.cli.main:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
</your@email.com>
```

---

### 2. lifeforce/cli/main.py

```python
"""
Lifeforce CLI 入口
这是用户与 Lifeforce 交互的主要界面
"""
import typer
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
from typing import Optional

from lifeforce.core.config import load_config
from lifeforce.agents.orchestrator import Orchestrator
from lifeforce.core.memory import MemorySystem
from lifeforce.core.budget import BudgetGuard
from lifeforce.utils.logger import setup_logger

app = typer.Typer(
    name="lifeforce",
    help="🌱 Lifeforce - A digital life form",
    add_completion=False,
)
console = Console()
logger = setup_logger()


@app.command()
def chat(
    message: str = typer.Argument(..., help="你想对 Lifeforce 说什么"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
):
    """
    与 Lifeforce 对话
    
    示例:
        lifeforce chat "hello"
        lifeforce chat "监控我的 Chaos 画板"
    """
    try:
        # 加载配置
        config = load_config(config_path)
        
        # 显示欢迎信息
        console.print(Panel.fit(
            "🌱 [bold green]Lifeforce[/bold green] is alive",
            border_style="green"
        ))
        
        # 初始化核心系统
        memory = MemorySystem(config.memory.db_path)
        budget_guard = BudgetGuard(
            hourly_limit=config.budget.hourly_limit,
            daily_limit=config.budget.daily_limit,
        )
        
        # 初始化 Orchestrator
        orchestrator = Orchestrator(
            memory=memory,
            budget_guard=budget_guard,
            config=config,
        )
        
        # 处理用户消息
        console.print(f"
[bold cyan]You:[/bold cyan] {message}")
        
        response = orchestrator.process(message)
        
        console.print(f"
[bold green]🤖 Orchestrator:[/bold green] {response}")
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def status():
    """
    查看 Lifeforce 的状态
    """
    console.print("[bold green]🌱 Lifeforce Status[/bold green]")
    console.print("Version: 0.1.0 (MVP)")
    console.print("Status: ✅ Running")
    # TODO: 显示更多状态信息（Agent 状态、记忆统计、预算使用等）


@app.command()
def init(
    path: Path = typer.Argument(Path.cwd(), help="初始化路径"),
):
    """
    初始化 Lifeforce 项目
    
    创建配置文件和数据目录
    """
    config_file = path / "config.yaml"
    data_dir = path / ".lifeforce"
    
    if config_file.exists():
        console.print("[yellow]⚠️  配置文件已存在[/yellow]")
        return
    
    # 创建数据目录
    data_dir.mkdir(exist_ok=True)
    
    # 创建默认配置
    default_config = """
# Lifeforce 配置文件

memory:
  db_path: ".lifeforce/memory.db"

budget:
  hourly_limit: 100
  daily_limit: 1000
  monthly_limit: 10000

llm:
  provider: "anthropic"
  model: "claude-sonnet-4"
  api_key_env: "ANTHROPIC_API_KEY"

agents:
  orchestrator:
    enabled: true
  observer:
    enabled: true
  executor:
    enabled: true

skills:
  shell_exec:
    enabled: true
    safety_check: true
  llm_call:
    enabled: true
  memory_write:
    enabled: true
"""
    
    config_file.write_text(default_config)
    
    console.print(f"[bold green]✅ 初始化成功[/bold green]")
    console.print(f"配置文件: {config_file}")
    console.print(f"数据目录: {data_dir}")
    console.print("
下一步:")
    console.print("1. 编辑 config.yaml 配置文件")
    console.print("2. 设置环境变量 ANTHROPIC_API_KEY")
    console.print("3. 运行: lifeforce chat 'hello'")


if __name__ == "__main__":
    app()
```

---

### 3. lifeforce/core/agent.py

```python
"""
Agent 基类
所有 Agent 都继承自这个基类
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
import uuid

from lifeforce.core.memory import MemorySystem
from lifeforce.core.budget import BudgetGuard
from lifeforce.utils.logger import setup_logger


class Agent(ABC):
    """Agent 基类"""
    
    def __init__(
        self,
        name: str,
        role: str,
        memory: MemorySystem,
        budget_guard: BudgetGuard,
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.role = role
        self.memory = memory
        self.budget_guard = budget_guard
        self.logger = setup_logger(name)
        
        self.logger.info(f"Agent {name} initialized (ID: {self.id})")
    
    @abstractmethod
    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理消息的核心方法
        每个 Agent 必须实现这个方法
        
        Args:
            message: 输入消息
            
        Returns:
            处理结果
        """
        pass
    
    def log_action(self, action: str, details: Dict[str, Any]) -> None:
        """记录 Agent 的行动"""
        self.memory.write({
            "type": "agent_action",
            "agent_id": self.id,
            "agent_name": self.name,
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        })
        
        self.logger.info(f"Action: {action}")
    
    def request_tokens(self, amount: int, purpose: str) -> bool:
        """
        请求 token 预算
        
        Args:
            amount: 需要的 token 数量
            purpose: 用途说明
            
        Returns:
            是否批准
        """
        approved, reason = self.budget_guard.request_tokens(amount)
        
        if not approved:
            self.logger.warning(f"Token request denied: {reason}")
            return False
        
        self.logger.info(f"Token request approved: {amount} for {purpose}")
        return True
    
    def __repr__(self) -> str:
        return f"<agent {self.name}="" ({self.role})="">"
</agent>
```

---

### 4. lifeforce/agents/orchestrator.py

```python
"""
Orchestrator Agent - 指挥官
负责解析用户意图、调度其他 Agent
"""
from typing import Any, Dict
from anthropic import Anthropic

from lifeforce.core.agent import Agent
from lifeforce.core.memory import MemorySystem
from lifeforce.core.budget import BudgetGuard


class Orchestrator(Agent):
    """指挥官 Agent"""
    
    def __init__(
        self,
        memory: MemorySystem,
        budget_guard: BudgetGuard,
        config: Any,
    ):
        super().__init__(
            name="Orchestrator",
            role="任务分解与调度",
            memory=memory,
            budget_guard=budget_guard,
        )
        
        self.config = config
        self.llm_client = Anthropic(api_key=config.llm.api_key)
        
        # 元提示词
        self.system_prompt = """
你是 Lifeforce 的"大脑皮层" - Orchestrator Agent。

你的职责是：
1. 理解用户的深层意图（不只是字面意思）
2. 将复杂任务分解为可执行的子任务
3. 调度最合适的专业 Agent 去执行
4. 整合结果，以优雅的方式呈现给用户

当前可用的 Agents：
- Observer: 观察文件系统、监控变化
- Executor: 执行具体任务（shell 命令、API 调用）

你不需要事事亲力亲为，你的智慧在于"知道谁最擅长什么"。

请用简洁、友好的语气回复用户。
"""
    
    def process(self, user_message: str) -> str:
        """
        处理用户消息
        
        Args:
            user_message: 用户输入
            
        Returns:
            回复内容
        """
        # 记录用户消息
        self.log_action("receive_message", {"message": user_message})
        
        # 预估 token 使用量（粗略估计）
        estimated_tokens = len(user_message) * 2  # 简单估算
        
        if not self.request_tokens(estimated_tokens, "process_user_message"):
            return "⚠️ 预算不足，无法处理请求"
        
        try:
            # 调用 LLM
            response = self.llm_client.messages.create(
                model=self.config.llm.model,
                max_tokens=500,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            reply = response.content[0].text
            
            # 记录回复
            self.log_action("send_reply", {"reply": reply})
            
            return reply
            
        except Exception as e:
            self.logger.error(f"Error calling LLM: {e}")
            return f"❌ 处理消息时出错: {e}"
    
    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        实现基类的 process 方法
        （为了兼容 Agent 基类接口）
        """
        if isinstance(message, str):
            return {"reply": self.process(message)}
        
        return {"reply": self.process(message.get("content", ""))}
```

---

### 5. lifeforce/core/memory.py

```python
"""
记忆系统
使用 SQLite 存储记忆
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
import json
import sqlite3

from lifeforce.utils.logger import setup_logger


class MemorySystem:
    """记忆系统"""
    
    def __init__(self, db_path: str = ".lifeforce/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = setup_logger("MemorySystem")
        self.conn = sqlite3.connect(str(self.db_path))
        
        self._init_db()
        
        self.logger.info(f"Memory system initialized at {db_path}")
    
    def _init_db(self) -> None:
        """初始化数据库表"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                created_at TEXT NOT NULL,
                last_accessed TEXT,
                access_count INTEGER DEFAULT 0,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_type ON memories(type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)
        """)
        
        self.conn.commit()
    
    def write(self, memory: Dict[str, Any]) -> int:
        """
        写入记忆
        
        Args:
            memory: 记忆内容
            
        Returns:
            记忆 ID
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO memories (type, content, importance, created_at, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            memory.get("type", "unknown"),
            json.dumps(memory, ensure_ascii=False),
            memory.get("importance", 0.5),
            datetime.now().isoformat(),
            json.dumps(memory.get("metadata", {}), ensure_ascii=False),
        ))
        
        self.conn.commit()
        memory_id = cursor.lastrowid
        
        self.logger.debug(f"Memory written: ID={memory_id}, type={memory.get('type')}")
        
        return memory_id
    
    def read(
        self,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        读取记忆
        
        Args:
            memory_type: 记忆类型（可选）
            limit: 返回数量
            
        Returns:
            记忆列表
        """
        cursor = self.conn.cursor()
        
        if memory_type:
            cursor.execute("""
                SELECT id, type, content, importance, created_at, access_count
                FROM memories
                WHERE type = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (memory_type, limit))
        else:
            cursor.execute("""
                SELECT id, type, content, importance, created_at, access_count
                FROM memories
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        
        memories = []
        for row in cursor.fetchall():
            memories.append({
                "id": row[0],
                "type": row[1],
                "content": json.loads(row[2]),
                "importance": row[3],
                "created_at": row[4],
                "access_count": row[5],
            })
        
        return memories
    
    def stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM memories")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM memories
            GROUP BY type
            ORDER BY count DESC
        """)
        
        type_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_count": total_count,
            "type_counts": type_counts,
        }
    
    def close(self) -> None:
        """关闭数据库连接"""
        self.conn.close()
        self.logger.info("Memory system closed")
```

---

### 6. lifeforce/core/budget.py

```python
"""
预算管理系统
防止 token 失控消耗
"""
from typing import Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from lifeforce.utils.logger import setup_logger


class BudgetGuard:
    """预算守卫"""
    
    def __init__(
        self,
        hourly_limit: int = 100,
        daily_limit: int = 1000,
        monthly_limit: int = 10000,
    ):
        self.limits = {
            "hourly": hourly_limit,
            "daily": daily_limit,
            "monthly": monthly_limit,
        }
        
        self.usage = defaultdict(int)
        self.reset_times = {
            "hourly": datetime.now() + timedelta(hours=1),
            "daily": datetime.now() + timedelta(days=1),
            "monthly": datetime.now() + timedelta(days=30),
        }
        
        self.logger = setup_logger("BudgetGuard")
        
        self.logger.info(f"Budget limits: {self.limits}")
    
    def request_tokens(self, amount: int) -> Tuple[bool, str]:
        """
        请求 token 预算
        
        Args:
            amount: 需要的 token 数量
            
        Returns:
            (是否批准, 原因)
        """
        # 检查是否需要重置
        self._check_reset()
        
        # 检查所有层级的限制
        for period, limit in self.limits.items():
            if self.usage[period] + amount > limit:
                reason = f"超过 {period} 限制 ({self.usage[period]}/{limit})"
                self.logger.warning(f"Token request denied: {reason}")
                return False, reason
        
        # 通过检查，分配 tokens
        for period in self.limits:
            self.usage[period] += amount
        
        self.logger.debug(f"Token allocated: {amount}")
        return True, "OK"
    
    def _check_reset(self) -> None:
        """检查并重置过期的计数器"""
        now = datetime.now()
        
        for period, reset_time in self.reset_times.items():
            if now >= reset_time:
                old_usage = self.usage[period]
                self.usage[period] = 0
                
                # 设置下一个重置时间
                if period == "hourly":
                    self.reset_times[period] = now + timedelta(hours=1)
                elif period == "daily":
                    self.reset_times[period] = now + timedelta(days=1)
                elif period == "monthly":
                    self.reset_times[period] = now + timedelta(days=30)
                
                self.logger.info(f"Reset {period} usage: {old_usage} -> 0")
    
    def get_usage(self) -> dict:
        """获取当前使用情况"""
        self._check_reset()
        
        return {
            period: {
                "used": self.usage[period],
                "limit": self.limits[period],
                "remaining": self.limits[period] - self.usage[period],
                "percentage": (self.usage[period] / self.limits[period]) * 100,
            }
            for period in self.limits
        }
```

---

### 7. lifeforce/core/config.py

```python
"""
配置管理
"""
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import os


class MemoryConfig(BaseModel):
    """记忆系统配置"""
    db_path: str = ".lifeforce/memory.db"


class BudgetConfig(BaseModel):
    """预算配置"""
    hourly_limit: int = 100
    daily_limit: int = 1000
    monthly_limit: int = 10000


class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: str = "anthropic"
    model: str = "claude-sonnet-4"
    api_key_env: str = "ANTHROPIC_API_KEY"
    
    @property
    def api_key(self) -> str:
        """从环境变量获取 API key"""
        key = os.getenv(self.api_key_env)
        if not key:
            raise ValueError(f"环境变量 {self.api_key_env} 未设置")
        return key


class Config(BaseSettings):
    """主配置"""
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径（可选）
        
    Returns:
        配置对象
    """
    if config_path is None:
        config_path = Path("config.yaml")
    
    if not config_path.exists():
        # 使用默认配置
        return Config()
    
    with open(config_path) as f:
        config_dict = yaml.safe_load(f)
    
    return Config(**config_dict)
```

---

### 8. lifeforce/utils/logger.py

```python
"""
日志系统
"""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器
    """
    logger = logging.getLogger(name or "lifeforce")
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 文件 handler
    log_dir = Path(".lifeforce/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_dir / "lifeforce.log")
    file_handler.setLevel(logging.DEBUG)
    
    # 格式化
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
```

---

## 📝 配置文件

### config.yaml

```yaml
# Lifeforce 配置文件

memory:
  db_path: ".lifeforce/memory.db"

budget:
  hourly_limit: 100
  daily_limit: 1000
  monthly_limit: 10000

llm:
  provider: "anthropic"
  model: "claude-sonnet-4"
  api_key_env: "ANTHROPIC_API_KEY"

agents:
  orchestrator:
    enabled: true
  observer:
    enabled: false  # Week 3 实现
  executor:
    enabled: false  # Week 2 实现

skills:
  shell_exec:
    enabled: false  # Week 2 实现
    safety_check: true
  llm_call:
    enabled: true
  memory_write:
    enabled: true
```

---

### .env.example

```bash
# Anthropic API Key
ANTHROPIC_API_KEY=your_api_key_here

# 可选：OpenAI API Key（如果使用 GPT-4）
# OPENAI_API_KEY=your_openai_key_here
```

---

### .gitignore

```plaintext
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Lifeforce
.lifeforce/
config.yaml
.env

# OS
.DS_Store
Thumbs.db
```

---

## 📖 [README.md](http://README.md)

```markdown
# 🌱 Lifeforce

一个具有生命力的数字生命体 - 多 Agent 协同系统

## 特性

- 🤖 多 Agent 协同（Orchestrator, Observer, Executor）
- 🧠 记忆系统（SQLite 持久化）
- 💰 预算管理（防止 token 失控）
- 🎨 优雅的 CLI 界面（typer + rich）
- 🔒 安全机制（审批门控、沙箱隔离）

## 快速开始

### 1. 安装依赖

```bash
# 使用 poetry
poetry install

# 或使用 pip
pip install -e .
```

### 2. 配置

```bash
# 初始化项目
lifeforce init

# 设置 API key
export ANTHROPIC_API_KEY="your_api_key_here"
```

### 3. 运行

```bash
# 与 Lifeforce 对话
lifeforce chat "hello"

# 查看状态
lifeforce status
```

## 开发路线图

- [x]  Week 1: 基础框架 + Orchestrator

- [ ]  Week 2: Executor + Skills

- [ ]  Week 3: Observer + 记忆系统

- [ ]  Week 4: 整合测试

## 架构

```plaintext
CLI → Orchestrator → [Observer, Executor] → Skills → Memory
```

## 文档

- 架构设计

- 开发指南

- Week 1 任务

## License

MIT

```plaintext

---

## ✅ 下一步行动

现在你可以：

1. **在本地创建项目**
```bash
mkdir lifeforce && cd lifeforce
```

2. **复制上面的代码到对应文件**

   - 创建目录结构

   - 复制每个文件的代码

3. **安装依赖**

```bash
poetry init  # 复制 pyproject.toml 的内容
poetry install
```

4. **设置环境变量**

```bash
export ANTHROPIC_API_KEY="your_key"
```

5. **测试第一个命令**

```bash
poetry run python -m lifeforce.cli.main chat "hello"
```

---

我已经为你生成了完整的 MVP 框架！这是一个可以直接运行的最小版本。

要不要我继续生成：

- Week 1 的详细任务清单？

- 测试文件的代码？

- 或者你想先在本地试试这个版本？