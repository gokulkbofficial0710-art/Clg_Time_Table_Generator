from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.student import Student
from app.models.enrollment import StudentEnrollment
from app.models.exam import CourseExam
from app.models.timetable import TimetableVersion
from app.models.assignment import TimetableAssignment
from app.schemas.student import (
    StudentCreate, StudentUpdate, StudentResponse, StudentTimetableItem,
    StudentExamSeating, StudentSeatingResponse, DepartmentSeatingSummary
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/students", tags=["Students"])

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

    # Pre-fetch assignments for this version
    assignments = db.query(TimetableAssignment).filter_by(timetable_id=ver.id).all()
    assignment_by_exam_id = {a.exam_id: a for a in assignments}

    # Map enrollments for deterministic desk numbering per exam session
    all_enrollments = db.query(StudentEnrollment).all()
    exam_students_map = {}
    for en in all_enrollments:
        exam_students_map.setdefault(en.exam_id, []).append(en.student_id)
    for e_id in exam_students_map:
        exam_students_map[e_id].sort()

    results = []
    for s in students:
        s_exam_seatings = []
        for en in s.enrollments:
            a = assignment_by_exam_id.get(en.exam_id)
            if not a or not a.timeslot or not a.room:
                continue
            exam = a.exam
            slot = a.timeslot
            room = a.room
            if not exam:
                continue

            enrolled_list = exam_students_map.get(exam.id, [])
            seat_idx = (enrolled_list.index(s.id) + 1) if s.id in enrolled_list else 1
            seat_str = f"{room.room_code}-D{seat_idx:02d}"

            date_str = str(slot.date)
            try:
                date_dt = datetime.strptime(date_str, "%Y-%m-%d")
                day_name = date_dt.strftime("%A")
            except Exception:
                day_name = "Exam Day"

            s_exam_seatings.append(StudentExamSeating(
                exam_id=exam.id,
                exam_code=exam.exam_code,
                course_code=exam.course_code,
                course_name=exam.course_name,
                date=date_str,
                day_name=day_name,
                start_time=str(slot.start_time),
                end_time=str(slot.end_time),
                period=slot.period,
                room_code=room.room_code,
                room_name=room.name,
                building=room.building,
                room_capacity=room.capacity,
                seat_number=seat_str,
                is_locked=a.is_locked
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
