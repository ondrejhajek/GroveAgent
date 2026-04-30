from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

AGENT_DIR = BASE_DIR / "agent"

STORAGE_DIR = AGENT_DIR / "storage"

LOG_DIR = AGENT_DIR / "logs"

MEMORY_FILE = STORAGE_DIR / "MEMORY.md"

TASKS_FILE = STORAGE_DIR / "tasks.json"

CONFIG_FILE = AGENT_DIR / "config.yaml"