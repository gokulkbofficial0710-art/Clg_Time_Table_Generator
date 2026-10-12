import io
import csv
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.backlog import BacklogRecord
from app.models.timetable import TimetableVersion
from app.schemas.backlog import (
    BacklogCreateRequest,
    BacklogResponse,
    BacklogSummaryResponse
)
from app.services.pdf_exporter import generate_backlogs_pdf, generate_backlog_admit_card_pdf

router = APIRouter(prefix="/backlogs", tags=["Academic Registry - Backlogs"])

def check_is_pre_optimization(db: Session) -> bool:
    ver = db.query(TimetableVersion).filter_by(is_active=True).first()
    if not ver:
        return True
    return (
        ver.solver_status in ("PRE_OPTIMIZATION", "DRAFT", "PENDING")
        or (ver.quality_score == 0.0)
        or "pre-optimization" in (ver.name or "").lower()
        or (ver.metrics and ver.metrics.get("is_optimized") is False)
    )

@router.get("", response_model=List[BacklogResponse])
def get_backlogs(
    department: Optional[str] = None,
    student_type: Optional[str] = None,
    semester_type: Optional[str] = None,
    current_semester: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # If the timetable is in pre-optimization baseline state, backlog details are cleared & empty
    if check_is_pre_optimization(db):
        return []

    query = db.query(BacklogRecord)

    if department and department != "ALL":
        query = query.filter(BacklogRecord.department == department)
    if student_type and student_type != "ALL":
        query = query.filter(BacklogRecord.student_type == student_type)
    if semester_type and semester_type != "ALL":
        query = query.filter(BacklogRecord.semester_type == semester_type)
    if current_semester and current_semester != "ALL":
        query = query.filter(BacklogRecord.current_semester == current_semester)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (BacklogRecord.student_name.ilike(s)) |
            (BacklogRecord.student_code.ilike(s)) |
            (BacklogRecord.course_code.ilike(s)) |
            (BacklogRecord.course_name.ilike(s))
        )

    return query.order_by(BacklogRecord.exam_date, BacklogRecord.start_time, BacklogRecord.student_code).all()

@router.post("", response_model=BacklogResponse)
def create_backlog(
    req: BacklogCreateRequest,
    db: Session = Depends(get_db)
):
    # Auto-infer semester type (Odd vs Even) from backlog_semester
    b_sem_str = req.backlog_semester.lower()
    if any(digit in b_sem_str for digit in ["1", "3", "5", "7"]):
        inferred_sem_type = "Odd Semester"
    elif any(digit in b_sem_str for digit in ["2", "4", "6", "8"]):
        inferred_sem_type = "Even Semester"
    else:
        inferred_sem_type = req.semester_type or "Odd Semester"

    sem_type = req.semester_type or inferred_sem_type

    # Saturday scheduling: Backlogs are held strictly on Saturday (Sundays off)
    existing_count = db.query(BacklogRecord).count()
    if not req.exam_date or not req.exam_day or (req.exam_day and req.exam_day.lower() == "sunday"):
        exam_date = "2026-12-19"
        exam_day = "Saturday"
    else:
        exam_date = req.exam_date
        exam_day = req.exam_day

    # Session period on Saturday (alternate Morning vs Afternoon if not specified)
    period = req.period or ("Morning" if existing_count % 2 == 0 else "Afternoon")
    start_time = req.start_time or ("09:30:00" if period == "Morning" else "14:00:00")
    end_time = req.end_time or ("12:30:00" if period == "Morning" else "17:00:00")

    # Hall / Room allocation
    room_code = req.room_code or ("AUD-MAIN" if existing_count % 3 == 0 else "HALL-101" if existing_count % 3 == 1 else "LAB-COMP")
    room_name = req.room_name or (
        "Grand University Auditorium" if room_code == "AUD-MAIN" else
        "Science Lecture Hall A" if room_code == "HALL-101" else
        "Advanced Computing Laboratory"
    )

    # Deterministic desk numbering
    seat_num = req.seat_number or f"{room_code}-BK{existing_count + 1:02d}"

    record = BacklogRecord(
        student_code=req.student_code.strip(),
        student_name=req.student_name.strip(),
        department=req.department.strip(),
        student_type=req.student_type,
        current_semester=req.current_semester.strip(),
        backlog_semester=req.backlog_semester.strip(),
        semester_type=sem_type,
        course_code=req.course_code.strip().upper(),
        course_name=req.course_name.strip(),
        exam_date=exam_date,
        exam_day=exam_day,
        start_time=start_time,
        end_time=end_time,
        period=period,
        room_code=room_code,
        room_name=room_name,
        seat_number=seat_num,
        status="SCHEDULED"
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{id}")
def delete_backlog(id: int, db: Session = Depends(get_db)):
    rec = db.query(BacklogRecord).filter_by(id=id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Backlog record not found")
    db.delete(rec)
    db.commit()
    return {"message": "Backlog record resolved/deleted successfully", "id": id}

@router.get("/summary", response_model=BacklogSummaryResponse)
def get_backlogs_summary(department: Optional[str] = None, db: Session = Depends(get_db)):
    if check_is_pre_optimization(db):
        return BacklogSummaryResponse(
            total_backlogs=0,
            old_students_count=0,
            new_students_count=0,
            odd_sem_backlogs_count=0,
            even_sem_backlogs_count=0,
            weekend_sessions_count=0,
            venues_allocated_count=0,
            department_counts={},
            active_department=department,
            is_pre_optimization=True
        )

    all_recs = db.query(BacklogRecord).all()
    dept_counts = {}
    for r in all_recs:
        dept_counts[r.department] = dept_counts.get(r.department, 0) + 1

    filtered_recs = all_recs
    if department and department != "ALL":
        filtered_recs = [r for r in all_recs if r.department == department]

    total = len(filtered_recs)
    old_students = sum(1 for r in filtered_recs if r.student_type == "Old Student")
    new_students = sum(1 for r in filtered_recs if r.student_type == "New Student")
    odd_sem = sum(1 for r in filtered_recs if "Odd" in r.semester_type)
    even_sem = sum(1 for r in filtered_recs if "Even" in r.semester_type)
    weekend_sessions = len(set((r.exam_date, r.period) for r in filtered_recs))
    venues = len(set(r.room_code for r in filtered_recs if r.room_code))

    return BacklogSummaryResponse(
        total_backlogs=total,
        old_students_count=old_students,
        new_students_count=new_students,
        odd_sem_backlogs_count=odd_sem,
        even_sem_backlogs_count=even_sem,
        weekend_sessions_count=weekend_sessions,
        venues_allocated_count=venues,
        department_counts=dept_counts,
        active_department=department,
        is_pre_optimization=False
    )

@router.get("/{id}/admit-card/pdf")
def export_backlog_admit_card_pdf(id: int, db: Session = Depends(get_db)):
    rec = db.query(BacklogRecord).filter_by(id=id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Backlog candidate record not found")

    if check_is_pre_optimization(db):
        raise HTTPException(
            status_code=400,
            detail="Backlog examination seatings are cleared in pre-optimization state. Please extract the optimized timetable first."
        )

    backlog_data = {
        "student_code": rec.student_code,
        "student_name": rec.student_name,
        "department": rec.department,
        "student_type": rec.student_type,
        "current_semester": rec.current_semester,
        "backlog_semester": rec.backlog_semester,
        "semester_type": rec.semester_type,
        "course_code": rec.course_code,
        "course_name": rec.course_name,
        "exam_date": rec.exam_date,
        "exam_day": rec.exam_day,
        "start_time": rec.start_time,
        "end_time": rec.end_time,
        "period": rec.period,
        "room_code": rec.room_code,
        "room_name": rec.room_name,
        "seat_number": rec.seat_number,
        "status": rec.status,
    }
    pdf_bytes = generate_backlog_admit_card_pdf(backlog_data)
    safe_code = rec.student_code.replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=admit_card_backlog_{safe_code}.pdf"}
    )

@router.get("/export/pdf")
def export_backlogs_pdf(
    department: Optional[str] = None,
    student_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if check_is_pre_optimization(db):
        raise HTTPException(
            status_code=400,
            detail="Backlog examination records are cleared in pre-optimization state. Please extract the optimized timetable first."
        )

    query = db.query(BacklogRecord)
    if department and department != "ALL":
        query = query.filter(BacklogRecord.department == department)
    if student_type and student_type != "ALL":
        query = query.filter(BacklogRecord.student_type == student_type)

    records = query.order_by(BacklogRecord.exam_date, BacklogRecord.start_time, BacklogRecord.student_code).all()

    backlogs_data = [
        {
            "id": r.id,
            "student_code": r.student_code,
            "student_name": r.student_name,
            "department": r.department,
            "student_type": r.student_type,
            "current_semester": r.current_semester,
            "backlog_semester": r.backlog_semester,
            "semester_type": r.semester_type,
            "course_code": r.course_code,
            "course_name": r.course_name,
            "exam_date": r.exam_date,
            "exam_day": r.exam_day,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "period": r.period,
            "room_code": r.room_code,
            "room_name": r.room_name,
            "seat_number": r.seat_number,
        }
        for r in records
    ]

    pdf_bytes = generate_backlogs_pdf(backlogs=backlogs_data, department_filter=department)

    safe_dept = (department.replace(" ", "_").lower()) if department and department != "ALL" else "all_departments"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=backlog_schedule_{safe_dept}.pdf"}
    )

@router.get("/export/csv")
def export_backlogs_csv(
    department: Optional[str] = None,
    student_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if check_is_pre_optimization(db):
        raise HTTPException(
            status_code=400,
            detail="Backlog examination records are cleared in pre-optimization state. Please extract the optimized timetable first."
        )

    query = db.query(BacklogRecord)
    if department and department != "ALL":
        query = query.filter(BacklogRecord.department == department)
    if student_type and student_type != "ALL":
        query = query.filter(BacklogRecord.student_type == student_type)

    records = query.order_by(BacklogRecord.exam_date, BacklogRecord.start_time, BacklogRecord.student_code).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Record ID", "Student ID", "Candidate Name", "Department",
        "Student Status", "Current Semester", "Backlog Semester", "Semester Cycle",
        "Course Code", "Course Title", "Exam Date", "Day of Week",
        "Start Time", "End Time", "Session Period", "Venue Code", "Venue Name", "Seat Desk Number", "Status"
    ])

    for r in records:
        writer.writerow([
            r.id, r.student_code, r.student_name, r.department,
            r.student_type, r.current_semester, r.backlog_semester, r.semester_type,
            r.course_code, r.course_name, r.exam_date, r.exam_day,
            r.start_time, r.end_time, r.period, r.room_code, r.room_name, r.seat_number, r.status
        ])

    csv_data = output.getvalue()
    safe_dept = (department.replace(" ", "_").lower()) if department and department != "ALL" else "all_departments"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=backlog_schedule_{safe_dept}.csv"}
    )
