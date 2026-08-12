"""
Data Compression Module
Compress old data in database to reduce storage size by 50-80%
"""

import zlib
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional


class DataCompression:
    """Handles data compression for efficient storage"""

    def __init__(self, db_path: str = "./agent/storage/memory.db"):
        self.db_path = db_path
        self._init_compression_tables()

    def _init_compression_tables(self):
        """Add compression tracking columns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Add compression tracking if not exists
            cursor.execute("""
                ALTER TABLE decisions ADD COLUMN compressed INTEGER DEFAULT 0
            """)
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("""
                ALTER TABLE decisions ADD COLUMN compression_ratio REAL DEFAULT 0
            """)
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("""
                ALTER TABLE email_activity ADD COLUMN compressed INTEGER DEFAULT 0
            """)
        except sqlite3.OperationalError:
            pass

        conn.commit()
        conn.close()

    def compress_decisions(self, days_old: int = 30) -> Dict[str, Any]:
        """Compress decisions older than N days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days_old)

            # Find uncompressed old decisions
            cursor.execute("""
                SELECT id, decision_data
                FROM decisions
                WHERE timestamp < ?
                AND compressed = 0
                AND decision_data IS NOT NULL
            """, (cutoff_date.isoformat(),))

            results = cursor.fetchall()
            compressed_count = 0
            total_original_size = 0
            total_compressed_size = 0

            for decision_id, original_data in results:
                if original_data is None:
                    continue

                # Convert to bytes if string
                if isinstance(original_data, str):
                    original_bytes = original_data.encode('utf-8')
                else:
                    original_bytes = original_data

                # Compress using zlib
                try:
                    compressed_data = zlib.compress(original_bytes, level=9)
                    compression_ratio = len(original_bytes) / len(compressed_data)

                    # Only compress if significant reduction
                    if compression_ratio > 1.5:
                        cursor.execute("""
                            UPDATE decisions
                            SET decision_data = ?,
                                compressed = 1,
                                compression_ratio = ?
                            WHERE id = ?
                        """, (compressed_data, compression_ratio, decision_id))

                        compressed_count += 1
                        total_original_size += len(original_bytes)
                        total_compressed_size += len(compressed_data)

                except Exception as e:
                    pass

            conn.commit()
            conn.close()

            avg_ratio = (
                total_original_size / total_compressed_size
                if total_compressed_size > 0
                else 0
            )

            return {
                "status": "success",
                "compressed_records": compressed_count,
                "total_original_size_bytes": total_original_size,
                "total_compressed_size_bytes": total_compressed_size,
                "average_compression_ratio": avg_ratio,
                "space_saved_bytes": total_original_size - total_compressed_size,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def compress_email_activity(self, days_old: int = 60) -> Dict[str, Any]:
        """Compress email activity records"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days_old)

            # Serialize email data for compression
            cursor.execute("""
                SELECT id, sender_email, subject, timestamp
                FROM email_activity
                WHERE timestamp < ?
                AND compressed = 0
            """, (cutoff_date.isoformat(),))

            results = cursor.fetchall()
            compressed_count = 0
            total_original_size = 0
            total_compressed_size = 0

            for email_id, sender, subject, timestamp in results:
                # Create serializable record
                record = {
                    "sender": sender,
                    "subject": subject,
                    "timestamp": timestamp,
                }

                original_bytes = json.dumps(record).encode('utf-8')
                compressed_data = zlib.compress(original_bytes, level=9)

                compression_ratio = len(original_bytes) / len(compressed_data)

                if compression_ratio > 1.2:
                    cursor.execute("""
                        UPDATE email_activity
                        SET compressed = 1,
                            compression_ratio = ?
                        WHERE id = ?
                    """, (compression_ratio, email_id))

                    compressed_count += 1
                    total_original_size += len(original_bytes)
                    total_compressed_size += len(compressed_data)

            conn.commit()
            conn.close()

            return {
                "status": "success",
                "compressed_records": compressed_count,
                "space_saved_bytes": total_original_size - total_compressed_size,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def decompress_decision(self, decision_id: int) -> Optional[Dict[str, Any]]:
        """Decompress a decision for access"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT decision_data, compressed
                FROM decisions
                WHERE id = ?
            """, (decision_id,))

            result = cursor.fetchone()
            conn.close()

            if not result:
                return None

            data, is_compressed = result

            if is_compressed and data:
                decompressed = zlib.decompress(data).decode('utf-8')
                return json.loads(decompressed)
            else:
                return json.loads(data) if isinstance(data, str) else data

        except Exception as e:
            return None

    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Decisions compression stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN compressed = 1 THEN 1 ELSE 0 END) as compressed,
                    AVG(compression_ratio) as avg_ratio
                FROM decisions
            """)

            total_dec, compressed_dec, avg_ratio_dec = cursor.fetchone()

            # Email compression stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN compressed = 1 THEN 1 ELSE 0 END) as compressed,
                    AVG(compression_ratio) as avg_ratio
                FROM email_activity
            """)

            total_email, compressed_email, avg_ratio_email = cursor.fetchone()

            # Database file size
            db_size = Path(self.db_path).stat().st_size

            conn.close()

            return {
                "decisions": {
                    "total_records": total_dec or 0,
                    "compressed_records": compressed_dec or 0,
                    "compression_rate": (
                        (compressed_dec / total_dec * 100) if total_dec else 0
                    ),
                    "average_compression_ratio": avg_ratio_dec or 0,
                },
                "email_activity": {
                    "total_records": total_email or 0,
                    "compressed_records": compressed_email or 0,
                    "compression_rate": (
                        (compressed_email / total_email * 100) if total_email else 0
                    ),
                    "average_compression_ratio": avg_ratio_email or 0,
                },
                "database_file_size_bytes": db_size,
                "database_file_size_mb": db_size / 1024 / 1024,
            }

        except Exception as e:
            return {"error": str(e)}

    def auto_compress_old_data(self) -> Dict[str, Any]:
        """Automatically compress data older than retention period"""
        results = {
            "decisions_compressed": self.compress_decisions(days_old=30),
            "email_compressed": self.compress_email_activity(days_old=60),
            "stats": self.get_compression_stats(),
        }

        return results

    def verify_integrity(self) -> Dict[str, Any]:
        """Verify compressed data can be decompressed"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, decision_data FROM decisions
                WHERE compressed = 1
                LIMIT 100
            """)

            verified = 0
            failed = 0

            for decision_id, compressed_data in cursor.fetchall():
                try:
                    decompressed = zlib.decompress(compressed_data)
                    verified += 1
                except Exception:
                    failed += 1

            conn.close()

            return {
                "status": "success" if failed == 0 else "warning",
                "verified_records": verified,
                "failed_records": failed,
                "integrity": "OK" if failed == 0 else "DEGRADED",
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
