from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, func

from admin.db import Base

class ModuleTestLog(Base):
    __tablename__ = "module_test_log"

    id             = Column(Integer, primary_key=True)
    module_name    = Column(String(64), nullable=False, index=True)
    test_type      = Column(String(32), nullable=False)  # "probe"|"functional"|"integration"
    payload_key    = Column(String(64))
    status_code    = Column(Integer)
    latency_ms     = Column(Integer)
    success        = Column(Boolean)
    response_json  = Column(JSON)
    error_message  = Column(String(512))
    triggered_by   = Column(String(128))  # user sub do JWT
    created_at     = Column(DateTime(timezone=True), server_default=func.now(), index=True)
