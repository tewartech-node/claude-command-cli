"""
Reasoning: Decision-making engine
Analyzes state, generates options, chooses best action
"""


class Reasoning:
    """Strategic thinking and decision-making"""

    def __init__(self):
        self.decisions_made = 0

    def analyze(self, state: dict, memory=None) -> dict:
        """Analyze current state"""
        analysis = {
            "timestamp": state.get("timestamp"),
            "summary": "System nominal",
            "issues": [],
            "opportunities": [],
            "confidence": 0.75
        }

        # Check for issues
        if state.get("error_count", 0) > 0:
            analysis["issues"].append("Errors detected")
            analysis["summary"] = "Issues detected - need intervention"

        if state.get("performance_warning"):
            analysis["issues"].append("Performance degradation")

        # Identify opportunities
        if state.get("cpu_usage", 0) < 30:
            analysis["opportunities"].append("CPU headroom available")

        if state.get("can_optimize"):
            analysis["opportunities"].append("Optimization opportunities")

        return analysis

    def generate_options(self, analysis: dict) -> list:
        """Generate action options based on analysis"""
        options = []

        # If issues detected
        if analysis.get("issues"):
            for issue in analysis["issues"]:
                if "performance" in issue.lower():
                    options.append({
                        "name": "diagnose_performance",
                        "command": "ai",
                        "args": {
                            "prompt": "What are the main performance bottlenecks?"
                        },
                        "priority": 1
                    })

                if "error" in issue.lower():
                    options.append({
                        "name": "check_errors",
                        "command": "status",
                        "priority": 1
                    })

        # If opportunities
        if analysis.get("opportunities"):
            options.append({
                "name": "optimize_system",
                "command": "ai",
                "args": {
                    "prompt": "What optimizations would improve performance?"
                },
                "priority": 2
            })

        # Default: just observe
        if not options:
            options.append({
                "name": "observe",
                "command": "status",
                "priority": 3
            })

        return options

    def choose_best(self, options: list) -> dict:
        """Choose best option from safe options"""
        if not options:
            return {"name": "observe", "command": "status"}

        # Sort by priority (lower is higher priority)
        sorted_options = sorted(options, key=lambda x: x.get("priority", 999))

        # Return highest priority
        return sorted_options[0]
