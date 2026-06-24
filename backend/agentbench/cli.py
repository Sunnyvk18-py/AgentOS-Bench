import json
import shutil
import time
from pathlib import Path

import click
import httpx
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from agentbench.utils import (
    api_request,
    format_score,
    get_api_url,
    handle_connection_error,
    poll_until_done,
    unwrap_response,
)

AGENTS_DIR = Path(__file__).resolve().parent.parent / "app" / "agents"
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


@click.group()
@click.option(
    "--api-url",
    default=None,
    help="AgentOS Bench API URL (default: http://localhost:8000)",
)
@click.pass_context
def cli(ctx: click.Context, api_url: str | None) -> None:
    ctx.ensure_object(dict)
    ctx.obj["api_url"] = api_url or None


@cli.group()
def agents() -> None:
    """Manage agent plugins."""


@agents.command("list")
@click.pass_context
def agents_list(ctx: click.Context) -> None:
    api_url = get_api_url(ctx)
    response = api_request("GET", "/api/agents", api_url)
    data = unwrap_response(response) or []

    if not data:
        from rich.console import Console

        Console().print("[yellow]No agents registered yet[/yellow]")
        return

    table = Table(title="Registered Agents", show_header=True, header_style="bold cyan")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Config Schema Keys")

    for agent in data:
        keys = ", ".join(agent.get("config_schema", {}).keys()) or "—"
        table.add_row(agent.get("name", ""), agent.get("description", ""), keys)

    from rich.console import Console

    Console().print(table)


@agents.command("add")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.pass_context
def agents_add(ctx: click.Context, path: Path) -> None:
    from rich.console import Console

    console = Console()
    api_url = get_api_url(ctx)
    content = path.read_text(encoding="utf-8")

    response = api_request(
        "POST",
        "/api/agents/validate",
        api_url,
        json={"content": content},
    )
    result = unwrap_response(response)

    if not result.get("valid"):
        console.print("[bold red]Validation failed:[/bold red]")
        for err in result.get("errors", []):
            console.print(f"  • {err}")
        raise SystemExit(1)

    agent_name = result.get("agent_name") or path.stem
    target = AGENTS_DIR / path.name

    if target.exists():
        console.print(f"[red]Agent file already exists:[/red] {target}")
        raise SystemExit(1)

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    console.print(
        f"[green]Agent '{agent_name}' registered. Hot-reload will pick it up automatically.[/green]"
    )


@cli.command()
@click.option("--agent", required=True, help="Agent name")
@click.option("--model", required=True, help="LLM model name")
@click.option("--task", required=True, help="Task description")
@click.option("--weights", default=None, help="JSON string of ScoreWeights")
@click.option("--watch", is_flag=True, help="Stream trace steps live")
@click.pass_context
def run(ctx: click.Context, agent: str, model: str, task: str, weights: str | None, watch: bool) -> None:
    from rich.console import Console

    console = Console()
    api_url = get_api_url(ctx)
    payload: dict = {
        "agent_name": agent,
        "llm_model": model,
        "task_description": task,
    }
    if weights:
        payload["agent_config"] = {"weights": json.loads(weights)}

    response = api_request("POST", "/api/runs", api_url, json=payload)
    run_data = unwrap_response(response)
    run_id = run_data["id"]

    console.print(
        Panel(
            f"[bold]Run ID:[/bold] {run_id}\n[bold]Agent:[/bold] {agent}\n[bold]Model:[/bold] {model}",
            title="Eval Run Started",
            border_style="blue",
        )
    )

    if watch:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Evaluating...", total=None)
            final = poll_until_done(api_url, run_id, interval=1.5)
    else:
        final = poll_until_done(api_url, run_id, interval=1.5)

    if final.get("status") == "failed":
        console.print(Panel("[red]Eval run failed[/red]", border_style="red"))
        raise SystemExit(1)

    table = Table(title="Score Breakdown", show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Value")
    metrics = [
        ("Composite", final.get("composite_score")),
        ("Accuracy", final.get("accuracy_score")),
        ("Hallucination (raw)", final.get("hallucination_score")),
        ("Tool Precision", final.get("tool_call_precision")),
        ("Latency (ms)", final.get("latency_ms")),
        ("Cost (USD)", final.get("cost_usd")),
    ]
    for name, value in metrics:
        if name == "Latency (ms)":
            display = str(value) if value is not None else "—"
        elif name == "Cost (USD)":
            display = f"${value:.6f}" if value is not None else "—"
        else:
            display = format_score(value) if isinstance(value, (int, float)) else str(value)
        table.add_row(name, display)
    console.print(table)

    if Confirm.ask("View trace?", default=False):
        detail = unwrap_response(api_request("GET", f"/api/runs/{run_id}", api_url))
        for step in sorted(detail.get("steps", []), key=lambda s: s.get("step_index", 0)):
            body = step.get("content", "")
            if step.get("tool_name"):
                body += (
                    f"\n\nTool: {step.get('tool_name')}\n"
                    f"Input: {step.get('tool_input')}\n"
                    f"Output: {step.get('tool_output')}"
                )
            console.print(
                Panel(
                    body,
                    title=f"Step {step.get('step_index', 0)} [{step.get('step_type')}] — {step.get('duration_ms')}ms",
                )
            )


@cli.command()
@click.option("--name", required=True, help="Benchmark name")
@click.option("--task", required=True, help="Task description")
@click.option("--models", required=True, help="Comma-separated model names")
@click.option("--agent", required=True, help="Agent name")
@click.pass_context
def benchmark(ctx: click.Context, name: str, task: str, models: str, agent: str) -> None:
    from rich.console import Console

    console = Console()
    api_url = get_api_url(ctx)
    model_list = [m.strip() for m in models.split(",") if m.strip()]

    api_request(
        "POST",
        "/api/benchmarks",
        api_url,
        json={
            "benchmark_name": name,
            "task_description": task,
            "models": model_list,
            "agent_name": agent,
        },
    )

    winner = None
    winner_score = None
    result_data = None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Running benchmark...", total=None)
        deadline = time.time() + 120
        while time.time() < deadline:
            listing = unwrap_response(api_request("GET", "/api/benchmarks", api_url)) or []
            match = next((b for b in listing if b.get("benchmark_name") == name), None)
            if match and match.get("winner_model") and match.get("results"):
                result_data = match
                winner = match.get("winner_model")
                winner_score = match.get("results", {}).get(winner, {}).get("composite_score")
                break
            time.sleep(2)

    if not result_data:
        console.print("[red]Benchmark did not complete in time[/red]")
        raise SystemExit(1)

    table = Table(title=f"Benchmark: {name}", show_header=True, header_style="bold")
    table.add_column("Model")
    table.add_column("Accuracy")
    table.add_column("Hallucination")
    table.add_column("Latency")
    table.add_column("Cost")
    table.add_column("Composite")

    for model_name in result_data.get("models_compared", []):
        row = result_data.get("results", {}).get(model_name, {})
        is_winner = model_name == winner
        style = "bold green" if is_winner else ""
        table.add_row(
            model_name,
            format_score(row.get("accuracy")),
            format_score(row.get("hallucination")),
            str(row.get("latency_ms") or "—"),
            f"${row.get('cost_usd', 0):.6f}" if row.get("cost_usd") is not None else "—",
            format_score(row.get("composite_score")),
            style=style,
        )

    console.print(table)
    console.print(
        Panel(
            f"Winner: [bold green]{winner}[/bold green] with composite score "
            f"{format_score(winner_score)}",
            border_style="green",
        )
    )


@cli.command()
@click.option("--run-id", required=True, help="Run ID")
@click.option("--format", "fmt", default="markdown", type=click.Choice(["json", "markdown"]))
@click.option("--output", "output_path", default=None, type=click.Path(path_type=Path))
@click.pass_context
def report(ctx: click.Context, run_id: str, fmt: str, output_path: Path | None) -> None:
    from rich.console import Console

    console = Console()
    api_url = get_api_url(ctx)
    response = api_request(
        "POST",
        "/api/reports/export",
        api_url,
        json={"run_id": run_id, "format": fmt},
    )

    if fmt == "json":
        content = unwrap_response(response)
        text = json.dumps(content, indent=2)
    else:
        text = response.text

    if output_path:
        output_path.write_text(text, encoding="utf-8")
        console.print(f"[green]Report saved to {output_path}[/green]")
        return

    if fmt == "json":
        console.print(Syntax(text, "json", theme="monokai"))
    else:
        console.print(Markdown(text))


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    from rich.console import Console

    console = Console()
    api_url = get_api_url(ctx)

    try:
        with httpx.Client(base_url=api_url, timeout=10.0) as client:
            health = client.get("/health")
    except httpx.RequestError as exc:
        handle_connection_error(exc)
        raise SystemExit(1) from exc

    data = health.json()

    def colorize(value: str) -> str:
        if value in ("ok", "connected", "healthy"):
            return f"[green]{value}[/green]"
        if value in ("degraded", "unavailable"):
            return f"[yellow]{value}[/yellow]"
        return f"[red]{value}[/red]"

    lines = [
        f"API Status: {colorize(data.get('status', 'unknown'))}",
        f"Database: {colorize(data.get('db', 'unknown'))}",
        f"Kafka: {colorize(data.get('kafka', 'unknown'))}",
        f"Registered Agents: [cyan]{data.get('agents_count', 0)}[/cyan]",
        f"Completed Runs Today: [cyan]{data.get('completed_runs_today', 0)}[/cyan]",
    ]
    console.print(Panel("\n".join(lines), title="AgentOS Bench Status", border_style="blue"))


@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    from rich.console import Console

    console = Console()
    api_url = Prompt.ask("API URL", default="http://localhost:8000")
    openai_key = Prompt.ask("OpenAI API key (optional)", default="", show_default=False)
    anthropic_key = Prompt.ask("Anthropic API key (optional)", default="", show_default=False)

    lines = [
        f"ENV=dev",
        f"LOG_LEVEL=INFO",
        f"DATABASE_URL=sqlite+aiosqlite:///./agentos_bench.db",
        f"KAFKA_BOOTSTRAP_SERVERS=localhost:9092",
        f"KAFKA_TOPIC_EVAL_EVENTS=eval-events",
        f"OPENAI_API_KEY={openai_key}",
        f"ANTHROPIC_API_KEY={anthropic_key}",
        f"AGENTBENCH_API_URL={api_url}",
    ]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    console.print("[green]Setup complete. Run `agentbench status` to verify.[/green]")


if __name__ == "__main__":
    cli()
