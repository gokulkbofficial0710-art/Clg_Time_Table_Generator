from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from app.core.database import Base

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    building = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False, default=30)
    is_available = Column(Boolean, default=True, nullable=False)
    features = Column(JSON, default=list) # e.g. ["Computers", "Projector", "Wheelchair Access", "Lab Bench"]
    accessibility_features = Column(JSON, default=list) # e.g. ["Wheelchair Access", "Elevator Nearby"]
    blackout_intervals = Column(JSON, default=list) # e.g. [{"date": "2026-12-15", "start_time": "09:00", "end_time": "12:00", "reason": "Maintenance"}]
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
