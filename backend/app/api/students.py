from typing import List, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.student import Student
from app.models.enrollment import StudentEnrollment
from app.models.exam import CourseExam
from app.models.timetable import TimetableVersion
from app.models.assignment import TimetableAssignment
from app.schemas.student import (
    StudentCreate, StudentUpdate, StudentResponse, StudentTimetableItem,
    StudentExamSeating, StudentSeatingResponse, DepartmentSeatingSummary,
    HallSeatingChart, ParsedStudentItem, StudentTextPreviewResponse,
    StudentTextCommitRequest, StudentTextCommitResponse
)
from app.schemas.common import MessageResponse
from app.services.seating_service import compute_department_alternating_seatings
from app.services.student_text_parser import (
    parse_student_text_file, commit_student_text_records
)

router = APIRouter(prefix="/students", tags=["Students"])

SAMPLE_TEXT_TEMPLATES = {
    "delimited": """# Student Cohort Registry - Comma Delimited (.txt / .csv)
# Columns: student_id, name, department, semester, courses, accommodations
STU-2026-1101, Alex Williams, Computer Science, Semester 5, CS101, Extra Time
STU-2026-1102, Brittany Brown, Business, Semester 5, BUS101, None
STU-2026-1103, Charlie Clark, Mathematics, Semester 5, MA101, None
STU-2026-1104, Daniel Davis, Electrical Eng, Semester 5, CS101, Wheelchair Access
STU-2026-1105, Evelyn Evans, Physics, Semester 5, MA101, None
""",
    "pipe": """# Student Cohort Registry - Pipe Delimited (.txt)
STU-2026-1201 | Fiona Fisher | Computer Science | Semester 5 | CS101,CS201 | Extra Time
STU-2026-1202 | George Garcia | Business | Semester 5 | BUS101 | None
STU-2026-1203 | Hannah Harris | Mathematics | Semester 5 | MA101,MA310 | None
STU-2026-1204 | Ian Isaac | Electrical Eng | Semester 5 | CS499 | None
""",
    "block": """# Student Cohort Registry - Key-Value Block (.txt)
Student ID: STU-2026-1301
Name: Julia Jones
Department: Computer Science
Semester: Semester 5
Courses: CS101, CS201
Accommodations: Extra Time
---
Student ID: STU-2026-1302
Name: Kevin King
Department: Business
Semester: Semester 5
Courses: BUS101, BUS205
Accommodations: None
---
Student ID: STU-2026-1303
Name: Laura Lewis
Department: Mathematics
Semester: Semester 5
Courses: MA101
Accommodations: Wheelchair Access
"""
}

@router.get("/text-template")
def get_student_text_templates(format_type: str = "delimited"):
    template = SAMPLE_TEXT_TEMPLATES.get(format_type.lower(), SAMPLE_TEXT_TEMPLATES["delimited"])
    return Response(
        content=template,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=students_{format_type}_template.txt"}
    )

@router.post("/preview-text", response_model=StudentTextPreviewResponse)
async def preview_student_text(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None)
):
    content = ""
    if file:
        file_bytes = await file.read()
        try:
            content = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = file_bytes.decode("latin-1", errors="replace")
    elif raw_text:
        content = raw_text

    if not content.strip():
        raise HTTPException(status_code=400, detail="Please upload a .txt file or paste student records text.")

    res = parse_student_text_file(content)
    res["sample_text"] = content[:500]
    return res

@router.post("/commit-text", response_model=StudentTextCommitResponse)
def commit_student_text(
    req: StudentTextCommitRequest,
    db: Session = Depends(get_db)
):
    if not req.students:
        raise HTTPException(status_code=400, detail="No student records provided to commit.")

    items_dict = [st.model_dump() for st in req.students]
    res = commit_student_text_records(
        db=db,
        students_data=items_dict,
        overwrite=req.overwrite_existing,
        auto_enroll=req.auto_enroll_courses
    )
    return res

@router.get("", response_model=List[StudentResponse])
def get_all_students(
    department: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Student)
    if department:
        query = query.filter(Student.department == department)
    if search:
        s = f"%{search}%"
        query = query.filter((Student.name.ilike(s)) | (Student.student_id.ilike(s)))
    students = query.order_by(Student.id).all()

    return [
        StudentResponse(
            id=s.id,
            student_id=s.student_id,
            name=s.name,
            department=s.department,
            semester=s.semester,
            special_accommodations=s.special_accommodations or [],
            enrolled_exam_ids=[en.exam_id for en in s.enrollments]
        )
        for s in students
    ]

@router.get("/seatings", response_model=List[StudentSeatingResponse])
def get_student_seatings(
    department: Optional[str] = None,
    search: Optional[str] = None,
    version_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Returns full student examination seating allocations:
    Each student's 5 (or N) subjects, allocated halls/rooms, exam dates, and timings.
    """
    if version_id:
        ver = db.query(TimetableVersion).filter_by(id=version_id).first()
    else:
        ver = db.query(TimetableVersion).filter_by(is_active=True).first()

    if not ver:
        return []

    # If the timetable is in pre-optimization baseline state, seating allocations are cleared & empty
    is_pre_opt = (
        ver.solver_status in ("PRE_OPTIMIZATION", "DRAFT", "PENDING")
        or (ver.quality_score == 0.0)
        or "pre-optimization" in (ver.name or "").lower()
        or (ver.metrics and ver.metrics.get("is_optimized") is False)
    )
    if is_pre_opt:
        return []

    query = db.query(Student)
    if department:
        query = query.filter(Student.department == department)
    if search:
        s = f"%{search}%"
        query = query.filter((Student.name.ilike(s)) | (Student.student_id.ilike(s)))
    students = query.order_by(Student.department, Student.student_id).all()

    # Compute department-wise alternating seating allocation
    seating_result = compute_department_alternating_seatings(db, version_id=ver.id)

    results = []
    for s in students:
        s_exam_seatings = []
        for en in s.enrollments:
            info = seating_result.seatings_map.get((s.id, en.exam_id))
            if not info:
                continue

            s_exam_seatings.append(StudentExamSeating(
                exam_id=info["exam_id"],
                exam_code=info["exam_code"],
                course_code=info["course_code"],
                course_name=info["course_name"],
                date=info["date"],
                day_name=info.get("day_name") or "Exam Day",
                start_time=info["start_time"],
                end_time=info["end_time"],
                period=info.get("period") or "",
                room_code=info["room_code"],
                room_name=info["room_name"],
                building=info["building"],
                room_capacity=info.get("room_capacity"),
                seat_number=info["seat_number"],
                bench_number=info.get("bench_number"),
                is_locked=info.get("is_locked", False)
            ))

        s_exam_seatings.sort(key=lambda x: (x.date, x.start_time))
        distinct_halls = len(set(e.room_code for e in s_exam_seatings))

        results.append(StudentSeatingResponse(
            id=s.id,
            student_id=s.student_id,
            name=s.name,
            department=s.department,
            semester=s.semester,
            special_accommodations=s.special_accommodations or [],
            subjects_count=len(s_exam_seatings),
            distinct_halls_count=distinct_halls,
            exams=s_exam_seatings
        ))

    return results

@router.get("/seatings/hall-charts", response_model=List[HallSeatingChart])
def get_hall_seating_charts(
    version_id: Optional[int] = None,
    room_code: Optional[str] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns visual room/hall seating charts with benches arranged department-wise alternatively
    (e.g., Bench 1: Computer Science, Bench 2: Business, etc.).
    """
    if version_id:
        ver = db.query(TimetableVersion).filter_by(id=version_id).first()
    else:
        ver = db.query(TimetableVersion).filter_by(is_active=True).first()

    if not ver:
        return []

    is_pre_opt = (
        ver.solver_status in ("PRE_OPTIMIZATION", "DRAFT", "PENDING")
        or (ver.quality_score == 0.0)
        or "pre-optimization" in (ver.name or "").lower()
        or (ver.metrics and ver.metrics.get("is_optimized") is False)
    )
    if is_pre_opt:
        return []

    seating_res = compute_department_alternating_seatings(db, version_id=ver.id)
    charts = seating_res.hall_charts

    if room_code:
        charts = [c for c in charts if c["room_code"] == room_code]
    if date:
        charts = [c for c in charts if c["date"] == date]

    return charts

@router.get("/seatings/departments", response_model=List[DepartmentSeatingSummary])
def get_departments_seating_summary(
    version_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Summarizes student seating metrics across departments.
    """
    if version_id:
        ver = db.query(TimetableVersion).filter_by(id=version_id).first()
    else:
        ver = db.query(TimetableVersion).filter_by(is_active=True).first()

    if not ver:
        return []

    is_pre_opt = (
        ver.solver_status in ("PRE_OPTIMIZATION", "DRAFT", "PENDING")
        or (ver.quality_score == 0.0)
        or "pre-optimization" in (ver.name or "").lower()
        or (ver.metrics and ver.metrics.get("is_optimized") is False)
    )
    if is_pre_opt:
        return []

    all_students = db.query(Student).all()
    assignments = db.query(TimetableAssignment).filter_by(timetable_id=ver.id).all() if ver else []
    scheduled_exam_ids = {a.exam_id for a in assignments if a.timeslot_id and a.room_id}

    dept_stats = {}
    for s in all_students:
        dept = s.department
        if dept not in dept_stats:
            dept_stats[dept] = {
                "department": dept,
                "students_count": 0,
                "total_sittings": 0,
                "distinct_exams": set()
            }
        dept_stats[dept]["students_count"] += 1
        for en in s.enrollments:
            if en.exam_id in scheduled_exam_ids:
                dept_stats[dept]["total_sittings"] += 1
                dept_stats[dept]["distinct_exams"].add(en.exam_id)

    res = []
    for dept, stats in sorted(dept_stats.items()):
        res.append(DepartmentSeatingSummary(
            department=dept,
            students_count=stats["students_count"],
            total_sittings=stats["total_sittings"],
            distinct_exams_count=len(stats["distinct_exams"])
        ))
    return res

@router.get("/{id}", response_model=StudentResponse)
def get_student_by_id(id: int, db: Session = Depends(get_db)):
    s = db.query(Student).filter_by(id=id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentResponse(
        id=s.id,
        student_id=s.student_id,
        name=s.name,
        department=s.department,
        semester=s.semester,
        special_accommodations=s.special_accommodations or [],
        enrolled_exam_ids=[en.exam_id for en in s.enrollments]
    )

@router.post("", response_model=StudentResponse)
def create_student(req: StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(Student).filter_by(student_id=req.student_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Student ID '{req.student_id}' already registered")
    
    student = Student(
        student_id=req.student_id,
        name=req.name,
        department=req.department,
        semester=req.semester,
        special_accommodations=req.special_accommodations
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return StudentResponse(
        id=student.id,
        student_id=student.student_id,
        name=student.name,
        department=student.department,
        semester=student.semester,
        special_accommodations=student.special_accommodations or [],
        enrolled_exam_ids=[]
    )

@router.put("/{id}", response_model=StudentResponse)
def update_student(id: int, req: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(id=id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if req.student_id and req.student_id != student.student_id:
        existing = db.query(Student).filter_by(student_id=req.student_id).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Student ID '{req.student_id}' already registered")
        student.student_id = req.student_id

    if req.name is not None:
        student.name = req.name
    if req.department is not None:
        student.department = req.department
    if req.semester is not None:
        student.semester = req.semester
    if req.special_accommodations is not None:
        student.special_accommodations = req.special_accommodations

    db.commit()
    db.refresh(student)
    return StudentResponse(
        id=student.id,
        student_id=student.student_id,
        name=student.name,
        department=student.department,
        semester=student.semester,
        special_accommodations=student.special_accommodations or [],
        enrolled_exam_ids=[en.exam_id for en in student.enrollments]
    )

@router.delete("/{id}", response_model=MessageResponse)
def delete_student(id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(id=id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    name = student.name
    db.delete(student)
    db.commit()
    return MessageResponse(message=f"Student '{name}' deleted successfully.")

@router.get("/{id}/timetable", response_model=List[StudentTimetableItem])
def get_student_timetable(id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(id=id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    active_ver = db.query(TimetableVersion).filter_by(is_active=True).first()
    if not active_ver:
        return []

    enrolled_exam_ids = [en.exam_id for en in student.enrollments]
    assignments = (
        db.query(TimetableAssignment)
        .filter(
            TimetableAssignment.timetable_id == active_ver.id,
            TimetableAssignment.exam_id.in_(enrolled_exam_ids)
        )
        .all()
    )

    items = []
    for a in assignments:
        exam = a.exam
        slot = a.timeslot
        room = a.room
        if slot and room:
            items.append(StudentTimetableItem(
                exam_code=exam.exam_code,
                course_code=exam.course_code,
                course_name=exam.course_name,
                date=str(slot.date),
                start_time=str(slot.start_time),
                end_time=str(slot.end_time),
                room_code=room.room_code,
                room_name=room.name,
                building=room.building,
                is_locked=a.is_locked
            ))
    # Sort chronologically
    return sorted(items, key=lambda it: (it.date, it.start_time))
