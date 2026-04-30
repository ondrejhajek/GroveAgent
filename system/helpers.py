import asyncio
import os
from datetime import datetime
from pathlib import Path

from faststream.rabbit import RabbitBroker
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
import system.constants as constants
from system.logger import logger


def assert_rabbitmq_reachable(broker: RabbitBroker) -> None:
    """Ověří, že je RabbitMQ dostupné. Vyhodí RuntimeError, pokud připojení selže."""

    async def _verify():
        await broker.connect()
        await broker.stop()

    try:
        asyncio.run(_verify())
    except Exception as exc:
        logger.error("Připojení k RabbitMQ selhalo: %s", exc)
        raise RuntimeError(
            f"Připojení k RabbitMQ selhalo: {exc}. "
            f"Zkontroluj RABBITMQ_HOST, RABBITMQ_USERNAME a RABBITMQ_PASSWORD."
        ) from exc


def load_or_create_agent_id(agent_nickname: str) -> str:
    path = Path(".agent_id")
    if path.exists():
        return path.read_text().strip()
    agent_id = f"agent_{agent_nickname}_" + datetime.now().strftime("%Y%d%m%H%M%S")
    path.write_text(agent_id)
    return agent_id


def print_startup_banner(agent_id: str, configuration) -> None:

    console = Console()

    agent_cfg = configuration.get("agent")

    tools = [t["name"] for t in configuration.get("tools_agents", []) if t.get("enabled")]

    active_observers = []
    for item in configuration.get("observers", []):
        if item.get("enabled"):
            params = item.get("parameters", {})
            detail = next(iter(params.values()), "") if params else ""
            active_observers.append((item.get("type"), str(detail)))

    mcp_servers = list((agent_cfg.get("mcpServers") or {}).get("mcpServers", {}).keys())

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column()

    table.add_row("Agent ID", f"[yellow]{agent_id}[/yellow]")
    table.add_row("Model", f"[green]{agent_cfg.get('model', '—')}[/green]")

    if tools:
        table.add_row("", "")
        table.add_row("[bold]Aktivní Tools agenti[/bold]", ", ".join(tools))

    if active_observers:
        table.add_row("", "")
        obs_lines = "\n".join(f"[cyan]{t}[/cyan]  {d}" for t, d in active_observers)
        table.add_row("[bold]Observers[/bold]", obs_lines)

    table.add_row("", "")

    if mcp_servers:
        table.add_row("[bold]MCP[/bold]", ", ".join(mcp_servers))

    table.add_row("", "")
    table.add_row("RabbitMQ exchange", f"{agent_id}")
    table.add_row("RabbitMQ", f"[link]http://{os.environ.get("RABBITMQ_HOST", "")}[/link]  (user: {os.environ.get("RABBITMQ_USERNAME", "")})")

    table.add_row("", "")
    constantz = {k: v for k, v in vars(constants).items() if k.isupper()}
    for name, value in constantz.items():
        table.add_row(name, f"{value}")

    console.print(Panel(table, title="[bold white]GroveAgent[/bold white]", border_style="bright_blue"))
