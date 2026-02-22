import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
import logging

from .base import BaseEmailProvider
from ..models import EmailMessage, EmailStatus
from ..config import SMTPConfig

logger = logging.getLogger("comunicacao.channels.email.providers.smtp")

class SMTPEmailProvider(BaseEmailProvider):
    """SMTP implementation of Email provider."""
    
    def __init__(self, config: SMTPConfig):
        self.config = config
    
    def _get_connection(self):
        """Creates and returns an SMTP connection."""
        if self.config.use_tls:
            server = smtplib.SMTP(self.config.host, self.config.port)
            server.starttls()
        else:
            server = smtplib.SMTP(self.config.host, self.config.port)
            
        if self.config.username and self.config.password:
            server.login(self.config.username, self.config.password)
            
        return server

    def send(self, message: EmailMessage) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = f"{self.config.sender_name} <{self.config.sender_email}>"
            msg["To"] = message.recipient
            
            # Attach parts
            if message.body_text:
                part1 = MIMEText(message.body_text, "plain")
                msg.attach(part1)
                
            if message.body_html:
                part2 = MIMEText(message.body_html, "html")
                msg.attach(part2)
            
            # TODO: Handle attachments
            
            with self._get_connection() as server:
                server.sendmail(
                    self.config.sender_email, 
                    message.recipient, 
                    msg.as_string()
                )
            
            message.status = EmailStatus.SENT
            message.provider_id = "smtp"
            logger.info(f"Email sent successfully via SMTP to {message.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {str(e)}")
            message.status = EmailStatus.FAILED
            message.error_message = str(e)
            return False

    def health_check(self) -> Dict[str, Any]:
        try:
            # Just try to connect and quit
            with self._get_connection() as server:
                server.noop()
            return {"status": "healthy", "provider": "smtp"}
        except Exception as e:
            return {"status": "unhealthy", "provider": "smtp", "error": str(e)}
