import smtplib
from email.message import EmailMessage
from typing import Dict

class EmailDispatcher:
    """
    Dispatcher para envio de emails via SMTP.
    """
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_email(self, to: str, subject: str, body: str) -> Dict:
        msg = EmailMessage()
        msg["From"] = self.username
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        try:
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as smtp:
                smtp.login(self.username, self.password)
                smtp.send_message(msg)
            return {"status": "sent", "to": to}
        except Exception as e:
            return {"status": "error", "error": str(e)}
