"""Lifeforce CLI 入口。"""

from pathlib import Path
from typing import Optional
import time

import typer
from rich.console import Console
from rich.panel import Panel

from lifeforce.agents.observer import ObserverAgent
from lifeforce.agents.orchestrator import Orchestrator
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.config import load_config
from lifeforce.core.memory import MemorySystem
from lifeforce.utils.logger import setup_logger

app = typer.Typer(name="lifeforce", help="Lifeforce - A digital life form", add_completion=False)
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
        console.print(Panel.fit("Lifeforce is alive", border_style="green"))

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
    console.print("[bold green]Lifeforce Status[/bold green]")
    console.print("Version: 0.1.0 (MVP)")
    console.print("Status: Running")


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
