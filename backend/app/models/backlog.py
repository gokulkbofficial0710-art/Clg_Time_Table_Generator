from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base

class BacklogRecord(Base):
    __tablename__ = "backlog_records"

    id = Column(Integer, primary_key=True, index=True)
    student_code = Column(String(50), index=True, nullable=False) # e.g. STU-2026-1002
    student_name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    student_type = Column(String(50), nullable=False, default="Old Student") # "Old Student" vs "New Student"
    current_semester = Column(String(50), nullable=False) # e.g. "Semester 3"
    backlog_semester = Column(String(50), nullable=False) # e.g. "Semester 1"
    semester_type = Column(String(50), nullable=False, default="Odd Semester") # "Odd Semester" vs "Even Semester"
    course_code = Column(String(50), nullable=False) # e.g. "MA101"
    course_name = Column(String(150), nullable=False) # e.g. "Calculus I & Analytical Geometry"
    exam_date = Column(String(50), nullable=False) # e.g. "2026-12-19"
    exam_day = Column(String(50), nullable=False) # "Saturday" vs "Sunday"
    start_time = Column(String(50), nullable=False, default="09:30:00")
    end_time = Column(String(50), nullable=False, default="12:30:00")
    period = Column(String(50), nullable=False, default="Morning") # "Morning" vs "Afternoon"
    room_code = Column(String(50), nullable=False) # e.g. "AUD-MAIN"
    room_name = Column(String(150), nullable=False) # e.g. "Grand University Auditorium"
    seat_number = Column(String(50), nullable=False) # e.g. "AUD-MAIN-BK01"
    status = Column(String(50), nullable=False, default="SCHEDULED") # "SCHEDULED", "COMPLETED", "PENDING"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
