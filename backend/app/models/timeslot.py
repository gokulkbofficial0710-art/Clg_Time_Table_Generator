from datetime import datetime, date, time, timezone
from sqlalchemy import Column, Integer, String, Boolean, Date, Time, DateTime
from app.core.database import Base

class TimeSlot(Base):
    __tablename__ = "timeslots"

    id = Column(Integer, primary_key=True, index=True)
    slot_code = Column(String(50), unique=True, index=True, nullable=False)
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, nullable=False) # e.g. 120 or 180
    period = Column(String(50), default="Morning") # Morning, Afternoon, Evening
    is_available = Column(Boolean, default=True, nullable=False)
    is_blackout = Column(Boolean, default=False, nullable=False) # Institutional blackout
    blackout_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
