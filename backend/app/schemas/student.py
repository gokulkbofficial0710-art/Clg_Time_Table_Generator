from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class StudentBase(BaseModel):
    student_id: str = Field(..., description="Unique student ID, e.g. STU-1001")
    name: str = Field(..., description="Full student name")
    department: str = Field(..., description="Academic department")
    semester: str = Field(..., description="Academic semester")
    special_accommodations: List[str] = Field(default_factory=list)

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    student_id: Optional[str] = None
    name: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[str] = None
    special_accommodations: Optional[List[str]] = None

class EnrollmentInfo(BaseModel):
    exam_id: int
    exam_code: str
    course_code: str
    course_name: str

class StudentResponse(StudentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    enrolled_exam_ids: List[int] = Field(default_factory=list)

class StudentTimetableItem(BaseModel):
    exam_code: str
    course_code: str
    course_name: str
    date: str
    start_time: str
    end_time: str
    room_code: str
    room_name: str
    building: str
    is_locked: bool

class StudentExamSeating(BaseModel):
    exam_id: int
    exam_code: str
    course_code: str
    course_name: str
    date: str
    day_name: Optional[str] = None
    start_time: str
    end_time: str
    period: Optional[str] = None
    room_code: str
    room_name: str
    building: str
    room_capacity: Optional[int] = None
    seat_number: str
    bench_number: Optional[int] = None
    is_locked: bool = False

class StudentSeatingResponse(StudentBase):
    id: int
    subjects_count: int
    distinct_halls_count: int
    exams: List[StudentExamSeating] = Field(default_factory=list)

class DepartmentSeatingSummary(BaseModel):
    department: str
    students_count: int
    total_sittings: int
    distinct_exams_count: int

class BenchAllocation(BaseModel):
    bench_number: int
    seat_number: str
    student_id: str
    student_name: str
    department: str
    semester: str
    course_code: str
    course_name: str
    exam_code: str
    special_accommodations: List[str] = Field(default_factory=list)

class HallSeatingChart(BaseModel):
    session_key: str
    timeslot_id: int
    slot_code: str
    date: str
    day_name: str
    start_time: str
    end_time: str
    period: Optional[str] = None
    room_id: int
    room_code: str
    room_name: str
    building: str
    room_capacity: int
    total_assigned: int
    participating_departments: List[str]
    is_alternating: bool
    benches: List[BenchAllocation]

class ParsedStudentItem(BaseModel):
    row_number: int = 1
    student_id: str
    name: str
    department: str
    semester: str = "Semester 5"
    enrolled_courses: List[str] = Field(default_factory=list)
    special_accommodations: List[str] = Field(default_factory=list)
    status: str = "VALID"
    errors: List[str] = Field(default_factory=list)

class StudentTextPreviewResponse(BaseModel):
    total_found: int
    valid_count: int
    invalid_count: int
    departments_detected: dict[str, int]
    students: List[ParsedStudentItem]
    sample_text: Optional[str] = None

class StudentTextCommitRequest(BaseModel):
    students: List[ParsedStudentItem]
    overwrite_existing: bool = True
    auto_enroll_courses: bool = True

class StudentTextCommitResponse(BaseModel):
    status: str
    message: str
    total_processed: int
    created_count: int
    updated_count: int
    enrollments_added: int
    departments: dict[str, int]

