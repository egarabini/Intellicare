from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EmailStatus(str, Enum):
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"

class EmailMessage(BaseModel):
    """Internal representation of an email message."""
    id: Optional[str] = None
    recipient: EmailStr
    subject: str
    template_name: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)  # Paths to files
    status: EmailStatus = EmailStatus.QUEUED
    provider_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = None

class EmailSendRequest(BaseModel):
    """Request model for the API."""
    recipient: EmailStr
    subject: str
    template_name: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    priority: str = "normal"

class EmailSendResponse(BaseModel):
    """Response model for the API."""
    message_id: str
    status: str
    recipient: EmailStr
    provider: str
