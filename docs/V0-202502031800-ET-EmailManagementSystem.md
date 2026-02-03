# 🔧 Especificação Técnica - Sistema de Gerenciamento de Emails

**Projeto:** IntelliCare Email Management System  
**Versão:** 1.0  
**Data:** 2025-02-03

---

## 1. STACK TECNOLÓGICA

### 1.1 Dependências Python

```txt
# requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
celery[redis]==5.4.0
redis==5.2.0
jinja2==3.1.4
python-email-validator==2.2.0
pydantic==2.10.0
pydantic-settings==2.6.0
sqlalchemy==2.0.36
alembic==1.14.0
psycopg2-binary==2.9.10
python-multipart==0.0.18
aiosmtplib==3.0.2
httpx==0.28.1
flower==2.0.1
python-dotenv==1.0.1
```

### 1.2 Infraestrutura

- **Python:** 3.11+
- **Redis:** 7.0+ (broker + cache)
- **PostgreSQL:** 15+ (logs e auditoria)
- **Docker:** Para containerização

---

## 2. ESTRUTURA DE DIRETÓRIOS

```
INTELLICAREREPO/
├── email_service/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── celery_app.py           # Configuração Celery
│   ├── config.py               # Settings (Pydantic)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── email_log.py        # SQLAlchemy models
│   │   └── schemas.py          # Pydantic schemas
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── email_tasks.py      # Celery tasks
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract provider
│   │   ├── smtp_provider.py
│   │   ├── mailgun_provider.py
│   │   └── sendgrid_provider.py
│   ├── templates/
│   │   ├── base.html           # Template base
│   │   ├── verification.html
│   │   ├── status_update.html
│   │   ├── welcome.html
│   │   └── password_reset.html
│   ├── routers/
│   │   ├── __init__.py
│   │   └── emails.py           # API endpoints
│   ├── database.py             # SQLAlchemy setup
│   └── utils.py                # Helpers
├── alembic/                    # Migrations
├── tests/
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── requirements.txt
```

---

## 3. CONFIGURAÇÃO (config.py)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    """Configurações do sistema de email"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # FastAPI
    app_name: str = "IntelliCare Email Service"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql://user:pass@localhost:5432/intellicare_emails"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_track_started: bool = True
    celery_task_time_limit: int = 30  # segundos
    
    # Email Provider
    email_provider: Literal["smtp", "mailgun", "sendgrid"] = "smtp"
    email_fallback_provider: Literal["smtp", "mailgun", "sendgrid", "none"] = "none"
    
    # SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_from_email: str = "noreply@intellicare.com.br"
    smtp_from_name: str = "IntelliCare"
    
    # Mailgun
    mailgun_api_key: str = ""
    mailgun_domain: str = ""
    mailgun_from_email: str = "noreply@intellicare.com.br"
    
    # SendGrid
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "noreply@intellicare.com.br"
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    
    # Retry Policy
    max_retries: int = 3
    retry_backoff: int = 60  # segundos
    
    # Templates
    templates_dir: str = "email_service/templates"
    
    # Logs
    log_retention_days: int = 90

settings = Settings()
```

---

## 4. MODELOS DE DADOS (models/email_log.py)

```python
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class EmailStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"

class EmailPriority(str, enum.Enum):
    URGENT = "urgent"
    NORMAL = "normal"
    LOW = "low"

class EmailLog(Base):
    __tablename__ = "email_logs"
    
    id = Column(String(36), primary_key=True)  # UUID
    task_id = Column(String(255), index=True, nullable=True)
    
    # Destinatário
    to_email = Column(String(255), nullable=False, index=True)
    to_name = Column(String(255), nullable=True)
    
    # Conteúdo
    subject = Column(String(500), nullable=False)
    template_name = Column(String(100), nullable=True)
    template_vars = Column(JSON, nullable=True)
    html_body = Column(Text, nullable=True)
    text_body = Column(Text, nullable=True)
    
    # Metadados
    priority = Column(Enum(EmailPriority), default=EmailPriority.NORMAL)
    status = Column(Enum(EmailStatus), default=EmailStatus.PENDING, index=True)
    provider = Column(String(50), nullable=True)
    
    # Tentativas
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    last_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    
    # Anexos (JSON array de URLs)
    attachments = Column(JSON, nullable=True)
    
    # Contexto adicional
    metadata = Column(JSON, nullable=True)
```

---

## 5. SCHEMAS PYDANTIC (models/schemas.py)

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class EmailPriority(str, Enum):
    URGENT = "urgent"
    NORMAL = "normal"
    LOW = "low"

class SendEmailRequest(BaseModel):
    to_email: EmailStr
    to_name: Optional[str] = None
    subject: str = Field(..., min_length=1, max_length=500)
    template_name: Optional[str] = None
    template_vars: Optional[Dict[str, Any]] = None
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    priority: EmailPriority = EmailPriority.NORMAL
    attachments: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "to_email": "usuario@example.com",
                "to_name": "João Silva",
                "subject": "Verificação de Email",
                "template_name": "verification",
                "template_vars": {
                    "token": "12345",
                    "protocol": "INTC-2025-001"
                },
                "priority": "urgent"
            }
        }

class SendEmailResponse(BaseModel):
    success: bool
    task_id: str
    email_id: str
    message: str

class EmailStatusResponse(BaseModel):
    email_id: str
    status: str
    to_email: str
    subject: str
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    attempts: int
    last_error: Optional[str]
```

---

## 6. CELERY CONFIGURATION (celery_app.py)

```python
from celery import Celery
from .config import settings

# Criar app Celery
celery_app = Celery(
    "intellicare_emails",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Configuração
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_time_limit - 5,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Filas por prioridade
    task_routes={
        "email_service.tasks.email_tasks.send_email_task": {
            "queue": "emails",
        },
    },

    # Retry policy
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": settings.max_retries},
    task_retry_backoff=settings.retry_backoff,
    task_retry_backoff_max=600,  # 10 minutos
    task_retry_jitter=True,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["email_service.tasks"])
```

---

## 7. PROVIDER BASE (providers/base.py)

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class EmailProvider(ABC):
    """Interface abstrata para provedores de email"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Envia um email

        Returns:
            Dict com:
                - success: bool
                - message_id: str (ID do provedor)
                - error: Optional[str]
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Retorna nome do provedor"""
        pass
```

---

## 8. SMTP PROVIDER (providers/smtp_provider.py)

```python
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
import logging

from .base import EmailProvider

logger = logging.getLogger(__name__)

class SMTPProvider(EmailProvider):
    """Provedor SMTP (Gmail, Outlook, etc.)"""

    def get_name(self) -> str:
        return "SMTP"

    async def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        try:
            # Criar mensagem
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{from_name or self.config['from_name']} <{from_email or self.config['from_email']}>"
            message["To"] = to_email

            # Adicionar corpo texto plano
            if text_body:
                part1 = MIMEText(text_body, "plain", "utf-8")
                message.attach(part1)

            # Adicionar corpo HTML
            part2 = MIMEText(html_body, "html", "utf-8")
            message.attach(part2)

            # TODO: Adicionar anexos (se necessário)

            # Enviar via SMTP
            await aiosmtplib.send(
                message,
                hostname=self.config["host"],
                port=self.config["port"],
                username=self.config["username"],
                password=self.config["password"],
                use_tls=self.config["use_tls"],
                timeout=30,
            )

            logger.info(f"Email enviado via SMTP para {to_email}")

            return {
                "success": True,
                "message_id": message["Message-ID"],
                "error": None,
            }

        except Exception as e:
            logger.error(f"Erro ao enviar email via SMTP: {str(e)}")
            return {
                "success": False,
                "message_id": None,
                "error": str(e),
            }
```

---

## 9. MAILGUN PROVIDER (providers/mailgun_provider.py)

```python
import httpx
from typing import Optional, List, Dict, Any
import logging

from .base import EmailProvider

logger = logging.getLogger(__name__)

class MailgunProvider(EmailProvider):
    """Provedor Mailgun (API)"""

    def get_name(self) -> str:
        return "Mailgun"

    async def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        try:
            url = f"https://api.mailgun.net/v3/{self.config['domain']}/messages"

            data = {
                "from": f"{from_name or 'IntelliCare'} <{from_email or self.config['from_email']}>",
                "to": to_email,
                "subject": subject,
                "html": html_body,
            }

            if text_body:
                data["text"] = text_body

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    auth=("api", self.config["api_key"]),
                    data=data,
                    timeout=30,
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Email enviado via Mailgun para {to_email}")
                    return {
                        "success": True,
                        "message_id": result.get("id"),
                        "error": None,
                    }
                else:
                    error_msg = f"Mailgun error {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "message_id": None,
                        "error": error_msg,
                    }

        except Exception as e:
            logger.error(f"Erro ao enviar email via Mailgun: {str(e)}")
            return {
                "success": False,
                "message_id": None,
                "error": str(e),
            }
```

---

**Continua...**

