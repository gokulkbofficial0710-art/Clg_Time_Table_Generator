from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False, index=True) # GENERATE, REOPTIMIZE, MANUAL_EDIT, LOCK_EXAM, UNLOCK_EXAM, IMPORT, RESTORE
    entity_type = Column(String(50), nullable=False) # TIMETABLE, EXAM, ASSIGNMENT, ROOM, STUDENT
    entity_id = Column(String(100), nullable=True)
    user = Column(String(100), default="Administrator", nullable=False)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
