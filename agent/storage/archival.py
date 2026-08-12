"""
Data Archival Module
Archive old data to compressed files to free up database space
"""

import json
import gzip
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import shutil


class DataArchival:
    """Handles data archival to external storage"""

    def __init__(
        self,
        db_path: str = "./agent/storage/memory.db",
        archive_root: str = "./agent/storage/archives",
    ):
        self.db_path = db_path
        self.archive_root = Path(archive_root)
        self.archive_root.mkdir(parents=True, exist_ok=True)

    def archive_old_decisions(
        self, days_old: int = 90, delete_after: bool = False
    ) -> Dict[str, Any]:
        """Archive decisions older than N days to compressed JSON"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days_old)
            month_key = cutoff_date.strftime("%Y-%m")

            # Create monthly archive directory
            month_archive = self.archive_root / month_key
            month_archive.mkdir(parents=True, exist_ok=True)

            # Fetch old decisions
            cursor.execute("""
                SELECT id, decision_type, confidence, success,
                       decision_data, timestamp
                FROM decisions
                WHERE timestamp < ?
                ORDER BY timestamp
            """, (cutoff_date.isoformat(),))

            archived_records = 0
            archive_file = month_archive / "decisions.json.gz"

            with gzip.open(archive_file, "wt", encoding="utf-8") as f:
                for row in cursor.fetchall():
                    record = {
                        "id": row["id"],
                        "type": row["decision_type"],
                        "confidence": row["confidence"],
                        "success": row["success"],
                        "data": row["decision_data"],
                        "timestamp": row["timestamp"],
                    }
                    f.write(json.dumps(record) + "\n")
                    archived_records += 1

            # Get file size
            archive_size = archive_file.stat().st_size

            # Optionally delete from database
            if delete_after:
                cursor.execute("""
                    DELETE FROM decisions WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                conn.commit()
                delete_count = cursor.rowcount
            else:
                delete_count = 0

            conn.close()

            return {
                "status": "success",
                "archived_records": archived_records,
                "archive_file": str(archive_file),
                "archive_size_bytes": archive_size,
                "deleted_from_db": delete_count,
                "month": month_key,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def archive_old_email_activity(
        self, days_old: int = 180, delete_after: bool = False
    ) -> Dict[str, Any]:
        """Archive old email activity records"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days_old)
            month_key = cutoff_date.strftime("%Y-%m")

            month_archive = self.archive_root / month_key
            month_archive.mkdir(parents=True, exist_ok=True)

            # Fetch old email activity
            cursor.execute("""
                SELECT id, sender_email, subject, message_id, timestamp
                FROM email_activity
                WHERE timestamp < ?
                ORDER BY timestamp
            """, (cutoff_date.isoformat(),))

            archived_records = 0
            archive_file = month_archive / "email-activity.json.gz"

            with gzip.open(archive_file, "wt", encoding="utf-8") as f:
                for row in cursor.fetchall():
                    record = {
                        "id": row["id"],
                        "sender": row["sender_email"],
                        "subject": row["subject"],
                        "message_id": row["message_id"],
                        "timestamp": row["timestamp"],
                    }
                    f.write(json.dumps(record) + "\n")
                    archived_records += 1

            archive_size = archive_file.stat().st_size

            if delete_after:
                cursor.execute("""
                    DELETE FROM email_activity WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                conn.commit()
                delete_count = cursor.rowcount
            else:
                delete_count = 0

            conn.close()

            return {
                "status": "success",
                "archived_records": archived_records,
                "archive_file": str(archive_file),
                "archive_size_bytes": archive_size,
                "deleted_from_db": delete_count,
                "month": month_key,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def archive_old_traffic_activity(
        self, days_old: int = 180, delete_after: bool = False
    ) -> Dict[str, Any]:
        """Archive old traffic activity records"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days_old)
            month_key = cutoff_date.strftime("%Y-%m")

            month_archive = self.archive_root / month_key
            month_archive.mkdir(parents=True, exist_ok=True)

            # Fetch old traffic activity
            cursor.execute("""
                SELECT id, domain, path, time_spent, category, timestamp
                FROM traffic_activity
                WHERE timestamp < ?
                ORDER BY timestamp
            """, (cutoff_date.isoformat(),))

            archived_records = 0
            archive_file = month_archive / "traffic-activity.json.gz"

            with gzip.open(archive_file, "wt", encoding="utf-8") as f:
                for row in cursor.fetchall():
                    record = {
                        "id": row["id"],
                        "domain": row["domain"],
                        "path": row["path"],
                        "time_spent": row["time_spent"],
                        "category": row["category"],
                        "timestamp": row["timestamp"],
                    }
                    f.write(json.dumps(record) + "\n")
                    archived_records += 1

            archive_size = archive_file.stat().st_size

            if delete_after:
                cursor.execute("""
                    DELETE FROM traffic_activity WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                conn.commit()
                delete_count = cursor.rowcount
            else:
                delete_count = 0

            conn.close()

            return {
                "status": "success",
                "archived_records": archived_records,
                "archive_file": str(archive_file),
                "archive_size_bytes": archive_size,
                "deleted_from_db": delete_count,
                "month": month_key,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def archive_all_old_data(self, delete_after: bool = False) -> Dict[str, Any]:
        """Archive all old data"""
        return {
            "decisions": self.archive_old_decisions(days_old=90, delete_after=delete_after),
            "email": self.archive_old_email_activity(days_old=180, delete_after=delete_after),
            "traffic": self.archive_old_traffic_activity(days_old=180, delete_after=delete_after),
            "timestamp": datetime.now().isoformat(),
        }

    def get_archive_stats(self) -> Dict[str, Any]:
        """Get statistics about archives"""
        try:
            total_size = 0
            file_count = 0
            months = set()

            for archive_file in self.archive_root.glob("**/*.gz"):
                total_size += archive_file.stat().st_size
                file_count += 1
                month = archive_file.parent.name
                months.add(month)

            return {
                "archive_root": str(self.archive_root),
                "total_files": file_count,
                "total_size_bytes": total_size,
                "total_size_gb": total_size / 1024 / 1024 / 1024,
                "months_archived": sorted(list(months)),
                "status": "OK",
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def retrieve_archived_data(
        self, month: str, data_type: str = "decisions"
    ) -> List[Dict[str, Any]]:
        """Retrieve archived data for a specific month"""
        try:
            archive_file = self.archive_root / month / f"{data_type}.json.gz"

            if not archive_file.exists():
                return []

            records = []
            with gzip.open(archive_file, "rt", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))

            return records

        except Exception as e:
            return []

    def cleanup_database(self) -> Dict[str, Any]:
        """Clean up database after archival"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Run VACUUM to reclaim space
            cursor.execute("VACUUM")

            conn.commit()
            conn.close()

            # Get new database size
            db_size = Path(self.db_path).stat().st_size

            return {
                "status": "success",
                "action": "VACUUM",
                "database_size_bytes": db_size,
                "database_size_mb": db_size / 1024 / 1024,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_storage_summary(self) -> Dict[str, Any]:
        """Get complete storage summary"""
        db_size = Path(self.db_path).stat().st_size
        archive_stats = self.get_archive_stats()

        return {
            "database": {
                "file": str(self.db_path),
                "size_bytes": db_size,
                "size_mb": db_size / 1024 / 1024,
            },
            "archives": archive_stats,
            "total_storage_bytes": db_size + archive_stats.get("total_size_bytes", 0),
            "total_storage_gb": (
                db_size + archive_stats.get("total_size_bytes", 0)
            ) / 1024 / 1024 / 1024,
        }

    def create_archive_index(self) -> Dict[str, Any]:
        """Create an index of all archived data"""
        try:
            index = {}

            for month_dir in sorted(self.archive_root.glob("*/"), reverse=True):
                month_key = month_dir.name
                files = {}

                for gz_file in month_dir.glob("*.gz"):
                    file_size = gz_file.stat().st_size
                    files[gz_file.name] = {
                        "size_bytes": file_size,
                        "size_mb": file_size / 1024 / 1024,
                        "path": str(gz_file),
                    }

                if files:
                    index[month_key] = files

            return {
                "status": "success",
                "archive_index": index,
                "total_months": len(index),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def verify_archives(self) -> Dict[str, Any]:
        """Verify all archives are readable"""
        try:
            verified = 0
            failed = 0
            errors = []

            for gz_file in self.archive_root.glob("**/*.gz"):
                try:
                    with gzip.open(gz_file, "rt") as f:
                        for line in f:
                            json.loads(line)
                            break  # Just verify header is readable
                    verified += 1
                except Exception as e:
                    failed += 1
                    errors.append(f"{gz_file}: {str(e)}")

            return {
                "status": "success" if failed == 0 else "warning",
                "verified_files": verified,
                "failed_files": failed,
                "errors": errors if errors else None,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
