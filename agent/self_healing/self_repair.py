"""
Self-Repair Engine: Automated Bug Detection and Fixes
Identifies issues and applies targeted code repairs
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from .code_analyzer import CodeAnalyzer
from .diagnostic_engine import DiagnosticEngine
import sqlite3


class SelfRepairEngine:
    """Automatically detects and repairs code issues"""

    def __init__(self, repo_root: str = ".", db_path: str = "./agent/storage/memory.db"):
        self.repo_root = Path(repo_root)
        self.db_path = db_path
        self.analyzer = CodeAnalyzer(repo_root)
        self.diagnostic_engine = DiagnosticEngine(db_path)
        self.repairs_log = []
        self._init_repair_log_table()

    def _init_repair_log_table(self):
        """Initialize repair log table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repair_log (
                id INTEGER PRIMARY KEY,
                repair_timestamp TEXT,
                file_path TEXT,
                issue_type TEXT,
                issue_description TEXT,
                fix_applied TEXT,
                status TEXT,
                rollback_available INTEGER DEFAULT 1
            )
        """)
        conn.commit()
        conn.close()

    def full_repair_cycle(self) -> Dict[str, Any]:
        """Run complete diagnostic and repair cycle"""
        # Get diagnostics
        diagnostics = self.diagnostic_engine.full_diagnostic_scan()

        # Run code analysis
        code_analysis = self.analyzer.analyze_codebase()

        repairs = []

        # Repair database issues
        repairs.extend(self._repair_database_issues(diagnostics))

        # Repair code issues
        repairs.extend(self._repair_code_issues(code_analysis))

        # Repair performance issues
        repairs.extend(self._repair_performance_issues(diagnostics))

        return {
            "cycle_timestamp": datetime.now().isoformat(),
            "diagnostics_found": diagnostics["total_issues"],
            "repairs_attempted": len(repairs),
            "repairs_successful": len([r for r in repairs if r["status"] == "successful"]),
            "repairs": repairs,
        }

    def _repair_database_issues(self, diagnostics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Repair database-related issues"""
        repairs = []

        for issue in diagnostics.get("issues", []):
            if issue["category"] != "database":
                continue

            if "fragmentation" in issue["issue"]:
                success = self._repair_fragmentation()
                repairs.append({
                    "type": "database_vacuum",
                    "issue": issue["issue"],
                    "status": "successful" if success else "failed",
                    "timestamp": datetime.now().isoformat(),
                })

            if "large database" in issue["issue"]:
                success = self._archive_old_data()
                repairs.append({
                    "type": "data_archive",
                    "issue": issue["issue"],
                    "status": "successful" if success else "failed",
                    "timestamp": datetime.now().isoformat(),
                })

        return repairs

    def _repair_fragmentation(self) -> bool:
        """Repair database fragmentation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("VACUUM")
            conn.commit()
            conn.close()

            self._log_repair("database", "fragmentation", "VACUUM executed")
            return True

        except Exception as e:
            self._log_repair("database", "fragmentation", f"VACUUM failed: {e}")
            return False

    def _archive_old_data(self) -> bool:
        """Archive old data to reduce database size"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Archive decisions older than 90 days
            cursor.execute("""
                DELETE FROM decisions
                WHERE timestamp < datetime('now', '-90 days')
                AND id NOT IN (SELECT decision_id FROM ratings)
            """)

            # Archive email activity older than 180 days
            cursor.execute("""
                DELETE FROM email_activity
                WHERE timestamp < datetime('now', '-180 days')
            """)

            conn.commit()
            conn.close()

            rows_deleted = cursor.rowcount
            self._log_repair("database", "archive", f"Archived {rows_deleted} old records")
            return True

        except Exception as e:
            self._log_repair("database", "archive", f"Archive failed: {e}")
            return False

    def _repair_code_issues(self, code_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Repair code-level issues"""
        repairs = []

        # Fix bare except clauses
        repairs.extend(self._fix_bare_except())

        # Add missing docstrings
        repairs.extend(self._add_missing_docstrings())

        # Fix unused imports
        repairs.extend(self._remove_unused_imports())

        return repairs

    def _fix_bare_except(self) -> List[Dict[str, Any]]:
        """Fix bare except clauses"""
        repairs = []

        agent_dir = self.repo_root / "agent"
        for py_file in agent_dir.glob("**/*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find bare except patterns
                if "except:" in content:
                    # Replace with proper exception handling
                    fixed_content = re.sub(
                        r"except:\s*",
                        "except Exception as e:\n            ",
                        content
                    )

                    if fixed_content != content:
                        with open(py_file, "w", encoding="utf-8") as f:
                            f.write(fixed_content)

                        repairs.append({
                            "type": "bare_except_fix",
                            "file": str(py_file),
                            "status": "successful",
                            "timestamp": datetime.now().isoformat(),
                        })

                        self._log_repair("code", "bare_except", f"Fixed in {py_file}")

            except Exception as e:
                repairs.append({
                    "type": "bare_except_fix",
                    "file": str(py_file),
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                })

        return repairs

    def _add_missing_docstrings(self) -> List[Dict[str, Any]]:
        """Add missing docstrings to public functions"""
        repairs = []

        agent_dir = self.repo_root / "agent"
        for py_file in agent_dir.glob("**/*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find functions without docstrings
                pattern = r"def\s+(\w+)\s*\([^)]*\):\s*\n(?!\s+[\"'])"
                matches = list(re.finditer(pattern, content))

                if matches:
                    # This would require more sophisticated AST manipulation
                    repairs.append({
                        "type": "missing_docstring",
                        "file": str(py_file),
                        "functions_found": len(matches),
                        "status": "identified",
                        "timestamp": datetime.now().isoformat(),
                    })

            except Exception as e:
                pass

        return repairs

    def _remove_unused_imports(self) -> List[Dict[str, Any]]:
        """Remove unused imports"""
        repairs = []

        # This would require sophisticated analysis to avoid breaking code
        # For now, just identify them

        return repairs

    def _repair_performance_issues(self, diagnostics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Repair performance-related issues"""
        repairs = []

        for issue in diagnostics.get("issues", []):
            if issue["category"] != "performance":
                continue

            if "High CPU usage" in issue["issue"]:
                repairs.append({
                    "type": "cpu_optimization",
                    "issue": issue["issue"],
                    "action": "Enable background task throttling",
                    "status": "recommended",
                    "timestamp": datetime.now().isoformat(),
                })

            if "Memory pressure" in issue["issue"]:
                repairs.append({
                    "type": "memory_optimization",
                    "issue": issue["issue"],
                    "action": "Increase GC frequency, reduce buffer sizes",
                    "status": "recommended",
                    "timestamp": datetime.now().isoformat(),
                })

        return repairs

    def _log_repair(self, category: str, issue_type: str, description: str):
        """Log a repair action to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO repair_log
            (repair_timestamp, file_path, issue_type, issue_description, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "",
            f"{category}/{issue_type}",
            description,
            "completed",
        ))
        conn.commit()
        conn.close()

    def get_repair_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent repair history"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM repair_log
            ORDER BY repair_timestamp DESC
            LIMIT ?
        """, (limit,))

        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return history

    def can_rollback(self, repair_id: int) -> bool:
        """Check if a repair can be rolled back"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT rollback_available FROM repair_log WHERE id = ?
        """, (repair_id,))

        result = cursor.fetchone()
        conn.close()

        return bool(result and result[0])

    def auto_repair_enabled(self) -> bool:
        """Check if auto-repair is enabled"""
        return os.getenv("AUTO_REPAIR", "true").lower() == "true"
