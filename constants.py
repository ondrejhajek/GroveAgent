from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

STORAGE_DIR = BASE_DIR / "storage"

MEMORY_FILE = STORAGE_DIR / "MEMORY.md"

TASKS_FILE = STORAGE_DIR / "TASKS.md"

CONFIG_FILE = BASE_DIR / "config.yaml"