import uuid
from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from conhecimento.storage.db import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String, index=True)
    content = Column(Text)
    metadata_ = Column("metadata", JSONB, default=dict)
    embedding = Column(Vector(384)) # 384 dimension supports all-MiniLM-L6-v2 and intfloat/multilingual-e5-small
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
