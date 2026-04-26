import re
import subprocess
from pydantic_ai import RunContext, Tool
from pydantic import BaseModel, Field
from system.constants import STORAGE_DIR

BLOCKED_PATTERNS = [
    r"rm\s+-rf?\s+/",
    r"rm\s+--no-preserve-root",
    r"mkfs\b",
    r"dd\s+.*of=/dev/",
    r">\s*/dev/sd",
    r"chmod\s+-R\s+777\s+/",
    r"chown\s+-R\s+.*\s+/",
    r":\(\)\s*\{.*\}",         # fork bomb
    r"curl\s+.*\|\s*bash",
    r"wget\s+.*\|\s*bash",
    r"base64\s+.*\|\s*bash",
    r"shutdown\b",
    r"reboot\b",
    r"halt\b",
    r"init\s+0\b",
    r"systemctl\s+(stop|disable|mask)\s+",
    r"iptables\s+.*-F",
    r"passwd\b",
    r"userdel\b",
    r"useradd\b",
]

MAX_SCRIPT_LENGTH = 2000
TIMEOUT_SECONDS = 30

ALLOWED_DIRS = [
    STORAGE_DIR,
    "/tmp",
]

class RunBashParams(BaseModel):
    script: str = Field(description="Bash příkaz nebo skript k vykonání")


class RunBashResult(BaseModel):
    success: bool = Field(description="Zda příkaz skončil s návratovým kódem 0")
    return_code: int = Field(description="Návratový kód procesu")
    stdout: str = Field(description="Standardní výstup příkazu")
    stderr: str = Field(description="Chybový výstup příkazu")
    blocked: bool = Field(default=False, description="Zda byl příkaz zablokován bezpečnostní kontrolou")
    blocked_reason: str = Field(default="", description="Důvod zablokování příkazu")


def _check_script(script: str) -> tuple[bool, str]:
    if len(script) > MAX_SCRIPT_LENGTH:
        return True, f"Skript překračuje maximální délku {MAX_SCRIPT_LENGTH} znaků"

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, script, re.IGNORECASE):
            return True, f"Skript obsahuje zakázaný vzor: {pattern}"

    return False, ""


def run_bash(ctx: RunContext, params: RunBashParams) -> RunBashResult:
    blocked, reason = _check_script(params.script)
    if blocked:
        return RunBashResult(
            success=False,
            return_code=-1,
            stdout="",
            stderr="",
            blocked=True,
            blocked_reason=reason,
        )

    try:
        result = subprocess.run(
            params.script,
            shell=True,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=STORAGE_DIR,
        )
    except subprocess.TimeoutExpired:
        return RunBashResult(
            success=False,
            return_code=-1,
            stdout="",
            stderr="",
            blocked=True,
            blocked_reason=f"Příkaz překročil časový limit {TIMEOUT_SECONDS}s",
        )

    return RunBashResult(
        success=result.returncode == 0,
        return_code=result.returncode,
        stdout=result.stdout[:10_000],
        stderr=result.stderr[:2_000],
    )


tool = Tool(run_bash, description="Spuštění bash příkazu nebo skriptu")
