import subprocess
import yaml
import typer
from dotenv import load_dotenv
from system.helpers import load_or_create_agent_id, print_startup_banner
from system.constants import CONFIG_FILE, BASE_DIR

load_dotenv()

app = typer.Typer(no_args_is_help=True)

@app.callback()
def main():
    """GroveAgent control panel."""

@app.command()
def info():
    """Vypíše konfiguraci agenta."""
    with open(CONFIG_FILE) as f:
        configuration = yaml.safe_load(f)
    print_startup_banner(
        load_or_create_agent_id(configuration.get("agent").get("nickname")),
        configuration
    )

@app.command()
def start():
    """Spustí aplikaci přes ./control.sh start."""
    script = BASE_DIR / "start.sh"
    raise typer.Exit(subprocess.call([str(script), "start"], cwd=BASE_DIR))

if __name__ == "__main__":
    app()
