from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class DashboardSummary(BaseModel):
    total_exams: int
    total_students: int
    available_rooms: int
    available_timeslots: int
    scheduled_exams: int
    unscheduled_exams: int
    student_clash_count: int
    room_clash_count: int
    capacity_violation_count: int
    locked_exam_count: int
    quality_score: float
    solver_status: str
    active_version_id: Optional[int] = None
    active_version_name: Optional[str] = None
    last_optimized_at: Optional[str] = None
    is_valid_timetable: bool

class DayDistributionItem(BaseModel):
    date: str
    day_name: str
    exam_count: int
    student_sessions_count: int

class RoomUtilizationItem(BaseModel):
    room_code: str
    room_name: str
    capacity: int
    assigned_sessions: int
    total_seats_allocated: int
    utilization_rate: float # 0.0 to 100.0%

class StudentLoadItem(BaseModel):
    burden_category: str # "1 exam/day", "2 exams/day", "3+ exams/day"
    student_count: int
    percentage: float
