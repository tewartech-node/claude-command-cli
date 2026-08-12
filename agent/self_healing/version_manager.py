"""
Version Manager: Git-based Version Control and Rollback
Tracks code changes, enables rollback to known good states
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class VersionManager:
    """Manages code versions and enables rollback"""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.git_available = self._check_git()

    def _check_git(self) -> bool:
        """Check if git is available and repo is initialized"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def create_checkpoint(self, message: str = "Auto-checkpoint") -> Dict[str, Any]:
        """Create a checkpoint (commit) of current state"""
        if not self.git_available:
            return {"error": "Git not available"}

        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.repo_root,
                capture_output=True,
            )

            # Commit with timestamp
            commit_message = f"{message} - {datetime.now().isoformat()}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # Get commit hash
                commit_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                )

                commit_hash = commit_result.stdout.strip()

                return {
                    "success": True,
                    "message": commit_message,
                    "commit_hash": commit_hash,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                }

        except Exception as e:
            return {"error": str(e)}

    def get_recent_commits(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent commits from repository"""
        if not self.git_available:
            return []

        try:
            result = subprocess.run(
                ["git", "log", f"--max-count={count}", "--format=%H|%s|%ai|%an"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            commits = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|")
                    if len(parts) == 4:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1],
                            "timestamp": parts[2],
                            "author": parts[3],
                        })

            return commits

        except Exception:
            return []

    def get_changed_files(self, from_commit: str = "HEAD~1", to_commit: str = "HEAD") -> List[str]:
        """Get files changed between two commits"""
        if not self.git_available:
            return []

        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{from_commit}..{to_commit}"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            return result.stdout.strip().split("\n") if result.stdout else []

        except Exception:
            return []

    def rollback_to_commit(self, commit_hash: str, create_backup: bool = True) -> Dict[str, Any]:
        """Rollback to a specific commit"""
        if not self.git_available:
            return {"error": "Git not available"}

        try:
            # Create backup checkpoint first
            if create_backup:
                backup = self.create_checkpoint(f"Backup before rollback to {commit_hash}")
                if "error" in backup:
                    return backup

            # Reset to commit
            result = subprocess.run(
                ["git", "reset", "--hard", commit_hash],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Rolled back to {commit_hash}",
                    "backup_commit": backup.get("commit_hash") if create_backup else None,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "error": result.stderr,
                }

        except Exception as e:
            return {"error": str(e)}

    def find_last_good_state(self, metric_check: callable) -> Optional[Dict[str, Any]]:
        """Find last commit where system was in good state"""
        if not self.git_available:
            return None

        commits = self.get_recent_commits(count=50)

        for commit in commits:
            # Try checking out commit (without modifying working tree)
            result = subprocess.run(
                ["git", "show", f"{commit['hash']}:agent/core/agent.py"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # For now, just return first commit
                # In real implementation, would check metrics
                return commit

        return None

    def get_blame_for_issue(self, filepath: str, start_line: int = 1, end_line: int = 50) -> List[Dict[str, Any]]:
        """Get git blame for specific lines to trace issue origin"""
        if not self.git_available:
            return []

        try:
            result = subprocess.run(
                ["git", "blame", "-L", f"{start_line},{end_line}", filepath],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            blame_lines = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    # Parse blame output
                    # Format: hash (author date) line_number content
                    blame_lines.append({
                        "line": line[:50],  # Simplified parsing
                        "timestamp": datetime.now().isoformat(),
                    })

            return blame_lines

        except Exception:
            return []

    def get_diff_since_commit(self, commit_hash: str) -> str:
        """Get diff since a specific commit"""
        if not self.git_available:
            return ""

        try:
            result = subprocess.run(
                ["git", "diff", commit_hash, "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            return result.stdout

        except Exception:
            return ""

    def tag_stable_version(self, version_name: str) -> Dict[str, Any]:
        """Tag current commit as a stable version"""
        if not self.git_available:
            return {"error": "Git not available"}

        try:
            result = subprocess.run(
                ["git", "tag", "-a", version_name, "-m", f"Stable version {version_name}"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "tag": version_name,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {"error": result.stderr}

        except Exception as e:
            return {"error": str(e)}

    def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all version tags"""
        if not self.git_available:
            return []

        try:
            result = subprocess.run(
                ["git", "tag", "-l", "--format=%(refname:short)|%(creatordate:iso)"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            tags = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|")
                    if len(parts) == 2:
                        tags.append({
                            "tag": parts[0],
                            "created": parts[1],
                        })

            return tags

        except Exception:
            return []

    def get_version_history(self, days: int = 7) -> Dict[str, Any]:
        """Get version history for last N days"""
        if not self.git_available:
            return {}

        try:
            since_date = (datetime.now() - timedelta(days=days)).isoformat()

            result = subprocess.run(
                ["git", "log", f"--since={since_date}", "--format=%H|%s|%ai"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            commits = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|")
                    if len(parts) == 3:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1],
                            "timestamp": parts[2],
                        })

            return {
                "period_days": days,
                "commits": len(commits),
                "history": commits,
            }

        except Exception:
            return {}

    def create_recovery_snapshot(self) -> Dict[str, Any]:
        """Create a full recovery snapshot"""
        return {
            "timestamp": datetime.now().isoformat(),
            "current_commit": self.get_recent_commits(1),
            "tags": self.get_all_tags(),
            "branches": self._get_branches(),
            "status": self._get_status(),
        }

    def _get_branches(self) -> List[str]:
        """Get list of branches"""
        if not self.git_available:
            return []

        try:
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            return [b.strip() for b in result.stdout.split("\n") if b.strip()]

        except Exception:
            return []

    def _get_status(self) -> Dict[str, Any]:
        """Get git status"""
        if not self.git_available:
            return {}

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )

            changes = {
                "modified": 0,
                "added": 0,
                "deleted": 0,
                "untracked": 0,
            }

            for line in result.stdout.split("\n"):
                if line.startswith(" M"):
                    changes["modified"] += 1
                elif line.startswith("A"):
                    changes["added"] += 1
                elif line.startswith(" D"):
                    changes["deleted"] += 1
                elif line.startswith("??"):
                    changes["untracked"] += 1

            return changes

        except Exception:
            return {}
