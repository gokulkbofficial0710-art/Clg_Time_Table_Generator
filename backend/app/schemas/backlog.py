from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class BacklogCreateRequest(BaseModel):
    student_code: str = Field(..., description="Student registration ID, e.g. STU-2026-1002")
    student_name: str = Field(..., description="Student full name")
    department: str = Field(..., description="Academic department")
    student_type: str = Field("Old Student", description="'Old Student' or 'New Student'")
    current_semester: str = Field(..., description="Current studying semester, e.g. 'Semester 3'")
    backlog_semester: str = Field(..., description="Backlog semester, e.g. 'Semester 1'")
    semester_type: Optional[str] = Field(None, description="'Odd Semester' or 'Even Semester'")
    course_code: str = Field(..., description="Course code of backlog subject, e.g. 'MA101'")
    course_name: str = Field(..., description="Course name of backlog subject, e.g. 'Calculus I & Analytical Geometry'")
    exam_date: Optional[str] = Field(None, description="Weekend exam date, e.g. '2026-12-19'")
    exam_day: Optional[str] = Field(None, description="'Saturday' or 'Sunday'")
    start_time: Optional[str] = Field("09:30:00", description="Start time, e.g. '09:30:00'")
    end_time: Optional[str] = Field("12:30:00", description="End time, e.g. '12:30:00'")
    period: Optional[str] = Field("Morning", description="'Morning' or 'Afternoon'")
    room_code: Optional[str] = Field(None, description="Hall/Room code, e.g. 'AUD-MAIN'")
    room_name: Optional[str] = Field(None, description="Hall name")
    seat_number: Optional[str] = Field(None, description="Desk number, e.g. 'AUD-MAIN-BK01'")

class BacklogResponse(BaseModel):
    id: int
    student_code: str
    student_name: str
    department: str
    student_type: str
    current_semester: str
    backlog_semester: str
    semester_type: str
    course_code: str
    course_name: str
    exam_date: str
    exam_day: str
    start_time: str
    end_time: str
    period: str
    room_code: str
    room_name: str
    seat_number: str
    status: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class BacklogSummaryResponse(BaseModel):
    total_backlogs: int
    old_students_count: int
    new_students_count: int
    odd_sem_backlogs_count: int
    even_sem_backlogs_count: int
    weekend_sessions_count: int
    venues_allocated_count: int
    department_counts: dict = Field(default_factory=dict)
    active_department: Optional[str] = None
    is_pre_optimization: bool = False

