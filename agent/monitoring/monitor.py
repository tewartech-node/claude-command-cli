"""
System Monitor: Watches infrastructure
Detects problems, triggers interventions
"""

import psutil
from datetime import datetime


class SystemMonitor:
    """Monitor system health"""

    def __init__(self):
        self.observations = []

    async def get_state(self) -> dict:
        """Get current system state"""
        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            state = {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": cpu,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "performance_warning": cpu > 75 or memory.percent > 80,
                "error_count": 0,
                "can_optimize": cpu < 50 and memory.percent < 50
            }

            self.observations.append(state)

            return state

        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "error_count": 1
            }

    def get_health_report(self) -> dict:
        """Generate health report"""
        if not self.observations:
            return {"status": "no_data"}

        latest = self.observations[-1]

        return {
            "cpu": latest.get("cpu_usage", 0),
            "memory": latest.get("memory_usage", 0),
            "disk": latest.get("disk_usage", 0),
            "healthy": latest.get("performance_warning", False) == False
        }
