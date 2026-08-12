"""
Email Monitor: Learn from Gmail activity
Analyzes your email patterns to understand interests and behavior
"""

import os
import sqlite3
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    from gmail import Gmail
except ImportError:
    Gmail = None


class EmailMonitor:
    """Monitor and learn from email patterns"""

    def __init__(self, db_path: str = "./agent/storage/memory.db"):
        self.db_path = db_path
        self.gmail_user = os.getenv("GMAIL_USER")
        self.gmail_password = os.getenv("GMAIL_PASSWORD")
        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
        self.interval = int(os.getenv("MONITOR_INTERVAL", "300"))
        self.gmail = None
        self._initialize_tables()

    def _initialize_tables(self):
        """Create email tracking tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                sender TEXT,
                subject TEXT,
                keywords TEXT,
                category TEXT,
                priority INTEGER,
                read_status INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT,
                frequency INTEGER,
                time_of_day TEXT,
                average_response_time INTEGER,
                importance_score REAL,
                last_occurrence DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_senders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_email TEXT UNIQUE,
                sender_name TEXT,
                message_count INTEGER,
                avg_response_time INTEGER,
                priority_level INTEGER,
                last_email DATETIME
            )
        """)

        conn.commit()
        conn.close()

    def connect_gmail(self) -> bool:
        """Connect to Gmail (requires app password)"""
        if not self.gmail_user or not self.gmail_app_password:
            print("⚠️  Gmail credentials not configured")
            print("   Set GMAIL_USER and GMAIL_APP_PASSWORD environment variables")
            print("   Learn how: https://support.google.com/accounts/answer/185833")
            return False

        try:
            # Note: Using imap_tools for better email access
            from imap_tools import MailBox
            self.mailbox = MailBox('imap.gmail.com')
            self.mailbox.login(self.gmail_user, self.gmail_app_password)
            print(f"✅ Connected to Gmail: {self.gmail_user}")
            return True
        except ImportError:
            print("📦 Installing imap_tools...")
            os.system("pip install imap_tools")
            return self.connect_gmail()
        except Exception as e:
            print(f"❌ Gmail connection failed: {e}")
            return False

    def extract_keywords(self, subject: str, body: str = "") -> list:
        """Extract keywords from email"""
        keywords = []

        # Simple keyword extraction
        important_words = {
            "urgent": 5,
            "important": 4,
            "meeting": 3,
            "deadline": 4,
            "project": 3,
            "report": 2,
            "update": 2,
            "review": 2,
            "approved": 3,
            "rejected": 3,
        }

        text = (subject + " " + body).lower()
        for word, score in important_words.items():
            if word in text:
                keywords.append({"word": word, "score": score})

        return keywords

    def categorize_email(self, sender: str, subject: str) -> str:
        """Categorize email by type"""
        categories = {
            "work": ["@company", "meeting", "project", "deadline"],
            "personal": ["@gmail", "family", "friend"],
            "notifications": ["notify", "alert", "confirmation"],
            "marketing": ["subscribe", "promo", "sale", "offer"],
            "security": ["verify", "confirm", "password", "security"],
        }

        text = (sender + " " + subject).lower()
        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category

        return "other"

    def log_email_activity(self, sender: str, subject: str, timestamp: datetime, read: bool = False):
        """Log email activity to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        keywords = self.extract_keywords(subject)
        category = self.categorize_email(sender, subject)
        priority = max([k["score"] for k in keywords], default=1) if keywords else 1

        cursor.execute("""
            INSERT INTO email_activity
            (timestamp, sender, subject, keywords, category, priority, read_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp.isoformat(),
            sender,
            subject,
            json.dumps(keywords),
            category,
            priority,
            1 if read else 0
        ))

        # Update sender stats
        cursor.execute("""
            INSERT INTO email_senders (sender_email, sender_name, message_count, last_email)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(sender_email) DO UPDATE SET
                message_count = message_count + 1,
                last_email = ?
        """, (sender, sender.split('@')[0], timestamp.isoformat(), timestamp.isoformat()))

        conn.commit()
        conn.close()

    def analyze_patterns(self) -> dict:
        """Analyze email patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get pattern info
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM email_activity
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY category
            ORDER BY count DESC
        """)

        patterns = {}
        for category, count in cursor.fetchall():
            patterns[category] = count

        # Get top senders
        cursor.execute("""
            SELECT sender_email, message_count
            FROM email_senders
            ORDER BY message_count DESC
            LIMIT 10
        """)

        top_senders = [{"sender": row[0], "count": row[1]} for row in cursor.fetchall()]

        conn.close()

        return {
            "patterns_by_category": patterns,
            "top_senders": top_senders,
            "total_emails_analyzed": sum(patterns.values()),
            "timestamp": datetime.now().isoformat()
        }

    def run(self):
        """Main monitoring loop"""
        print("📧 Email Monitor started")
        print(f"   User: {self.gmail_user}")
        print(f"   Interval: {self.interval}s")

        if not self.connect_gmail():
            print("⚠️  Running in demo mode (no Gmail access)")
            return

        try:
            iteration = 0
            while True:
                iteration += 1
                print(f"\n[{datetime.now().isoformat()}] Checking emails... (iteration {iteration})")

                try:
                    # Get recent emails
                    self.mailbox.login(self.gmail_user, self.gmail_app_password)

                    # Fetch last 50 emails
                    for msg in self.mailbox.fetch(limit=50, mark_seen=False):
                        self.log_email_activity(
                            sender=msg.from_,
                            subject=msg.subject,
                            timestamp=msg.date,
                            read=msg.seen
                        )

                    # Analyze patterns
                    patterns = self.analyze_patterns()
                    print(f"✅ Analyzed {patterns['total_emails_analyzed']} emails")
                    print(f"   Categories: {patterns['patterns_by_category']}")
                    print(f"   Top senders: {[s['sender'] for s in patterns['top_senders'][:3]]}")

                except Exception as e:
                    print(f"❌ Error fetching emails: {e}")

                # Wait before next check
                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\n\n📧 Email Monitor stopped")


if __name__ == "__main__":
    monitor = EmailMonitor()
    monitor.run()
