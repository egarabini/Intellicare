from pydantic import BaseModel
from typing import Optional
import os

class SMTPConfig(BaseModel):
    """Configuration for SMTP server."""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    sender_email: str
    sender_name: str = "IntelliCare Alert System"

class EmailConfig(BaseModel):
    """Configuration for the Email channel."""
    smtp: SMTPConfig
    templates_dir: str = "templates/email"
    
    @classmethod
    def from_env(cls) -> "EmailConfig":
        return cls(
            smtp=SMTPConfig(
                host=os.getenv("SMTP_HOST", "localhost"),
                port=int(os.getenv("SMTP_PORT", "1025")),  # Default to Mailhog port
                username=os.getenv("SMTP_USER"),
                password=os.getenv("SMTP_PASS"),
                use_tls=os.getenv("SMTP_TLS", "true").lower() == "true",
                sender_email=os.getenv("SMTP_SENDER_EMAIL", "alerts@intellicare.ai"),
                sender_name=os.getenv("SMTP_SENDER_NAME", "IntelliCare Alert System")
            )
        )
