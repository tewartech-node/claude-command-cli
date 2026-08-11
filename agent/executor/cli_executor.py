"""
CLI Executor: Brain's body
Runs CLI commands autonomously
Supports both CLI and direct API (for Termux/Android compatibility)
"""

import asyncio
import subprocess
import json
from pathlib import Path
import os


class CLIExecutor:
    """Execute CLI commands programmatically"""

    def __init__(self, cli_path: str = "./cli/go/bin/claude"):
        self.cli_path = cli_path
        self.cmd_count = 0
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")

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
        """Ask Claude via CLI, fallback to direct API (Android)"""
        result = await self.execute_command(
            "ai",
            {"prompt": prompt}
        )

        if result.get("success"):
            return result.get("output", "")

        # Android fallback: direct API call
        if self.api_key:
            return await self._ask_claude_api(prompt)

        return f"Error: {result.get('error', 'CLI unavailable')}"

    async def _ask_claude_api(self, prompt: str) -> str:
        """Call Claude API directly (Android Termux fallback)"""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("content", [{}])[0].get("text", "")
                else:
                    return f"API error {response.status_code}: {response.text}"
        except ImportError:
            return "Error: httpx not installed"
        except Exception as e:
            return f"API error: {e}"

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
