from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box


def load_or_create_agent_id(agent_nickname: str) -> str:
    path = Path(".agent_id")
    if path.exists():
        return path.read_text().strip()
    agent_id = f"agent_{agent_nickname}_" + datetime.now().strftime("%Y%d%m%H%M%S")
    path.write_text(agent_id)
    return agent_id


def print_startup_banner(agent_id: str, config: dict, rabbitmq_host: str, rabbitmq_user: str) -> None:
    console = Console()

    agent_cfg = config.get("agent", [{}])[0]

    tools = [t["name"] for t in config.get("tools_agents", []) if t.get("enabled")]

    active_observers = []
    for obs_type, items in config.get("observers", {}).items():
        for item in items:
            if item.get("enabled"):
                params = item.get("parameters", {})
                detail = next(iter(params.values()), "") if params else ""
                active_observers.append((obs_type, str(detail)))

    mcp_servers = list((agent_cfg.get("mcp") or {}).get("mcpServers", {}).keys())

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column()

    table.add_row("Agent ID", f"[yellow]{agent_id}[/yellow]")
    table.add_row("Model", f"[green]{agent_cfg.get('model', '—')}[/green]")
    table.add_row("", "")

    if tools:
        table.add_row("[bold]Aktivní Tools agenti[/bold]", ", ".join(tools))

    table.add_row("", "")

    if active_observers:
        obs_lines = "\n".join(f"[cyan]{t}[/cyan]  {d}" for t, d in active_observers)
        table.add_row("[bold]Aktivní Observers[/bold]", obs_lines)

    table.add_row("", "")

    if mcp_servers:
        table.add_row("[bold]MCP[/bold]", ", ".join(mcp_servers))

    table.add_row("", "")
    table.add_row("RabbitMQ exchange", f"{agent_id}")
    table.add_row("RabbitMQ", f"[link]http://{rabbitmq_host}:15672[/link]  (user: {rabbitmq_user})")

    console.print(Panel(table, title="[bold white]PREFECT[/bold white]", border_style="bright_blue"))
