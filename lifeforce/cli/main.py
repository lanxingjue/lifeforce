"""Lifeforce CLI 入口。"""

import json
from pathlib import Path
from typing import Optional
import time

import typer
from rich.console import Console
from rich.panel import Panel

from lifeforce.agents.observer import ObserverAgent
from lifeforce.agents.orchestrator import Orchestrator
from lifeforce.agents.self_modeler import SelfModelerAgent
from lifeforce.agents.thinker import ThinkerAgent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.config import load_config
from lifeforce.core.memory import MemorySystem
from lifeforce.growth import GrowthEngine
from lifeforce.genome import load_constitution
from lifeforce.heartbeat import CoreHeartbeat, HeartbeatScheduler, Vitals
from lifeforce.memory.self_model import SelfModelStore
from lifeforce.utils.logger import setup_logger

app = typer.Typer(name="lifeforce", help="Lifeforce - A digital life form", add_completion=False)
skill_app = typer.Typer(name="skill", help="Skill lifecycle commands", add_completion=False)
app.add_typer(skill_app, name="skill")
console = Console()
logger = setup_logger("lifeforce.cli")


@app.command()
def chat(
    message: str = typer.Argument(..., help="你想对 Lifeforce 说什么"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
) -> None:
    """与 Lifeforce 对话。"""
    try:
        config = load_config(config_path)
        constitution = load_constitution()
        core_values = ", ".join(constitution.article_2_values.get("core_values", []))
        console.print(
            Panel.fit(
                f"🌱 Lifeforce v{constitution.version}\n核心价值观: {core_values}\n状态: {constitution.status}",
                title="Lifeforce Constitution",
                border_style="green",
            )
        )

        memory_config = config.memory.model_dump()
        memory_config["openai_base_url"] = config.llm.base_url
        try:
            memory_config["openai_api_key"] = config.llm.api_key
        except Exception:
            # 延迟到真正调用 LLM 时再报 API Key 错误
            pass
        memory = MemorySystem(config.memory.db_path, config=memory_config)
        budget_guard = BudgetGuard(
            hourly_limit=config.budget.hourly_limit,
            daily_limit=config.budget.daily_limit,
            monthly_limit=config.budget.monthly_limit,
        )

        orchestrator = Orchestrator(memory=memory, budget_guard=budget_guard, config=config)
        console.print(f"[bold cyan]You:[/bold cyan] {message}")

        response = orchestrator.handle_user_message(message)
        console.print(f"[bold green]Orchestrator:[/bold green] {response}")
    except Exception as exc:
        logger.error("Error in chat: %s", exc)
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def status() -> None:
    """查看 Lifeforce 状态。"""
    try:
        config = load_config()
        memory_config = config.memory.model_dump()
        memory_config["openai_base_url"] = config.llm.base_url
        try:
            memory_config["openai_api_key"] = config.llm.api_key
        except Exception:
            pass
        memory = MemorySystem(config.memory.db_path, config=memory_config)
        records = memory.read(memory_type="heartbeat", limit=1)
        if records:
            vitals = Vitals.from_dict(records[0]["content"]["vitals"])
            console.print(
                Panel.fit(
                    f"💓 Beat Count: {vitals.beat_count}\n"
                    f"⏱️  Uptime: {vitals.uptime_seconds:.0f}s\n"
                    f"🏥 Health: {vitals.health_status}\n"
                    f"✅ Tasks Completed: {vitals.tasks_completed}\n"
                    f"❌ Tasks Failed: {vitals.tasks_failed}\n"
                    f"🧠 Memories: {vitals.memories_count}",
                    title="Lifeforce Status",
                    border_style="green",
                )
            )
        else:
            console.print("[yellow]No heartbeat data found. Start daemon first.[/yellow]")
    except Exception as exc:
        logger.error("Error in status: %s", exc)
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def daemon(config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径")) -> None:
    """启动守护进程模式（持续心跳）。"""
    console.print("[bold green]🌱 Starting Lifeforce daemon...[/bold green]")
    try:
        config = load_config(config_path)
        memory_config = config.memory.model_dump()
        memory_config["openai_base_url"] = config.llm.base_url
        try:
            memory_config["openai_api_key"] = config.llm.api_key
        except Exception:
            pass
        memory = MemorySystem(config.memory.db_path, config=memory_config)
        budget_guard = BudgetGuard(
            hourly_limit=config.budget.hourly_limit,
            daily_limit=config.budget.daily_limit,
            monthly_limit=config.budget.monthly_limit,
        )
        heartbeat = CoreHeartbeat(memory, budget_guard)
        scheduler = HeartbeatScheduler(heartbeat)
        scheduler.start()
        console.print("[bold green]💚 Lifeforce is alive![/bold green]")
        console.print("Press Ctrl+C to stop")
        while True:
            time.sleep(1)
            if int(time.time()) % 60 == 0:
                vitals = scheduler.get_vitals()
                console.print(
                    f"💓 Beat #{vitals.beat_count} | Health: {vitals.health_status} | Uptime: {vitals.uptime_seconds:.0f}s"
                )
    except KeyboardInterrupt:
        try:
            scheduler.stop()
        except Exception:
            pass
        console.print("[bold red]💔 Lifeforce stopped[/bold red]")
    except Exception as exc:
        logger.error("Error in daemon: %s", exc)
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("observe")
def observe(
    path: Path = typer.Argument(..., help="要监控的目录路径"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
) -> None:
    """启动文件监控（按 Ctrl+C 停止）。"""
    try:
        config = load_config(config_path)
        memory_config = config.memory.model_dump()
        memory_config["openai_base_url"] = config.llm.base_url
        try:
            memory_config["openai_api_key"] = config.llm.api_key
        except Exception:
            pass

        memory = MemorySystem(config.memory.db_path, config=memory_config)
        budget_guard = BudgetGuard(
            hourly_limit=config.budget.hourly_limit,
            daily_limit=config.budget.daily_limit,
            monthly_limit=config.budget.monthly_limit,
        )
        observer = ObserverAgent(memory=memory, budget_guard=budget_guard, watch_paths=[str(path)])
        observer.start_watching()

        console.print(Panel.fit(f"开始监控: {path}", border_style="green"))
        console.print("[yellow]按 Ctrl+C 停止监控[/yellow]")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        try:
            observer.stop_watching()
        except Exception:
            pass
        console.print("[bold yellow]监控已停止[/bold yellow]")
    except Exception as exc:
        logger.error("Error in observe: %s", exc)
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("observe-recent")
def observe_recent(
    limit: int = typer.Argument(10, help="最近变化条数"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
) -> None:
    """查看最近文件变化记录。"""
    try:
        config = load_config(config_path)
        memory_config = config.memory.model_dump()
        memory_config["openai_base_url"] = config.llm.base_url
        try:
            memory_config["openai_api_key"] = config.llm.api_key
        except Exception:
            pass
        memory = MemorySystem(config.memory.db_path, config=memory_config)
        changes = memory.read(memory_type="file_change", limit=limit)

        if not changes:
            console.print("[yellow]暂无文件变化记录[/yellow]")
            return

        console.print("[bold green]最近文件变化[/bold green]")
        for item in changes:
            content = item.get("content", {})
            event_type = content.get("event_type", "unknown")
            file_path = content.get("file_path", "unknown")
            ts = content.get("timestamp", item.get("created_at", ""))
            console.print(f"- {event_type:<8} {file_path} ({ts})")
    except Exception as exc:
        logger.error("Error in observe-recent: %s", exc)
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def reflect(
    deep: bool = typer.Option(False, "--deep", is_flag=True, flag_value=True, help="使用元认知模式反思"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
) -> None:
    """触发反思，支持深度元认知模式。"""
    if deep:
        console.print("[bold cyan]🧠 启动元认知反思模式...[/bold cyan]")
    else:
        console.print("[bold cyan]🤔 Reflecting on self...[/bold cyan]")
    try:
        config = load_config(config_path)
        memory_config = config.memory.model_dump()
        memory_config["openai_base_url"] = config.llm.base_url
        try:
            memory_config["openai_api_key"] = config.llm.api_key
        except Exception:
            pass
        memory = MemorySystem(config.memory.db_path, config=memory_config)
        budget_guard = BudgetGuard(
            hourly_limit=config.budget.hourly_limit,
            daily_limit=config.budget.daily_limit,
            monthly_limit=config.budget.monthly_limit,
        )
        self_modeler = SelfModelerAgent(memory=memory, budget_guard=budget_guard, config=config)
        thinker = ThinkerAgent(memory=memory, budget_guard=budget_guard, config=config)
        base_description = self_modeler.reflect_on_self()
        if deep:
            data_root = Path(str(getattr(config.memory, "data_dir", ".lifeforce")))
            self_model = SelfModelStore(data_root / "self_model")
            engine = GrowthEngine(data_root=data_root, memory=memory, thinker=thinker, self_model=self_model)
            inputs = engine.collect_inputs()
            reflection = engine.reflect_deep(inputs)
            thought = reflection["text"]
        else:
            thought = thinker.think("反思今天的行为和决策", mode="normal")
        output = f"{base_description}\n\n[思考输出]\n{thought}"
        console.print(Panel.fit(output, title="🧠 Self-Reflection", border_style="cyan"))
    except Exception as exc:
        logger.error("Error in reflect: %s", exc)
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def grow(config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径")) -> None:
    """执行一次完整成长循环。"""
    try:
        config = load_config(config_path)
        memory_config = config.memory.model_dump()
        memory_config["openai_base_url"] = config.llm.base_url
        try:
            memory_config["openai_api_key"] = config.llm.api_key
        except Exception:
            pass
        memory = MemorySystem(config.memory.db_path, config=memory_config)
        budget_guard = BudgetGuard(
            hourly_limit=config.budget.hourly_limit,
            daily_limit=config.budget.daily_limit,
            monthly_limit=config.budget.monthly_limit,
        )
        thinker = ThinkerAgent(memory=memory, budget_guard=budget_guard, config=config)
        self_model = SelfModelStore(Path(str(getattr(config.memory, "data_dir", ".lifeforce"))) / "self_model")
        engine = GrowthEngine(
            data_root=Path(str(getattr(config.memory, "data_dir", ".lifeforce"))),
            memory=memory,
            thinker=thinker,
            self_model=self_model,
        )
        result = engine.run_growth_cycle()
        console.print(Panel.fit(json.dumps(result, ensure_ascii=False, indent=2), title="🌱 Growth Cycle", border_style="green"))
    except Exception as exc:
        logger.error("Error in grow: %s", exc)
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def learn(
    topic: str = typer.Argument(..., help="要学习的主题"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
) -> None:
    """主动学习指定主题。"""
    try:
        config = load_config(config_path)
        memory_config = config.memory.model_dump()
        memory_config["openai_base_url"] = config.llm.base_url
        try:
            memory_config["openai_api_key"] = config.llm.api_key
        except Exception:
            pass
        memory = MemorySystem(config.memory.db_path, config=memory_config)
        budget_guard = BudgetGuard(
            hourly_limit=config.budget.hourly_limit,
            daily_limit=config.budget.daily_limit,
            monthly_limit=config.budget.monthly_limit,
        )
        thinker = ThinkerAgent(memory=memory, budget_guard=budget_guard, config=config)
        self_model = SelfModelStore(Path(str(getattr(config.memory, "data_dir", ".lifeforce"))) / "self_model")
        engine = GrowthEngine(
            data_root=Path(str(getattr(config.memory, "data_dir", ".lifeforce"))),
            memory=memory,
            thinker=thinker,
            self_model=self_model,
        )
        result = engine.learning.learn_topic(topic)
        console.print(Panel.fit(json.dumps(result, ensure_ascii=False, indent=2), title="📚 Learning", border_style="cyan"))
    except Exception as exc:
        logger.error("Error in learn: %s", exc)
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@skill_app.command("search")
def skill_search(
    capability: str = typer.Argument(..., help="能力缺口描述"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
) -> None:
    """搜索相关技能。"""
    try:
        config = load_config(config_path)
        memory = MemorySystem(config.memory.db_path, config=config.memory.model_dump())
        budget_guard = BudgetGuard(
            hourly_limit=config.budget.hourly_limit,
            daily_limit=config.budget.daily_limit,
            monthly_limit=config.budget.monthly_limit,
        )
        thinker = ThinkerAgent(memory=memory, budget_guard=budget_guard, config=config)
        self_model = SelfModelStore(Path(str(getattr(config.memory, "data_dir", ".lifeforce"))) / "self_model")
        engine = GrowthEngine(
            data_root=Path(str(getattr(config.memory, "data_dir", ".lifeforce"))),
            memory=memory,
            thinker=thinker,
            self_model=self_model,
        )
        result = engine.skill_manager.search(capability, limit=3)
        console.print(Panel.fit(json.dumps(result, ensure_ascii=False, indent=2), title="🔎 Skill Search", border_style="yellow"))
    except Exception as exc:
        logger.error("Error in skill search: %s", exc)
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@skill_app.command("install")
def skill_install(
    skill_id: str = typer.Argument(..., help="技能 ID"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
) -> None:
    """安装指定技能并更新 self-model。"""
    try:
        config = load_config(config_path)
        memory = MemorySystem(config.memory.db_path, config=config.memory.model_dump())
        budget_guard = BudgetGuard(
            hourly_limit=config.budget.hourly_limit,
            daily_limit=config.budget.daily_limit,
            monthly_limit=config.budget.monthly_limit,
        )
        thinker = ThinkerAgent(memory=memory, budget_guard=budget_guard, config=config)
        self_model = SelfModelStore(Path(str(getattr(config.memory, "data_dir", ".lifeforce"))) / "self_model")
        engine = GrowthEngine(
            data_root=Path(str(getattr(config.memory, "data_dir", ".lifeforce"))),
            memory=memory,
            thinker=thinker,
            self_model=self_model,
        )
        installed = engine.skill_manager.install(skill_id)
        console.print(Panel.fit(json.dumps(installed, ensure_ascii=False, indent=2), title="🧩 Skill Installed", border_style="green"))
    except Exception as exc:
        logger.error("Error in skill install: %s", exc)
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def init(path: Path = typer.Argument(Path.cwd(), help="初始化路径")) -> None:
    """初始化 Lifeforce 项目。"""
    config_file = path / "config.yaml"
    data_dir = path / ".lifeforce"

    if config_file.exists():
        console.print("[yellow]配置文件已存在[/yellow]")
        return

    data_dir.mkdir(exist_ok=True)
    config_file.write_text(DEFAULT_CONFIG, encoding="utf-8")

    console.print("[bold green]初始化成功[/bold green]")
    console.print(f"配置文件: {config_file}")
    console.print(f"数据目录: {data_dir}")


DEFAULT_CONFIG = """memory:
  db_path: ".lifeforce/memory.db"
  data_dir: ".lifeforce"
  default_user_id: "wells"
  decay_enabled: true
  decay_half_life_days: 30
  retrieval_limit: 5
  min_score: 0.5
  vector_store:
    provider: "chroma"
    config:
      path: "./data/chroma_db"
  graph_store:
    provider: "kuzu"
    config:
      db: "./data/kuzu_db"

budget:
  hourly_limit: 100
  daily_limit: 1000
  monthly_limit: 10000

llm:
  provider: "apiyi"
  model: "MiniMax-M2.7"
  api_key_env: "APIYI_API_KEY"
  base_url: "https://api.apiyi.com/v1"
"""


if __name__ == "__main__":
    app()
