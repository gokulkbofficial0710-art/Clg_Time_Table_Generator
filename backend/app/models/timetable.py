from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class TimetableVersion(Base):
    __tablename__ = "timetable_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_number = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    solver_status = Column(String(50), nullable=False, default="FEASIBLE") # OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN, MODEL_INVALID
    solver_runtime_ms = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0) # 0 to 100
    objective_cost = Column(Float, default=0.0)
    metrics = Column(JSON, default=dict)
    diagnostics = Column(JSON, default=list)
    created_by = Column(String(100), default="Administrator")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    assignments = relationship("TimetableAssignment", back_populates="timetable", cascade="all, delete-orphan")
