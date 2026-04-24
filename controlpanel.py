import os, yaml
from pathlib import Path

import typer
from dotenv import load_dotenv
from helpers import load_or_create_agent_id, print_startup_banner

BASE_DIR = Path(__file__).resolve().parent
config_path = BASE_DIR.parent / "config.yaml"

load_dotenv()

app = typer.Typer()

@app.command()
def info():
    with open(BASE_DIR.parent / "config.yaml") as f:
        config = yaml.safe_load(f)
    print_startup_banner(
        load_or_create_agent_id(config.get("agent", [{}])[0].get("nickname")),
        config,
        os.environ.get("RABBITMQ_HOST", "0.0.0.0"),
        os.environ.get("RABBITMQ_USERNAME", ""),
    )

if __name__ == "__main__":
    app()
