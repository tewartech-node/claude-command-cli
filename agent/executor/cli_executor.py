"""
CLI Executor: Brain's body
Runs CLI commands autonomously
"""

import asyncio
import subprocess
import json
from pathlib import Path


class CLIExecutor:
    """Execute CLI commands programmatically"""

    def __init__(self, cli_path: str = "./cli/go/bin/claude"):
        self.cli_path = cli_path
        self.cmd_count = 0

    async def execute_command(
        self,
        command: str,
        args: dict = None
    ) -> dict:
        """Execute a CLI command"""
        args = args or {}

        try:
            # Build command
            cmd = [self.cli_path, command]

            # Add arguments
            if args:
                cmd.append(json.dumps(args))

            # Run asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            self.cmd_count += 1

            return {
                "success": process.returncode == 0,
                "command": command,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr else "",
                "return_code": process.returncode
            }

        except FileNotFoundError:
            return {
                "success": False,
                "command": command,
                "error": f"CLI not found: {self.cli_path}",
                "return_code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "return_code": -1
            }

    async def ask_claude(self, prompt: str) -> str:
        """Use 'claude ai' to ask a question"""
        result = await self.execute_command(
            "ai",
            {"prompt": prompt}
        )
        return result.get("output", "")

    async def check_status(self) -> dict:
        """Use 'claude status' to check system"""
        result = await self.execute_command("status")
        return result

    async def github_action(self, action: str) -> dict:
        """Use 'claude gh' for GitHub operations"""
        result = await self.execute_command(
            "gh",
            {"action": action}
        )
        return result

    def get_stats(self) -> dict:
        """Get execution statistics"""
        return {
            "commands_executed": self.cmd_count
        }
