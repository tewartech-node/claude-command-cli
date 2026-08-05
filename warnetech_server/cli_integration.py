"""Integration with warnetech-cli (termux-cli/warnet): triggering CLI
commands from API requests, receiving CLI outputs, logging CLI operations,
and providing a bridge between the server and local CLI workflows.

Shells out to the real Node.js entrypoint at `config.cli_entrypoint`
(`termux-cli/warnet`) rather than reimplementing its command surface —
the CLI already owns encryption, config loading, and command parsing
(see termux-cli/warnet, termux-cli/crypto.js); duplicating that here
would be exactly the kind of drift CLAUDE.md's "keep layers separated"
principle warns against.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import ServerConfig
from .logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class CLIResult:
    command: str
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    duration_ms: float

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class CLIIntegration:
    def __init__(self, config: ServerConfig, repo_root: Optional[Path] = None) -> None:
        self._config = config
        self._repo_root = repo_root or Path(__file__).resolve().parent.parent

    def _entrypoint_path(self) -> Path:
        return self._repo_root / self._config.cli_entrypoint

    def is_available(self) -> bool:
        return self._entrypoint_path().exists()

    def run_command(self, command: str, args: Optional[list[str]] = None) -> CLIResult:
        args = args or []
        entrypoint = self._entrypoint_path()

        if not entrypoint.exists():
            logger.warning("cli entrypoint not found", entrypoint=str(entrypoint))
            return CLIResult(command=command, args=tuple(args), returncode=127, stdout="", stderr=f"entrypoint not found: {entrypoint}", duration_ms=0.0)

        cmd = ["node", str(entrypoint), command, *args]
        start = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._config.cli_timeout_seconds,
                cwd=str(self._repo_root),
            )
            duration_ms = (time.monotonic() - start) * 1000
            result = CLIResult(command=command, args=tuple(args), returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr, duration_ms=duration_ms)
        except subprocess.TimeoutExpired:
            duration_ms = (time.monotonic() - start) * 1000
            result = CLIResult(command=command, args=tuple(args), returncode=124, stdout="", stderr="cli command timed out", duration_ms=duration_ms)
        except OSError as exc:
            duration_ms = (time.monotonic() - start) * 1000
            result = CLIResult(command=command, args=tuple(args), returncode=126, stdout="", stderr=str(exc), duration_ms=duration_ms)

        logger.info("cli command executed", command=command, args=args, returncode=result.returncode, duration_ms=result.duration_ms)
        return result

    def status(self) -> dict:
        return self.run_command("status").__dict__

    def trigger_from_request(self, command: str, args: Optional[list[str]] = None) -> dict:
        """The bridge routes.py calls: runs the command and returns a
        JSON-serializable dict rather than the CLIResult dataclass, so
        route handlers don't need to know about this module's types.
        """
        result = self.run_command(command, args)
        return {
            "command": result.command,
            "args": list(result.args),
            "ok": result.ok,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_ms": result.duration_ms,
        }
