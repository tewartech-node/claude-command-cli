"""
Constraint System: Define and Enforce Acceptable System States
Validates system behavior against defined constraints and triggers corrections
"""

import json
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
from enum import Enum


class ConstraintViolation(Enum):
    """Severity levels for constraint violations"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Constraint:
    """A single system constraint"""

    def __init__(
        self,
        name: str,
        description: str,
        validator: Callable[[Any], bool],
        violation_severity: ConstraintViolation = ConstraintViolation.MEDIUM,
        auto_fix: Optional[Callable[[], bool]] = None,
    ):
        self.name = name
        self.description = description
        self.validator = validator
        self.violation_severity = violation_severity
        self.auto_fix = auto_fix
        self.last_checked = None
        self.is_violated = False
        self.violation_count = 0

    def check(self, value: Any) -> bool:
        """Check if constraint is satisfied"""
        self.last_checked = datetime.now().isoformat()
        self.is_violated = not self.validator(value)

        if self.is_violated:
            self.violation_count += 1

        return not self.is_violated

    def attempt_fix(self) -> bool:
        """Attempt to fix the violation"""
        if not self.is_violated or not self.auto_fix:
            return False

        try:
            success = self.auto_fix()
            if success:
                self.is_violated = False
                self.violation_count = 0
            return success
        except Exception:
            return False


class ConstraintSystem:
    """Manages all system constraints and enforces compliance"""

    def __init__(self):
        self.constraints: Dict[str, Constraint] = {}
        self.violations: List[Dict[str, Any]] = []
        self._setup_default_constraints()

    def _setup_default_constraints(self):
        """Setup critical default constraints"""

        # Success rate constraint
        self.add_constraint(
            Constraint(
                name="success_rate_minimum",
                description="Decision success rate must be >= 60%",
                validator=lambda val: val >= 60,
                violation_severity=ConstraintViolation.CRITICAL,
            )
        )

        # Confidence constraint
        self.add_constraint(
            Constraint(
                name="avg_confidence_minimum",
                description="Average decision confidence must be >= 0.5",
                validator=lambda val: val >= 0.5,
                violation_severity=ConstraintViolation.HIGH,
            )
        )

        # Database size constraint
        self.add_constraint(
            Constraint(
                name="database_size_limit",
                description="Database size must be < 1GB",
                validator=lambda val: val < 1024 * 1024 * 1024,
                violation_severity=ConstraintViolation.MEDIUM,
            )
        )

        # Memory usage constraint
        self.add_constraint(
            Constraint(
                name="memory_usage_limit",
                description="Process memory must be < 500MB",
                validator=lambda val: val < 500 * 1024 * 1024,
                violation_severity=ConstraintViolation.HIGH,
            )
        )

        # CPU usage constraint
        self.add_constraint(
            Constraint(
                name="cpu_usage_limit",
                description="CPU usage must be < 80%",
                validator=lambda val: val < 80,
                violation_severity=ConstraintViolation.MEDIUM,
            )
        )

        # Decision velocity constraint
        self.add_constraint(
            Constraint(
                name="decision_velocity_minimum",
                description="Must make at least 1 decision per hour",
                validator=lambda val: val >= 1,
                violation_severity=ConstraintViolation.LOW,
            )
        )

        # Learning progress constraint
        self.add_constraint(
            Constraint(
                name="learning_progress",
                description="Must learn at least 1 pattern per day",
                validator=lambda val: val >= 1,
                violation_severity=ConstraintViolation.LOW,
            )
        )

        # Error rate constraint
        self.add_constraint(
            Constraint(
                name="error_rate_limit",
                description="Error rate must be < 5%",
                validator=lambda val: val < 5,
                violation_severity=ConstraintViolation.HIGH,
            )
        )

        # Code health constraint
        self.add_constraint(
            Constraint(
                name="critical_code_issues",
                description="Must have no critical code issues",
                validator=lambda val: val == 0,
                violation_severity=ConstraintViolation.CRITICAL,
            )
        )

        # Data quality constraint
        self.add_constraint(
            Constraint(
                name="data_integrity",
                description="Database integrity must be intact",
                validator=lambda val: val == "ok",
                violation_severity=ConstraintViolation.CRITICAL,
            )
        )

    def add_constraint(self, constraint: Constraint):
        """Add a new constraint to the system"""
        self.constraints[constraint.name] = constraint

    def check_constraint(self, constraint_name: str, value: Any) -> Dict[str, Any]:
        """Check a specific constraint"""
        if constraint_name not in self.constraints:
            return {"error": f"Constraint '{constraint_name}' not found"}

        constraint = self.constraints[constraint_name]
        is_satisfied = constraint.check(value)

        result = {
            "constraint": constraint_name,
            "description": constraint.description,
            "satisfied": is_satisfied,
            "value": value,
            "timestamp": datetime.now().isoformat(),
        }

        if not is_satisfied:
            self.violations.append({
                "constraint": constraint_name,
                "severity": constraint.violation_severity.value,
                "timestamp": datetime.now().isoformat(),
                "value": value,
            })

        return result

    def check_all_constraints(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Check all constraints against provided metrics"""
        results = []
        violations = []

        for constraint_name, constraint in self.constraints.items():
            if constraint_name not in metrics:
                continue

            value = metrics[constraint_name]
            is_satisfied = constraint.check(value)

            results.append({
                "constraint": constraint_name,
                "satisfied": is_satisfied,
                "value": value,
                "timestamp": datetime.now().isoformat(),
            })

            if not is_satisfied:
                violations.append({
                    "constraint": constraint_name,
                    "severity": constraint.violation_severity.value,
                    "description": constraint.description,
                    "value": value,
                })

        return {
            "total_constraints": len(results),
            "passed": len([r for r in results if r["satisfied"]]),
            "failed": len([r for r in results if not r["satisfied"]]),
            "violations": violations,
            "results": results,
        }

    def auto_fix_violations(self) -> Dict[str, Any]:
        """Automatically fix constraint violations"""
        fixes = []

        for constraint in self.constraints.values():
            if constraint.is_violated and constraint.auto_fix:
                success = constraint.attempt_fix()
                fixes.append({
                    "constraint": constraint.name,
                    "fix_attempted": True,
                    "fix_successful": success,
                })

        return {
            "fixes_attempted": len(fixes),
            "fixes_successful": len([f for f in fixes if f["fix_successful"]]),
            "fixes": fixes,
        }

    def get_violations_by_severity(self, severity: ConstraintViolation) -> List[Dict[str, Any]]:
        """Get all violations of a specific severity"""
        return [
            v for v in self.violations
            if v["severity"] == severity.value
        ]

    def get_critical_violations(self) -> List[Dict[str, Any]]:
        """Get all critical violations"""
        return self.get_violations_by_severity(ConstraintViolation.CRITICAL)

    def get_compliance_score(self) -> float:
        """Calculate overall compliance score (0-100)"""
        if not self.constraints:
            return 100.0

        satisfied = sum(1 for c in self.constraints.values() if not c.is_violated)
        return (satisfied / len(self.constraints)) * 100

    def define_custom_constraint(
        self,
        name: str,
        description: str,
        validator_func: Callable[[Any], bool],
        severity: str = "medium",
    ) -> bool:
        """Define a custom constraint at runtime"""
        try:
            severity_map = {
                "critical": ConstraintViolation.CRITICAL,
                "high": ConstraintViolation.HIGH,
                "medium": ConstraintViolation.MEDIUM,
                "low": ConstraintViolation.LOW,
            }

            constraint = Constraint(
                name=name,
                description=description,
                validator=validator_func,
                violation_severity=severity_map.get(severity, ConstraintViolation.MEDIUM),
            )

            self.add_constraint(constraint)
            return True

        except Exception:
            return False

    def get_constraint_report(self) -> Dict[str, Any]:
        """Generate comprehensive constraint compliance report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "compliance_score": self.get_compliance_score(),
            "total_constraints": len(self.constraints),
            "violations_critical": len(self.get_critical_violations()),
            "violations_total": len(self.violations),
            "constraints": {
                name: {
                    "description": c.description,
                    "violated": c.is_violated,
                    "violation_count": c.violation_count,
                    "last_checked": c.last_checked,
                }
                for name, c in self.constraints.items()
            },
        }
