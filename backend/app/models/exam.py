from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class CourseExam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    exam_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. EXAM-CS101
    course_code = Column(String(50), index=True, nullable=False) # e.g. CS101
    course_name = Column(String(150), nullable=False) # e.g. Algorithms & Data Structures
    department = Column(String(100), nullable=False)
    semester = Column(String(50), nullable=False)
    academic_year = Column(String(50), nullable=False, default="2026-2027")
    duration_minutes = Column(Integer, nullable=False, default=120)
    exam_type = Column(String(50), default="Written") # Written, Practical, Lab, Oral
    required_features = Column(JSON, default=list) # e.g. ["Computers", "Wheelchair Access"]
    eligible_slot_ids = Column(JSON, default=list) # Empty means all slots are eligible
    preferred_slot_ids = Column(JSON, default=list) # Soft preference slots
    priority = Column(Integer, default=5) # 1 (lowest) to 10 (highest)
    is_locked = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    enrollments = relationship("StudentEnrollment", back_populates="exam", cascade="all, delete-orphan")
    assignments = relationship("TimetableAssignment", back_populates="exam", cascade="all, delete-orphan")

    @property
    def enrollment_count(self) -> int:
        return len(self.enrollments) if self.enrollments else 0
