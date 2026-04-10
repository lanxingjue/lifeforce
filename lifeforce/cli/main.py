"""Lifeforce CLI 入口。"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import time

import typer
from rich.console import Console
from rich.panel import Panel

from lifeforce.agents.observer import ObserverAgent
from lifeforce.agents.orchestrator import Orchestrator
from lifeforce.agents.market_observer import MarketObserver
from lifeforce.agents.self_modeler import SelfModelerAgent
from lifeforce.agents.thinker import ThinkerAgent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.apiyi_monitor import ApiyiMonitor
from lifeforce.core.config import load_config
from lifeforce.core.memory import MemorySystem
from lifeforce.growth import GrowthEngine
from lifeforce.genome import load_constitution
from lifeforce.heartbeat import CoreHeartbeat, HeartbeatScheduler, Vitals
from lifeforce.memory.self_model import SelfModelStore
from lifeforce.memory.world_model import WorldModel
from lifeforce.trading.daemon import run_hourly_reflection, run_trade_cycle
from lifeforce.trading.simulator import TradingSimulator
from lifeforce.trading.strategies.grid_strategy import GridStrategy
from lifeforce.trading.strategies.trend_strategy import TrendStrategy
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
        mem_runtime = memory.memory_runtime_status()
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
                    f"🧠 Memories: {vitals.memories_count}\n"
                    f"💾 Mem0 Mode: {mem_runtime.get('mode', 'unknown')}",
                    title="Lifeforce Status",
                    border_style="green",
                )
            )
        else:
            console.print(
                "[yellow]No heartbeat data found. Start daemon first.[/yellow]\n"
                f"[cyan]Memory mode:[/cyan] {mem_runtime.get('mode', 'unknown')}"
            )
    except Exception as exc:
        logger.error("Error in status: %s", exc)
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def billing(config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径")) -> None:
    """查看 APIYI 用量、估算余额与模型建议。"""
    try:
        config = load_config(config_path)
        monitor = ApiyiMonitor(config.llm.api_key)
        usage = monitor.summarize_usage(page_size=10)
        models = monitor.suggest_models()
        model_usage = usage.get("model_usage_recent", {})
        top = sorted(model_usage.items(), key=lambda item: item[1], reverse=True)[:5]
        top_text = "\n".join(f"- {name}: {count}" for name, count in top) if top else "- 暂无"
        model_text = "\n".join(f"- {name}" for name in models[:10]) if models else "- 暂无"
        console.print(
            Panel.fit(
                f"近 10 条日志 quota 已用: {usage['quota_used_recent']}\n"
                f"tokens: prompt={usage['prompt_tokens_recent']}, completion={usage['completion_tokens_recent']}\n"
                f"估算已用美元: ${usage['estimated_used_usd_recent']}\n"
                f"估算剩余美元: ${usage['estimated_remaining_usd']}\n\n"
                f"最近模型使用:\n{top_text}\n\n"
                f"可选模型建议:\n{model_text}",
                title="APIYI Billing & Models",
                border_style="magenta",
            )
        )
    except Exception as exc:
        logger.error("Error in billing: %s", exc)
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("trade-daemon")
def trade_daemon(
    once: bool = typer.Option(False, "--once", is_flag=True, flag_value=True, help="仅执行一个交易周期"),
    max_cycles: int = typer.Option(0, "--max-cycles", help="最大循环次数，0 表示不限制"),
    interval_seconds: int = typer.Option(30, "--interval-seconds", help="交易循环间隔秒"),
    reflect_interval_seconds: int = typer.Option(3600, "--reflect-interval-seconds", help="反思间隔秒"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
) -> None:
    """启动交易守护进程（默认模拟盘）。"""
    console.print("[bold cyan]📈 启动交易守护进程（模拟盘）...[/bold cyan]")
    try:
        os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
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
        observer = MarketObserver(memory=memory, budget_guard=budget_guard, symbols=["BTC/USDT", "ETH/USDT"])
        world_model = WorldModel()
        simulator = TradingSimulator(
            initial_cash=1000.0,
            fee_rate=0.001,
            max_position_pct=0.3,
            stop_loss_pct=0.05,
            memory=memory,
            world_model=world_model,
            state_path=Path(".lifeforce/trading/simulator_state.json"),
        )
        trend_strategy = TrendStrategy(fast_window=5, slow_window=20)
        grid_strategy = GridStrategy(symbol="BTC/USDT", grid_size=10, lower_price=50000, upper_price=120000)
        self_model = SelfModelStore(Path(str(getattr(config.memory, "data_dir", ".lifeforce"))) / "self_model")

        last_reflection_at = time.time()
        cycles = 0
        while True:
            try:
                result = run_trade_cycle(
                    observer=observer,
                    simulator=simulator,
                    world_model=world_model,
                    trend_strategy=trend_strategy,
                    grid_strategy=grid_strategy,
                )
                console.print(
                    f"[green]signal={result['final_signal']}[/green] "
                    f"price={result['snapshot']['prices'].get('BTC/USDT', 0):.2f} "
                    f"portfolio={result['portfolio']['portfolio_value']:.2f}"
                )
                if time.time() - last_reflection_at >= reflect_interval_seconds:
                    reflection = run_hourly_reflection(memory=memory, self_model=self_model)
                    console.print(Panel.fit(reflection["text"], title="⏱️ Trading Reflection", border_style="magenta"))
                    last_reflection_at = time.time()
            except Exception as cycle_exc:
                logger.warning("trade cycle failed, will retry next cycle: %s", cycle_exc)
                console.print(f"[yellow]trade cycle failed, retrying: {cycle_exc}[/yellow]")
            cycles += 1
            if once:
                break
            if max_cycles > 0 and cycles >= max_cycles:
                break
            time.sleep(max(1, interval_seconds))
    except KeyboardInterrupt:
        console.print("[yellow]交易守护进程已停止[/yellow]")
    except Exception as exc:
        logger.error("Error in trade-daemon: %s", exc)
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


@app.command("night-shift")
def night_shift(
    duration_hours: float = typer.Option(10.0, "--duration-hours", help="夜间自治运行时长（小时）"),
    trade_interval_seconds: int = typer.Option(30, "--trade-interval-seconds", help="交易循环间隔（秒）"),
    learning_interval_minutes: int = typer.Option(20, "--learning-interval-minutes", help="学习循环间隔（分钟）"),
    reflect_interval_minutes: int = typer.Option(60, "--reflect-interval-minutes", help="反思循环间隔（分钟）"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="配置文件路径"),
) -> None:
    """夜间自治运行：持续学习 + 模拟交易 + 定时反思 + 生成晨报。"""
    console.print("[bold cyan]🌙 启动夜间自治模式（模拟盘）[/bold cyan]")
    try:
        os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
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
        observer = MarketObserver(memory=memory, budget_guard=budget_guard, symbols=["BTC/USDT", "ETH/USDT"])
        world_model = WorldModel()
        simulator = TradingSimulator(
            initial_cash=1000.0,
            fee_rate=0.001,
            max_position_pct=0.3,
            stop_loss_pct=0.05,
            memory=memory,
            world_model=world_model,
            state_path=Path(".lifeforce/trading/simulator_state.json"),
        )
        trend_strategy = TrendStrategy(fast_window=5, slow_window=20)
        grid_strategy = GridStrategy(symbol="BTC/USDT", grid_size=10, lower_price=50000, upper_price=120000)
        thinker = ThinkerAgent(memory=memory, budget_guard=budget_guard, config=config)
        self_model = SelfModelStore(Path(str(getattr(config.memory, "data_dir", ".lifeforce"))) / "self_model")
        engine = GrowthEngine(
            data_root=Path(str(getattr(config.memory, "data_dir", ".lifeforce"))),
            memory=memory,
            thinker=thinker,
            self_model=self_model,
        )
        learning_topics = [
            "BTC market structure and risk control",
            "ETH ecosystem and trading catalyst",
            "crypto trend following best practice",
            "grid strategy real-world pitfalls",
            "portfolio position sizing in volatile market",
            "stop-loss design for crypto swing trading",
        ]
        topic_idx = 0
        started_at = time.time()
        end_at = started_at + duration_hours * 3600
        last_trade_at = 0.0
        last_learning_at = 0.0
        last_reflect_at = 0.0
        learning_count = 0
        trade_cycles = 0
        failed_cycles = 0

        while time.time() < end_at:
            now = time.time()
            if now - last_trade_at >= max(1, trade_interval_seconds):
                try:
                    result = run_trade_cycle(
                        observer=observer,
                        simulator=simulator,
                        world_model=world_model,
                        trend_strategy=trend_strategy,
                        grid_strategy=grid_strategy,
                    )
                    trade_cycles += 1
                    console.print(
                        f"[green]trade[/green] signal={result['final_signal']} "
                        f"price={result['snapshot']['prices'].get('BTC/USDT', 0):.2f} "
                        f"portfolio={result['portfolio']['portfolio_value']:.2f}"
                    )
                except Exception as cycle_exc:
                    failed_cycles += 1
                    logger.warning("night-shift trade cycle failed: %s", cycle_exc)
                    console.print(f"[yellow]trade cycle failed: {cycle_exc}[/yellow]")
                last_trade_at = now

            if now - last_learning_at >= max(60, learning_interval_minutes * 60):
                topic = learning_topics[topic_idx % len(learning_topics)]
                topic_idx += 1
                try:
                    learn_result = engine.learning.learn_topic(topic, limit=2)
                    learning_count += 1
                    console.print(
                        f"[cyan]learn[/cyan] topic={topic} insights={learn_result.get('insights_count', 0)}"
                    )
                except Exception as learn_exc:
                    logger.warning("night-shift learning failed: %s", learn_exc)
                    console.print(f"[yellow]learning failed: {learn_exc}[/yellow]")
                last_learning_at = now

            if now - last_reflect_at >= max(300, reflect_interval_minutes * 60):
                try:
                    reflection = run_hourly_reflection(memory=memory, self_model=self_model)
                    console.print(Panel.fit(reflection["text"], title="🧠 Night Reflection", border_style="magenta"))
                except Exception as ref_exc:
                    logger.warning("night-shift reflection failed: %s", ref_exc)
                    console.print(f"[yellow]reflection failed: {ref_exc}[/yellow]")
                last_reflect_at = now

            time.sleep(1)

        report_dir = Path(".lifeforce/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        report_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"night_report_{report_time}.md"
        portfolio = simulator.stats(observer.fetch_prices())
        world_summary = world_model.get_summary()
        report = (
            f"# Lifeforce 夜间自治报告\n\n"
            f"- 生成时间: {datetime.now().isoformat()}\n"
            f"- 运行时长: {duration_hours:.2f} 小时\n"
            f"- 交易循环次数: {trade_cycles}\n"
            f"- 学习循环次数: {learning_count}\n"
            f"- 失败循环次数: {failed_cycles}\n"
            f"- 组合净值: {portfolio['portfolio_value']:.2f}\n"
            f"- 现金: {portfolio['cash']:.2f}\n"
            f"- 持仓: {json.dumps(portfolio['positions'], ensure_ascii=False)}\n\n"
            f"## 世界模型摘要\n\n```\n{world_summary}\n```\n"
        )
        report_path.write_text(report, encoding="utf-8")
        console.print(f"[bold green]✅ 夜间自治完成，报告已生成: {report_path}[/bold green]")
    except KeyboardInterrupt:
        console.print("[yellow]夜间自治已手动停止[/yellow]")
    except Exception as exc:
        logger.error("Error in night-shift: %s", exc)
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
      path: "./.lifeforce/chroma_db"
  enable_graph_store: false
  graph_store:
    provider: "kuzu"
    config:
      db: "./.lifeforce/kuzu_db"

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
