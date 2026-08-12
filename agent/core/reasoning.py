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

    def choose_best(self, options: list, memory=None) -> dict:
        """Choose best option from safe options, factoring in historical confidence"""
        if not options:
            return {"name": "observe", "command": "status"}

        # Score each option: priority + confidence boost
        scored_options = []
        for option in options:
            score = option.get("priority", 999)

            # Factor in historical confidence if memory available
            if memory:
                confidence = memory.get_confidence(option.get("name", ""))
                # Adjust score: lower priority is better, confidence boost is better
                # confidence 0.9 = 0.1 penalty reduction, confidence 0.5 = 0.5 penalty reduction
                score = score * (1.0 - (confidence * 0.3))

            scored_options.append({
                "option": option,
                "score": score,
                "confidence": memory.get_confidence(option.get("name", "")) if memory else 0.5
            })

        # Sort by score (lower is better)
        sorted_options = sorted(scored_options, key=lambda x: x["score"])

        # Attach confidence to chosen option for logging
        best = sorted_options[0]["option"]
        best["confidence_score"] = sorted_options[0]["confidence"]

        return best
