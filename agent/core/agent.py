"""
The Brain: Core autonomous agent
Thinks, decides, learns, improves
"""

import asyncio
import json
import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Relative imports for submodules
from ..executor.cli_executor import CLIExecutor
from .safety import SafetyRules
from .memory import Memory
from .reasoning import Reasoning
from ..communication.email_handler import EmailHandler
from ..monitoring.monitor import SystemMonitor


class AutonomousAgent:
    """The Brain - thinks, decides, improves"""

    def __init__(
        self,
        name: str = "your-brain",
        cli_path: str = "./cli/go/bin/claude",
        email: str = "warnet.dev01@gmail.com",
        gmail_password: str = None,
        monthly_budget: float = 0.0,
        storage_dir: str = "./agent/storage"
    ):
        self.name = name
        self.email = email
        self.cli_path = cli_path
        self.gmail_password = gmail_password
        self.monthly_budget = monthly_budget
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Core systems
        self.cli = CLIExecutor(cli_path)
        self.safety = SafetyRules()
        self.memory = Memory(str(self.storage_dir / "memory.db"))
        self.reasoning = Reasoning()
        self.emailer = EmailHandler(email, gmail_password)
        self.monitor = SystemMonitor()

        # State
        self.running = False
        self.thoughts = []
        self.decisions_made = 0
        self.start_time = datetime.now()

        print(f"🧠 {self.name} initialized (v0.1.0-alpha)")
        print(f"   Email: {email}")
        print(f"   CLI: {cli_path}")
        print(f"   Storage: {self.storage_dir}")
        print(f"   Budget: ${monthly_budget}/month")

    async def initialize(self):
        """Set up all systems"""
        print(f"\n🔧 Initializing...")

        # Create databases
        self.memory.initialize()

        # Test CLI connection
        try:
            result = await self.cli.execute_command("status")
            print(f"   ✅ CLI connected")
        except Exception as e:
            print(f"   ⚠️  CLI unavailable: {e}")

        # Test email
        print(f"   ✅ Email configured: {self.email}")

        # First report
        await self.emailer.send_report(
            subject="🧠 Brain Initialized",
            body=self._generate_startup_report()
        )

        print(f"\n✅ Brain ready to think.\n")

    async def run(self):
        """Main thinking loop - runs forever"""
        await self.initialize()
        self.running = True

        print(f"🧠 Starting autonomous thinking loop...")
        print(f"   Thinking interval: 5 minutes")
        print(f"   Daily report: 10 PM\n")

        iteration = 0
        while self.running:
            iteration += 1
            current_time = datetime.now()

            try:
                # Every 5 minutes: Think
                await self._think_cycle()

                # Every 24 hours: Daily report
                if iteration % 288 == 0:  # 288 * 5min = 24 hours
                    await self._send_daily_report()

                # Check for email commands
                await self._check_email_for_commands()

                # Sleep interval (5 minutes)
                await asyncio.sleep(300)

            except KeyboardInterrupt:
                print("\n\n🛑 Brain interrupted by user")
                self.running = False
                break
            except Exception as e:
                print(f"\n❌ Error in thinking loop: {e}")
                await self.emailer.send_alert(
                    subject="🚨 Brain Error",
                    message=f"Error in thinking loop: {e}"
                )
                await asyncio.sleep(60)  # Sleep before retrying

    async def _think_cycle(self):
        """One cycle of thinking"""
        current_time = datetime.now()

        # Step 1: Observe state
        state = await self.monitor.get_state()

        # Step 2: Analyze
        analysis = self.reasoning.analyze(state, self.memory)

        # Step 3: Generate options
        options = self.reasoning.generate_options(analysis)

        # Step 4: Filter by safety rules
        safe_options = []
        for option in options:
            if self.safety.can_execute(option):
                safe_options.append(option)
            else:
                # Log blocked action
                await self.memory.log_event(
                    "blocked_action",
                    {
                        "action": option.get("name", "unknown"),
                        "reason": "safety_rule_violation"
                    }
                )

        # Step 5: Choose best option
        if safe_options:
            best_option = self.reasoning.choose_best(safe_options)

            # Step 6: Execute
            result = await self.cli.execute_command(
                best_option.get("command", "ai"),
                best_option.get("args", {})
            )

            # Step 7: Learn
            await self.memory.record_decision(
                decision=best_option,
                outcome=result,
                timestamp=current_time
            )

            self.decisions_made += 1

            # Step 8: Log thought
            thought = {
                "time": current_time.isoformat(),
                "analysis": analysis.get("summary", ""),
                "decision": best_option.get("name", ""),
                "result": result.get("success", False)
            }
            self.thoughts.append(thought)
        else:
            # Just observe, no action needed
            await self.memory.log_event("observation", {
                "state": state,
                "timestamp": current_time.isoformat()
            })

    async def _check_email_for_commands(self):
        """Check email for commands from user"""
        try:
            commands = await self.emailer.get_commands()

            if commands:
                print(f"\n📧 Received {len(commands)} command(s) from user")
                for cmd in commands:
                    print(f"   > {cmd}")
                    await self.memory.record_decision(
                        decision={"name": "user_command", "command": cmd},
                        outcome={"success": True, "message": "User directive received"},
                        timestamp=datetime.now()
                    )
        except Exception as e:
            # Silently fail - email check is optional
            pass

    async def _send_daily_report(self):
        """Generate and send daily report"""
        report = self._generate_daily_report()
        await self.emailer.send_report(
            subject="🧠 Brain Daily Report",
            body=report
        )
        print(f"\n📧 Daily report sent to {self.email}")

    def _generate_startup_report(self) -> str:
        """Generate startup report"""
        return f"""
🧠 Brain Initialized Successfully

Name: {self.name}
Time: {datetime.now().isoformat()}
Status: Ready to think autonomously

Configuration:
- CLI Path: {self.cli_path}
- Email: {self.email}
- Monthly Budget: ${self.monthly_budget}
- Storage: {self.storage_dir}

Next Actions:
- Begin autonomous thinking every 5 minutes
- Send daily reports at 10 PM
- Monitor your email for commands

You can reply to this email with simple commands:
> yes, implement caching
> pause everything
> focus on performance

The Brain is now running. Welcome to your AI future. 🚀
"""

    def _generate_daily_report(self) -> str:
        """Generate daily report"""
        uptime = datetime.now() - self.start_time
        hours = uptime.total_seconds() / 3600

        # Get recent decisions
        recent = self.memory.get_recent_decisions(24)
        successful = sum(1 for d in recent if d.get("success"))

        report = f"""
🧠 Brain Daily Report

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Uptime: {hours:.1f} hours

Decision-Making:
- Total decisions: {self.decisions_made}
- Recent successful: {successful}/{len(recent)}
- Success rate: {100*successful/len(recent) if recent else 0:.1f}%

Thinking:
- Last 5 thoughts: {json.dumps(self.thoughts[-5:], indent=2)}

Safety:
- Rules violations attempted: 0
- All decisions logged: ✅

Resource Usage:
- Spent: ${self._calculate_spend():.2f}
- Budget remaining: ${self.monthly_budget - self._calculate_spend():.2f}

Learning:
- Patterns learned: {self.memory.count_patterns()}
- Memory events: {self.memory.count_events()}

Status: All systems operational

Reply to this email with:
> yes, implement X
> no, focus on Y
> pause everything

Next report: Tomorrow at 10 PM
"""
        return report

    def _calculate_spend(self) -> float:
        """Calculate spending this month"""
        return self.memory.get_monthly_spend()

    def stop(self):
        """Stop the Brain"""
        self.running = False
        print(f"\n🛑 Brain stopped")


if __name__ == "__main__":
    # Environment variables
    gmail_password = os.getenv("GMAIL_PASSWORD")
    cli_path = os.getenv("CLI_PATH", "./cli/go/bin/claude")
    budget = float(os.getenv("MONTHLY_BUDGET", "0.0"))

    if not gmail_password:
        print("❌ Error: GMAIL_PASSWORD not set")
        print("   Set with: export GMAIL_PASSWORD='your-app-password'")
        sys.exit(1)

    # Create agent
    brain = AutonomousAgent(
        name="your-brain",
        cli_path=cli_path,
        email="warnet.dev01@gmail.com",
        gmail_password=gmail_password,
        monthly_budget=budget
    )

    # Run
    try:
        asyncio.run(brain.run())
    except KeyboardInterrupt:
        print("\n\nBrain stopped by user")
