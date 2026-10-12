from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False) # e.g. STU-1001
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    semester = Column(String(50), nullable=False)
    special_accommodations = Column(JSON, default=list) # e.g. ["Wheelchair Access", "Extra Time"]
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    enrollments = relationship("StudentEnrollment", back_populates="student", cascade="all, delete-orphan")
