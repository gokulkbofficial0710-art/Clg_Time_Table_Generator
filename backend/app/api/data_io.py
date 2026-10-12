import io
import csv
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.timetable import TimetableVersion
from app.models.assignment import TimetableAssignment
from app.schemas.import_export import ImportPreviewResponse, ImportCommitRequest
from app.schemas.common import MessageResponse
from app.services.csv_handler import parse_and_preview_csv, commit_imported_data, CSV_TEMPLATES
from app.services.demo_data import load_demo_dataset, create_infeasible_scenario, reset_infeasible_scenario
from app.services.pdf_exporter import generate_timetable_pdf

router = APIRouter(prefix="", tags=["Import / Export & Demo Data"])

@router.get("/import/template/{entity_type}")
def get_csv_template(entity_type: str):
    template = CSV_TEMPLATES.get(entity_type.lower())
    if not template:
        raise HTTPException(status_code=404, detail=f"No template available for '{entity_type}'")
    return Response(
        content=template,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entity_type}_template.csv"}
    )

@router.post("/import/preview", response_model=ImportPreviewResponse)
async def preview_csv_import(
    entity_type: str = Form(...),
    file: UploadFile = File(...)
):
    contents = await file.read()
    text = contents.decode("utf-8-sig", errors="replace")
    preview = parse_and_preview_csv(entity_type.lower(), text)
    return preview

@router.post("/import/commit", response_model=MessageResponse)
def commit_csv_import(req: ImportCommitRequest, db: Session = Depends(get_db)):
    result = commit_imported_data(db, req.entity_type.lower(), req.items, overwrite=req.overwrite_existing)
    return MessageResponse(
        message=f"Successfully imported {result['committed_count']} {req.entity_type} records.",
        details=result
    )

@router.post("/data/load-demo", response_model=MessageResponse)
def load_demo(include_infeasible: bool = False, db: Session = Depends(get_db)):
    stats = load_demo_dataset(db, include_infeasible=include_infeasible)
    return MessageResponse(
        message=f"Deterministic demo dataset loaded successfully ({stats['exams_count']} exams, {stats['students_count']} students, {stats['rooms_count']} rooms).",
        details=stats
    )

@router.post("/data/load-infeasible", response_model=MessageResponse)
def load_infeasible(db: Session = Depends(get_db)):
    res = create_infeasible_scenario(db)
    return MessageResponse(
        message="Infeasible scenario configured: conflicting exams locked to identical slot and room.",
        details=res
    )

@router.post("/data/reset-infeasible", response_model=MessageResponse)
def reset_infeasible(db: Session = Depends(get_db)):
    res = reset_infeasible_scenario(db)
    return MessageResponse(
        message="Infeasible scenario cleared: conflicting locks removed.",
        details=res
    )

@router.get("/export/timetable/csv")
def export_timetable_csv(version_id: Optional[int] = None, db: Session = Depends(get_db)):
    ver = db.query(TimetableVersion).filter_by(id=version_id).first() if version_id else db.query(TimetableVersion).filter_by(is_active=True).first()
    if not ver:
        raise HTTPException(status_code=404, detail="No active timetable version found to export")

    assignments = db.query(TimetableAssignment).filter_by(timetable_id=ver.id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Exam Code", "Course Code", "Course Name", "Department", "Duration (min)",
        "Date", "Start Time", "End Time", "Period",
        "Room Code", "Room Name", "Building", "Capacity",
        "Enrolled Students", "Locked", "Source", "Validation Status"
    ])

    for a in assignments:
        exam = a.exam
        slot = a.timeslot
        room = a.room
        writer.writerow([
            exam.exam_code if exam else "",
            exam.course_code if exam else "",
            exam.course_name if exam else "",
            exam.department if exam else "",
            exam.duration_minutes if exam else "",
            str(slot.date) if slot else "UNSCHEDULED",
            str(slot.start_time) if slot else "",
            str(slot.end_time) if slot else "",
            slot.period if slot else "",
            room.room_code if room else "UNSCHEDULED",
            room.name if room else "",
            room.building if room else "",
            room.capacity if room else "",
            a.assigned_student_count,
            "YES" if a.is_locked else "NO",
            a.source,
            a.validation_status
        ])

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=timetable_v{ver.version_number}.csv"}
    )

@router.get("/export/timetable/pdf")
def export_timetable_pdf(version_id: Optional[int] = None, report_type: str = "master", db: Session = Depends(get_db)):
    ver = db.query(TimetableVersion).filter_by(id=version_id).first() if version_id else db.query(TimetableVersion).filter_by(is_active=True).first()
    if not ver:
        raise HTTPException(status_code=404, detail="No active timetable version found to export")

    assignments = db.query(TimetableAssignment).filter_by(timetable_id=ver.id).all()
    ass_data = []
    for a in assignments:
        exam = a.exam
        slot = a.timeslot
        room = a.room
        ass_data.append({
            "exam_code": exam.exam_code if exam else "",
            "course_name": exam.course_name if exam else "",
            "department": exam.department if exam else "",
            "date": str(slot.date) if slot else "Unscheduled",
            "start_time": str(slot.start_time) if slot else "",
            "end_time": str(slot.end_time) if slot else "",
            "period": slot.period if slot else "",
            "room_code": room.room_code if room else "TBA",
            "building": room.building if room else "",
            "room_capacity": room.capacity if room else 0,
            "assigned_student_count": a.assigned_student_count,
            "is_locked": a.is_locked
        })

    pdf_bytes = generate_timetable_pdf(
        assignments=ass_data,
        timetable_name=ver.name,
        metrics=ver.metrics,
        report_type=report_type
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=timetable_v{ver.version_number}.pdf"}
    )

@router.get("/export/students/seatings/pdf")
def export_students_seatings_pdf(
    department: Optional[str] = None,
    version_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Exports Department Student Seating & Hall Allocations Ledger as PDF.
    """
    from datetime import datetime
    from app.models.student import Student
    from app.models.enrollment import StudentEnrollment
    from app.services.pdf_exporter import generate_department_seatings_pdf

    ver = db.query(TimetableVersion).filter_by(id=version_id).first() if version_id else db.query(TimetableVersion).filter_by(is_active=True).first()
    if not ver:
        raise HTTPException(status_code=404, detail="No active timetable version found to export")

    is_pre_opt = (
        ver.solver_status in ("PRE_OPTIMIZATION", "DRAFT", "PENDING")
        or (ver.quality_score == 0.0)
        or "pre-optimization" in (ver.name or "").lower()
        or (ver.metrics and ver.metrics.get("is_optimized") is False)
    )
    if is_pre_opt:
        raise HTTPException(status_code=400, detail="Student seating allocations are cleared in pre-optimization state. Please extract the optimized timetable first.")

    query = db.query(Student)
    if department:
        query = query.filter(Student.department == department)
    students = query.order_by(Student.department, Student.student_id).all()

    assignments = db.query(TimetableAssignment).filter_by(timetable_id=ver.id).all()
    assignment_by_exam_id = {a.exam_id: a for a in assignments}

    all_enrollments = db.query(StudentEnrollment).all()
    exam_students_map = {}
    for en in all_enrollments:
        exam_students_map.setdefault(en.exam_id, []).append(en.student_id)
    for e_id in exam_students_map:
        exam_students_map[e_id].sort()

    students_seatings_data = []
    for s in students:
        s_exams = []
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

            s_exams.append({
                "exam_code": exam.exam_code,
                "course_code": exam.course_code,
                "course_name": exam.course_name,
                "date": date_str,
                "day_name": day_name,
                "start_time": str(slot.start_time),
                "end_time": str(slot.end_time),
                "period": slot.period or "",
                "room_code": room.room_code,
                "room_name": room.name,
                "building": room.building,
                "seat_number": seat_str,
                "is_locked": a.is_locked
            })

        s_exams.sort(key=lambda x: (x["date"], x["start_time"]))
        students_seatings_data.append({
            "id": s.id,
            "student_id": s.student_id,
            "name": s.name,
            "department": s.department,
            "semester": s.semester,
            "special_accommodations": s.special_accommodations or [],
            "exams": s_exams
        })

    pdf_bytes = generate_department_seatings_pdf(
        department=department,
        students_seatings=students_seatings_data,
        timetable_name=ver.name,
        metrics=ver.metrics
    )

    safe_dept = (department.replace(" ", "_").lower()) if department else "all_departments"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=seating_roster_{safe_dept}_v{ver.version_number}.pdf"}
    )

@router.get("/export/students/{id}/hall-ticket/pdf")
def export_student_hall_ticket_pdf(
    id: int,
    version_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Exports a single student's Official Examination Hall Ticket / Admit Card as PDF.
    """
    from datetime import datetime
    from app.models.student import Student
    from app.models.enrollment import StudentEnrollment
    from app.services.pdf_exporter import generate_student_hall_ticket_pdf

    student = db.query(Student).filter_by(id=id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")

    ver = db.query(TimetableVersion).filter_by(id=version_id).first() if version_id else db.query(TimetableVersion).filter_by(is_active=True).first()
    if not ver:
        raise HTTPException(status_code=404, detail="No active timetable version found to export")

    is_pre_opt = (
        ver.solver_status in ("PRE_OPTIMIZATION", "DRAFT", "PENDING")
        or (ver.quality_score == 0.0)
        or "pre-optimization" in (ver.name or "").lower()
        or (ver.metrics and ver.metrics.get("is_optimized") is False)
    )
    if is_pre_opt:
        raise HTTPException(status_code=400, detail="Student seating allocations are cleared in pre-optimization state. Please extract the optimized timetable first.")

    assignments = db.query(TimetableAssignment).filter_by(timetable_id=ver.id).all()
    assignment_by_exam_id = {a.exam_id: a for a in assignments}

    all_enrollments = db.query(StudentEnrollment).all()
    exam_students_map = {}
    for en in all_enrollments:
        exam_students_map.setdefault(en.exam_id, []).append(en.student_id)
    for e_id in exam_students_map:
        exam_students_map[e_id].sort()

    student_exams = []
    for en in student.enrollments:
        a = assignment_by_exam_id.get(en.exam_id)
        if not a or not a.timeslot or not a.room:
            continue
        exam = a.exam
        slot = a.timeslot
        room = a.room
        if not exam:
            continue

        enrolled_list = exam_students_map.get(exam.id, [])
        seat_idx = (enrolled_list.index(student.id) + 1) if student.id in enrolled_list else 1
        seat_str = f"{room.room_code}-D{seat_idx:02d}"

        date_str = str(slot.date)
        try:
            date_dt = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = date_dt.strftime("%A")
        except Exception:
            day_name = "Exam Day"

        student_exams.append({
            "exam_code": exam.exam_code,
            "course_code": exam.course_code,
            "course_name": exam.course_name,
            "date": date_str,
            "day_name": day_name,
            "start_time": str(slot.start_time),
            "end_time": str(slot.end_time),
            "period": slot.period or "",
            "room_code": room.room_code,
            "room_name": room.name,
            "building": room.building,
            "seat_number": seat_str,
            "is_locked": a.is_locked
        })

    student_exams.sort(key=lambda x: (x["date"], x["start_time"]))

    student_data = {
        "student_id": student.student_id,
        "name": student.name,
        "department": student.department,
        "semester": student.semester,
        "special_accommodations": student.special_accommodations or []
    }

    pdf_bytes = generate_student_hall_ticket_pdf(
        student_data=student_data,
        exams_seatings=student_exams,
        timetable_name=ver.name
    )

    safe_id = student.student_id.replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=hall_ticket_{safe_id}.pdf"}
    )

@router.get("/export/students/seatings/csv")
def export_students_seatings_csv(
    department: Optional[str] = None,
    version_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Exports student examination seating allocations as a CSV spreadsheet.
    """
    from datetime import datetime
    from app.models.student import Student
    from app.models.enrollment import StudentEnrollment

    ver = db.query(TimetableVersion).filter_by(id=version_id).first() if version_id else db.query(TimetableVersion).filter_by(is_active=True).first()
    if not ver:
        raise HTTPException(status_code=404, detail="No active timetable version found")

    is_pre_opt = (
        ver.solver_status in ("PRE_OPTIMIZATION", "DRAFT", "PENDING")
        or (ver.quality_score == 0.0)
        or "pre-optimization" in (ver.name or "").lower()
        or (ver.metrics and ver.metrics.get("is_optimized") is False)
    )
    if is_pre_opt:
        raise HTTPException(status_code=400, detail="Student seating allocations are cleared in pre-optimization state. Please extract the optimized timetable first.")

    query = db.query(Student)
    if department:
        query = query.filter(Student.department == department)
    students = query.order_by(Student.department, Student.student_id).all()

    assignments = db.query(TimetableAssignment).filter_by(timetable_id=ver.id).all()
    assignment_by_exam_id = {a.exam_id: a for a in assignments}

    all_enrollments = db.query(StudentEnrollment).all()
    exam_students_map = {}
    for en in all_enrollments:
        exam_students_map.setdefault(en.exam_id, []).append(en.student_id)
    for e_id in exam_students_map:
        exam_students_map[e_id].sort()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Student ID", "Candidate Name", "Department", "Semester", "Special Accommodations",
        "Exam Code", "Course Code", "Course Title", "Exam Date", "Day",
        "Start Time", "End Time", "Period",
        "Room Code", "Room Name", "Building Venue", "Allocated Seat / Desk", "Is Locked"
    ])

    for s in students:
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

            writer.writerow([
                s.student_id, s.name, s.department, s.semester,
                ", ".join(s.special_accommodations or []),
                exam.exam_code, exam.course_code, exam.course_name,
                date_str, day_name,
                str(slot.start_time), str(slot.end_time), slot.period or "",
                room.room_code, room.name, room.building,
                seat_str, "YES" if a.is_locked else "NO"
            ])

    output.seek(0)
    safe_dept = (department.replace(" ", "_").lower()) if department else "all_departments"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=seating_roster_{safe_dept}_v{ver.version_number}.csv"}
    )

