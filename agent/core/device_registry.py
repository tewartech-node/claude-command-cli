"""
Device Registry: Network of autonomous Brains
Manages multi-device coordination, discovery, and memory sharing
Supports: Termux (ARM32/ARM64), Windows (XP-11), Linux, macOS
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path


class DeviceRegistry:
    """Central registry for networked Brains"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def initialize(self):
        """Create device registry tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Devices table - tracks all Brains in network
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE,
                device_name TEXT,
                platform TEXT,
                arch TEXT,
                status TEXT,
                last_seen DATETIME,
                memory_path TEXT,
                sync_key TEXT,
                capabilities TEXT
            )
        """)

        # Network connections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_device TEXT,
                target_device TEXT,
                connection_type TEXT,
                last_sync DATETIME,
                sync_count INTEGER,
                status TEXT,
                FOREIGN KEY(source_device) REFERENCES devices(device_id),
                FOREIGN KEY(target_device) REFERENCES devices(device_id)
            )
        """)

        # Shared decisions table - track which device made decision
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER,
                source_device TEXT,
                timestamp DATETIME,
                shared_to TEXT,
                FOREIGN KEY(source_device) REFERENCES devices(device_id)
            )
        """)

        # Network stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                total_devices INTEGER,
                connected_devices INTEGER,
                total_synced_decisions INTEGER,
                total_network_confidence REAL
            )
        """)

        conn.commit()
        conn.close()
        print("✅ Device registry initialized")

    def register_device(self, device_id: str, device_name: str, platform: str,
                       arch: str, memory_path: str) -> bool:
        """Register a Brain device in the network"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO devices
                (device_id, device_name, platform, arch, status, last_seen, memory_path, capabilities)
                VALUES (?, ?, ?, ?, 'online', ?, ?, ?)
            """, (
                device_id, device_name, platform, arch,
                datetime.now().isoformat(), memory_path,
                json.dumps(["decisions", "ratings", "patterns"])
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error registering device: {e}")
            conn.close()
            return False

    def get_network_status(self) -> dict:
        """Get current network status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all devices
        cursor.execute("SELECT COUNT(*) FROM devices")
        total_devices = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'online'")
        online_devices = cursor.fetchone()[0]

        # Get devices list
        cursor.execute("""
            SELECT device_id, device_name, platform, arch, status, last_seen
            FROM devices
            ORDER BY last_seen DESC
        """)

        devices = []
        for row in cursor.fetchall():
            devices.append({
                "id": row[0],
                "name": row[1],
                "platform": row[2],
                "arch": row[3],
                "status": row[4],
                "last_seen": row[5]
            })

        # Get total synced decisions
        cursor.execute("SELECT COUNT(*) FROM shared_decisions")
        synced_decisions = cursor.fetchone()[0]

        conn.close()

        return {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "devices": devices,
            "total_synced_decisions": synced_decisions,
            "timestamp": datetime.now().isoformat()
        }

    def record_sync(self, source_device: str, target_device: str, decision_count: int) -> bool:
        """Record a sync operation between devices"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Update or create connection
            cursor.execute("""
                INSERT OR IGNORE INTO connections
                (source_device, target_device, connection_type, last_sync, sync_count, status)
                VALUES (?, ?, 'automatic', ?, 1, 'success')
            """, (source_device, target_device, datetime.now().isoformat()))

            cursor.execute("""
                UPDATE connections
                SET last_sync = ?, sync_count = sync_count + 1
                WHERE source_device = ? AND target_device = ?
            """, (datetime.now().isoformat(), source_device, target_device))

            # Record shared decisions
            for i in range(decision_count):
                cursor.execute("""
                    INSERT INTO shared_decisions
                    (decision_id, source_device, timestamp, shared_to)
                    VALUES (?, ?, ?, ?)
                """, (i, source_device, datetime.now().isoformat(), target_device))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error recording sync: {e}")
            conn.close()
            return False

    def get_device_by_id(self, device_id: str) -> dict:
        """Get device information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT device_id, device_name, platform, arch, status, memory_path
            FROM devices
            WHERE device_id = ?
        """, (device_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0],
            "name": row[1],
            "platform": row[2],
            "arch": row[3],
            "status": row[4],
            "memory_path": row[5]
        }

    def list_online_devices(self) -> list:
        """Get all online devices"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT device_id, device_name, platform, arch
            FROM devices
            WHERE status = 'online'
            ORDER BY last_seen DESC
        """)

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "name": row[1],
                "platform": row[2],
                "arch": row[3]
            })

        conn.close()
        return results

    def get_network_intelligence(self) -> dict:
        """Aggregate intelligence from entire network"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get average confidence across all devices
        cursor.execute("""
            SELECT AVG(CAST(good_count AS FLOAT) / CAST(total_count AS FLOAT))
            FROM (
                SELECT COUNT(*) as total_count,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as good_count
                FROM decisions
            )
        """)

        network_confidence = cursor.fetchone()[0] or 0.5

        # Get most reliable decision type across network
        cursor.execute("""
            SELECT decision_name, COUNT(*) as frequency,
                   AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0 END) as reliability
            FROM decisions
            GROUP BY decision_name
            ORDER BY reliability DESC
            LIMIT 5
        """)

        reliable_strategies = []
        for row in cursor.fetchall():
            reliable_strategies.append({
                "strategy": row[0],
                "frequency": row[1],
                "reliability": round(row[2], 2)
            })

        conn.close()

        return {
            "network_confidence": round(network_confidence, 2),
            "reliable_strategies": reliable_strategies,
            "timestamp": datetime.now().isoformat()
        }
