import os
import time
from typing import Any

import httpx
from rich.console import Console
from rich.panel import Panel

console = Console()
DEFAULT_API_URL = "http://localhost:8000"


def get_api_url(ctx: Any | None = None) -> str:
    if ctx is not None and hasattr(ctx, "obj") and ctx.obj and ctx.obj.get("api_url"):
        return ctx.obj["api_url"]
    return os.getenv("AGENTBENCH_API_URL", DEFAULT_API_URL)


def format_score(score: float | None) -> str:
    if score is None:
        return "[dim]—[/dim]"
    pct = score * 100
    text = f"{pct:.1f}%"
    if score > 0.8:
        return f"[green]{text}[/green]"
    if score >= 0.5:
        return f"[yellow]{text}[/yellow]"
    return f"[red]{text}[/red]"


def handle_connection_error(exc: Exception | None = None) -> None:
    console.print(
        Panel(
            "[bold red]Cannot connect to AgentOS Bench API[/bold red]\n\n"
            "Start the backend server:\n"
            "  [cyan]cd backend[/cyan]\n"
            "  [cyan]python -m uvicorn app.main:app --reload[/cyan]\n\n"
            "Or set a custom URL:\n"
            "  [cyan]export AGENTBENCH_API_URL=http://localhost:8000[/cyan]\n"
            "  [cyan]agentbench --api-url http://localhost:8000 status[/cyan]",
            title="Server Offline",
            border_style="red",
        )
    )
    if exc:
        console.print(f"[dim]{exc}[/dim]")


def api_request(method: str, path: str, api_url: str, **kwargs) -> httpx.Response:
    try:
        with httpx.Client(base_url=api_url, timeout=60.0) as client:
            return client.request(method, path, **kwargs)
    except httpx.ConnectError as exc:
        handle_connection_error(exc)
        raise SystemExit(1) from exc
    except httpx.TimeoutException as exc:
        handle_connection_error(exc)
        raise SystemExit(1) from exc


def unwrap_response(response: httpx.Response) -> Any:
    if response.status_code >= 400:
        try:
            body = response.json()
            error = body.get("error") or body.get("detail") or response.text
        except Exception:
            error = response.text
        console.print(f"[red]API error ({response.status_code}):[/red] {error}")
        raise SystemExit(1)
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        data = response.json()
        if isinstance(data, dict) and "success" in data:
            if not data.get("success"):
                console.print(f"[red]{data.get('error')}[/red]")
                raise SystemExit(1)
            return data.get("data")
        return data
    return response.text


def poll_until_done(api_url: str, run_id: str, interval: float = 1.5) -> dict[str, Any]:
    while True:
        response = api_request("GET", f"/api/runs/{run_id}", api_url)
        run = unwrap_response(response)
        status = run.get("status")
        if status in ("completed", "failed"):
            return run
        time.sleep(interval)
