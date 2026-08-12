"""
Self-Healing Code Module
========================

The Brain's meta-programming layer that analyzes, diagnoses, repairs, and modifies
its own code during runtime. Enables autonomous self-improvement and bug fixes.

Core Components:
- Diagnostic Engine: Routine health scans and performance monitoring
- Code Analyzer: AST-based code introspection
- Self-Repair Engine: Automated bug detection and fixes
- Behavior Monitor: Continuous behavioral monitoring
- Constraint System: Define acceptable system states
- Version Manager: Git-based rollback and versioning
"""

from .diagnostic_engine import DiagnosticEngine
from .code_analyzer import CodeAnalyzer
from .self_repair import SelfRepairEngine
from .behavior_monitor import BehaviorMonitor
from .constraint_system import ConstraintSystem
from .version_manager import VersionManager
from .health_dashboard import HealthDashboard

__all__ = [
    "DiagnosticEngine",
    "CodeAnalyzer",
    "SelfRepairEngine",
    "BehaviorMonitor",
    "ConstraintSystem",
    "VersionManager",
    "HealthDashboard",
]
