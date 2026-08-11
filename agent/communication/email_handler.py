"""
Email Handler: Communication with human
Sends reports, receives commands
"""

import smtplib
import imaplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import time


class EmailHandler:
    """Handle email communication"""

    GMAIL_SMTP = "smtp.gmail.com"
    GMAIL_IMAP = "imap.gmail.com"
    SMTP_PORT = 587
    IMAP_PORT = 993

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.connected = False

    async def send_report(
        self,
        subject: str,
        body: str
    ) -> bool:
        """Send a report email"""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email
            msg["To"] = self.email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            # Connect and send
            server = smtplib.SMTP(self.GMAIL_SMTP, self.SMTP_PORT)
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)
            server.quit()

            print(f"✅ Email sent: {subject}")
            return True

        except Exception as e:
            print(f"⚠️  Failed to send email: {e}")
            return False

    async def send_alert(
        self,
        subject: str,
        message: str
    ) -> bool:
        """Send an alert email"""
        return await self.send_report(subject, message)

    async def get_commands(self) -> list:
        """Check email for commands from user"""
        try:
            # Connect to IMAP
            imap = imaplib.IMAP4_SSL(self.GMAIL_IMAP, self.IMAP_PORT)
            imap.login(self.email, self.password)

            # Select inbox
            imap.select("INBOX")

            # Search for unread emails
            status, messages = imap.search(None, "UNSEEN")

            commands = []

            if messages and messages[0]:
                for msg_id in messages[0].split():
                    # Get the email
                    status, msg_data = imap.fetch(msg_id, "(RFC822)")

                    # Parse email
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = response_part[1]
                            # Extract text (simplified)
                            if isinstance(msg, bytes):
                                text = msg.decode("utf-8", errors="ignore")
                                # Extract commands (lines starting with >)
                                for line in text.split("\n"):
                                    line = line.strip()
                                    if line.startswith(">"):
                                        commands.append(line[1:].strip())

            imap.close()
            imap.logout()

            return commands

        except Exception as e:
            print(f"⚠️  Failed to check email: {e}")
            return []
