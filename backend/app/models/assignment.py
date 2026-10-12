from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class TimetableAssignment(Base):
    __tablename__ = "timetable_assignments"

    id = Column(Integer, primary_key=True, index=True)
    timetable_id = Column(Integer, ForeignKey("timetable_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    timeslot_id = Column(Integer, ForeignKey("timeslots.id", ondelete="SET NULL"), nullable=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True, index=True)
    
    assigned_student_count = Column(Integer, default=0, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    source = Column(String(50), default="AUTOMATIC") # AUTOMATIC or MANUAL
    validation_status = Column(String(50), default="VALID") # VALID, CONFLICT, UNSCHEDULED
    conflict_reasons = Column(JSON, default=list) # e.g. ["Room capacity exceeded", "Student clash with CS201"]
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    timetable = relationship("TimetableVersion", back_populates="assignments")
    exam = relationship("CourseExam", back_populates="assignments")
    timeslot = relationship("TimeSlot")
    room = relationship("Room")
