"""Whitelisted shell command tool with opt-in execution and logging."""

import os
import re
import shlex
import subprocess
from datetime import datetime
from .base import BaseTool, ToolExecutionError
from .registry import register_tool

# Simple whitelist of safe read-only/info commands (first token)
WHITELIST = {
    "ls", "df", "du", "whoami", "uname", "uptime", "id", "ps", "echo", "stat", "date"
}

# Dangerous regex patterns (case-insensitive)
DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bsudo\b",
    r"\bdd\b",
    r":\s*\(\)\s*{\s*:\|:\s*&\s*};\s*:",  # fork bomb
    r">/dev/\w+",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bmkfs\b",
    r"\bchmod\s+0\b",
    r"\bchown\s+root\b",
]

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "shell_exec.log")

def is_dangerous(command: str) -> bool:
    cmd = command.lower()
    for p in DANGEROUS_PATTERNS:
        if re.search(p, cmd, flags=re.IGNORECASE):
            return True
    return False

def log_attempt(command: str, allowed: bool, note: str = ""):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"{datetime.utcnow().isoformat()} | allowed={allowed} | cmd={command!r} | {note}\n")
    except Exception:
        pass

@register_tool
class ShellCommandTool(BaseTool):
    name = "shell"
    description = "Execute a small set of safe shell commands (whitelist). Set SHELL_ALLOW=1 to allow arbitrary commands."

    def run(self, command: str, timeout: int = 30) -> dict:
        if not command or not command.strip():
            raise ToolExecutionError("Empty command")

        if is_dangerous(command):
            log_attempt(command, allowed=False, note="blocked: dangerous pattern")
            return {"ok": False, "error": "Command blocked by safety policy (dangerous pattern detected)."}

        # Determine first token
        try:
            first = shlex.split(command)[0]
        except Exception:
            first = command.strip().split()[0]

        allow_flag = os.environ.get("SHELL_ALLOW", "") in ("1", "true", "yes")

        if first not in WHITELIST and not allow_flag:
            log_attempt(command, allowed=False, note="blocked: not whitelisted and env not set")
            return {"ok": False, "error": "Command not permitted: only a small whitelist is allowed. Set SHELL_ALLOW=1 to opt-in (risky)."}

        # Allowed: execute
        log_attempt(command, allowed=True, note="executing")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            out = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
            return {"ok": True, "result": out}
        except subprocess.TimeoutExpired:
            log_attempt(command, allowed=False, note="timeout")
            return {"ok": False, "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            log_attempt(command, allowed=False, note=f"exc:{e}")
            return {"ok": False, "error": f"Command execution failed: {str(e)}"}
