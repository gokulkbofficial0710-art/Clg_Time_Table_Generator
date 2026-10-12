from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class ExamBase(BaseModel):
    exam_code: str = Field(..., description="Unique exam code, e.g. EXAM-CS101")
    course_code: str = Field(..., description="Course code, e.g. CS101")
    course_name: str = Field(..., description="Course name, e.g. Data Structures")
    department: str = Field(..., description="Academic department")
    semester: str = Field(..., description="Semester")
    academic_year: str = Field("2026-2027", description="Academic year")
    duration_minutes: int = Field(120, ge=15, description="Exam duration in minutes")
    exam_type: str = Field("Written", description="Written, Practical, Lab, etc.")
    required_features: List[str] = Field(default_factory=list, description="Features like Computers, Wheelchair Access")
    eligible_slot_ids: List[int] = Field(default_factory=list)
    preferred_slot_ids: List[int] = Field(default_factory=list)
    priority: int = Field(5, ge=1, le=10)
    is_locked: bool = False
    notes: Optional[str] = None

class ExamCreate(ExamBase):
    enrolled_student_ids: Optional[List[int]] = Field(default_factory=list)

class ExamUpdate(BaseModel):
    exam_code: Optional[str] = None
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[str] = None
    academic_year: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=15)
    exam_type: Optional[str] = None
    required_features: Optional[List[str]] = None
    eligible_slot_ids: Optional[List[int]] = None
    preferred_slot_ids: Optional[List[int]] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    is_locked: Optional[bool] = None
    notes: Optional[str] = None
    enrolled_student_ids: Optional[List[int]] = None

class ExamResponse(ExamBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    enrollment_count: int = 0
    enrolled_student_ids: List[int] = Field(default_factory=list)
