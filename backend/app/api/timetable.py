from typing import List, Optional, Dict, Any
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.timetable import TimetableVersion
from app.models.assignment import TimetableAssignment
from app.models.exam import CourseExam
from app.models.room import Room
from app.models.timeslot import TimeSlot
from app.models.student import Student
from app.models.enrollment import StudentEnrollment
from app.models.audit import AuditLog
from app.schemas.timetable import (
    AssignmentResponse, VersionResponse, GenerateRequest, ReoptimizeRequest,
    ManualAssignmentEditRequest, ValidationResult, BaselineComparisonResponse,
    BaselineComparisonItem
)
from app.schemas.common import MessageResponse
from app.solver.validator import TimetableValidator
from app.solver.engine import SchedulingEngine
from app.solver.diagnostics import SchedulingDiagnostics
from app.services.job_runner import start_optimization_job, get_job
from app.services.demo_data import seed_demo_backlogs_if_empty

router = APIRouter(prefix="/timetable", tags=["Timetable"])

def get_interval_dates(interval_days: int) -> Dict[str, date]:
    """
    Computes academic timetable dates for exam days D1 through D4:
    - Base start date: Monday Dec 14, 2026
    - Each next day advances by (1 + interval_days) calendar days.
    - Weekends (Sat/Sun) are reserved for study breaks / backlogs, so regular exams advance to Monday.
    Backlogs alone remain strictly on Saturday (Saturday Dec 19, Sundays off).
    """
    base = date(2026, 12, 14) # Monday
    days = [base]
    cur = base
    for _ in range(3):
        nxt = cur + timedelta(days=1 + interval_days)
        if nxt.weekday() == 5: # Saturday
            nxt += timedelta(days=2)
        elif nxt.weekday() == 6: # Sunday
            nxt += timedelta(days=1)
        cur = nxt
        days.append(cur)
    return {
        "SLOT-D1": days[0],
        "SLOT-D2": days[1],
        "SLOT-D3": days[2],
        "SLOT-D4": days[3],
    }

def update_slot_dates_by_interval(db: Session, interval_days: int):
    """
    Updates all regular examination TimeSlot dates as per the chosen study interval.
    Backlogs alone remain strictly on Saturday (Saturday Dec 19, Sundays off).
    """
    date_map = get_interval_dates(interval_days)
    slots = db.query(TimeSlot).all()
    for s in slots:
        for prefix, d_val in date_map.items():
            if s.slot_code.startswith(prefix):
                s.date = d_val
                break
    db.commit()

@router.post("/apply-interval")
def apply_interval_dates(interval_days: int = Query(1, ge=0, le=7), db: Session = Depends(get_db)):
    """
    Updates regular examination slot dates according to the chosen study interval policy.
    Backlogs alone remain strictly on Saturday (Saturday Dec 19, Sundays off).
    """
    update_slot_dates_by_interval(db, interval_days)
    date_map = get_interval_dates(interval_days)
    formatted = {k: v.strftime("%Y-%m-%d") for k, v in date_map.items()}
    return {
        "status": "SUCCESS",
        "study_interval_days": interval_days,
        "dates": formatted,
        "backlog_weekend": {
            "saturday": "2026-12-19",
            "sunday": "Off (No Sunday Exams)"
        }
    }

def _format_assignment_response(a: TimetableAssignment) -> AssignmentResponse:
    exam = a.exam
    slot = a.timeslot
    room = a.room
    return AssignmentResponse(
        id=a.id,
        timetable_id=a.timetable_id,
        exam_id=a.exam_id,
        exam_code=exam.exam_code if exam else f"EXAM-{a.exam_id}",
        course_code=exam.course_code if exam else "",
        course_name=exam.course_name if exam else "",
        department=exam.department if exam else "",
        duration_minutes=exam.duration_minutes if exam else 120,
        timeslot_id=a.timeslot_id,
        slot_code=slot.slot_code if slot else None,
        date=str(slot.date) if slot else None,
        start_time=str(slot.start_time) if slot else None,
        end_time=str(slot.end_time) if slot else None,
        period=slot.period if slot else None,
        room_id=a.room_id,
        room_code=room.room_code if room else None,
        room_name=room.name if room else None,
        building=room.building if room else None,
        room_capacity=room.capacity if room else None,
        assigned_student_count=a.assigned_student_count,
        is_locked=a.is_locked,
        source=a.source,
        validation_status=a.validation_status,
        conflict_reasons=a.conflict_reasons or [],
        updated_at=a.updated_at
    )

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

@router.get("", response_model=List[AssignmentResponse])
def get_current_timetable(
    version_id: Optional[int] = None,
    department: Optional[str] = None,
    room_id: Optional[int] = None,
    timeslot_id: Optional[int] = None,
    is_locked: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if version_id:
        version = db.query(TimetableVersion).filter_by(id=version_id).first()
    else:
        version = db.query(TimetableVersion).filter_by(is_active=True).first()

    if not version:
        return []

    if not version_id and check_is_pre_optimization(db):
        return []

    query = db.query(TimetableAssignment).filter(TimetableAssignment.timetable_id == version.id)
    if room_id:
        query = query.filter(TimetableAssignment.room_id == room_id)
    if timeslot_id:
        query = query.filter(TimetableAssignment.timeslot_id == timeslot_id)
    if is_locked is not None:
        query = query.filter(TimetableAssignment.is_locked == is_locked)

    assignments = query.all()
    filtered = []
    for a in assignments:
        if department and a.exam and a.exam.department != department:
            continue
        if search:
            s = search.lower()
            code_match = a.exam and s in a.exam.exam_code.lower()
            name_match = a.exam and s in a.exam.course_name.lower()
            room_match = a.room and s in a.room.room_code.lower()
            if not (code_match or name_match or room_match):
                continue
        filtered.append(_format_assignment_response(a))

    return filtered

@router.post("/generate")
def generate_timetable(req: GenerateRequest, async_job: bool = False, db: Session = Depends(get_db)):
    """Generate timetable via OR-Tools CP-SAT scheduler."""
    weights = {
        "burden": req.weight_student_burden or 100,
        "spacing": req.weight_exam_spacing or 50,
        "imbalance": req.weight_daily_imbalance or 30,
        "preference": req.weight_preference_violation or 20,
        "utilization": req.weight_room_utilization or 1,
        "reassignment": req.weight_unnecessary_changes or 20,
        "undesirable": req.weight_undesirable_session or 40,
    }

    if async_job:
        job_id = start_optimization_job(
            mode=req.mode,
            time_limit_seconds=req.time_limit_seconds,
            version_name=req.name,
            weights=weights
        )
        return {"status": "JOB_STARTED", "job_id": job_id, "mode": req.mode}

    # Update TimeSlot dates dynamically as per chosen study interval policy
    # (Backlogs alone remain strictly on Saturday: Saturday Dec 19, Sundays off)
    interval_days = req.study_interval_days if req.study_interval_days is not None else 1
    update_slot_dates_by_interval(db, interval_days)

    # Synchronous solve for immediate feedback
    exams = db.query(CourseExam).all()
    rooms = db.query(Room).all()
    slots = db.query(TimeSlot).all()
    students = db.query(Student).all()
    enrollments = db.query(StudentEnrollment).all()

    exam_dicts = [
        {
            "id": e.id, "exam_code": e.exam_code, "course_code": e.course_code,
            "course_name": e.course_name, "department": e.department,
            "duration_minutes": e.duration_minutes, "required_features": e.required_features or [],
            "eligible_slot_ids": e.eligible_slot_ids or [], "preferred_slot_ids": e.preferred_slot_ids or [],
            "priority": e.priority, "is_locked": e.is_locked
        } for e in exams
    ]
    room_dicts = [
        {
            "id": r.id, "room_code": r.room_code, "name": r.name, "building": r.building,
            "capacity": r.capacity, "is_available": r.is_available, "features": r.features or [],
            "blackout_intervals": r.blackout_intervals or []
        } for r in rooms
    ]
    slot_dicts = [
        {
            "id": s.id, "slot_code": s.slot_code, "date": s.date, "start_time": s.start_time,
            "end_time": s.end_time, "duration_minutes": s.duration_minutes, "period": s.period,
            "is_available": s.is_available, "is_blackout": s.is_blackout, "blackout_reason": s.blackout_reason
        } for s in slots
    ]
    enrollments_by_exam = {e.id: set() for e in exams}
    for en in enrollments:
        if en.exam_id in enrollments_by_exam:
            enrollments_by_exam[en.exam_id].add(en.student_id)

    locked_assignments = {}
    prev_assignments = []
    active_ver = db.query(TimetableVersion).filter_by(is_active=True).first()
    if active_ver:
        for pa in db.query(TimetableAssignment).filter_by(timetable_id=active_ver.id).all():
            prev_assignments.append({
                "exam_id": pa.exam_id, "timeslot_id": pa.timeslot_id, "room_id": pa.room_id, "is_locked": pa.is_locked
            })
            exam_obj = next((ex for ex in exams if ex.id == pa.exam_id), None)
            if (pa.is_locked or (exam_obj and exam_obj.is_locked)) and pa.timeslot_id and pa.room_id:
                locked_assignments[pa.exam_id] = (pa.timeslot_id, pa.room_id)

    engine = SchedulingEngine(
        exams=exam_dicts,
        rooms=room_dicts,
        timeslots=slot_dicts,
        enrollments=enrollments_by_exam,
        students={s.id: {"student_id": s.student_id, "name": s.name} for s in students},
        locked_assignments=locked_assignments,
        previous_assignments=prev_assignments,
        time_limit_seconds=req.time_limit_seconds,
        mode=req.mode,
        weights=weights
    )
    result = engine.solve()

    if not result.get("is_feasible"):
        return {
            "status": "INFEASIBLE",
            "solver_status": result.get("solver_status"),
            "solver_runtime_ms": result.get("solver_runtime_ms"),
            "diagnostics": result.get("diagnostics", []),
            "validation": result.get("validation", {}),
            "message": "Optimization model could not be satisfied. Review conflict diagnostics."
        }

    # Save to database
    max_ver = db.query(TimetableVersion).order_by(TimetableVersion.version_number.desc()).first()
    next_ver_num = (max_ver.version_number + 1) if max_ver else 1
    db.query(TimetableVersion).filter(TimetableVersion.is_active == True).update({"is_active": False})

    new_ver = TimetableVersion(
        version_number=next_ver_num,
        name=req.name or f"Optimized Schedule v{next_ver_num}",
        is_active=True,
        solver_status=result["solver_status"],
        solver_runtime_ms=result["solver_runtime_ms"],
        quality_score=result["quality_score"],
        objective_cost=result["objective_cost"],
        metrics=result["metrics"],
        diagnostics=result.get("diagnostics", []),
        created_by="Administrator",
        notes=f"Solved with CP-SAT in {result['solver_runtime_ms']}ms. Study Buffer: {interval_days} day(s)."
    )
    db.add(new_ver)
    db.flush()

    new_ass_objs = [
        TimetableAssignment(
            timetable_id=new_ver.id,
            exam_id=a["exam_id"],
            timeslot_id=a["timeslot_id"],
            room_id=a["room_id"],
            assigned_student_count=a["assigned_student_count"],
            is_locked=a["is_locked"],
            source="AUTOMATIC",
            validation_status=a["validation_status"]
        ) for a in result["assignments"]
    ]
    db.bulk_save_objects(new_ass_objs)
    db.commit()
    seed_demo_backlogs_if_empty(db)


    return {
        "status": "SUCCESS",
        "version_id": new_ver.id,
        "version_number": new_ver.version_number,
        "solver_status": new_ver.solver_status,
        "solver_runtime_ms": new_ver.solver_runtime_ms,
        "quality_score": new_ver.quality_score,
        "metrics": new_ver.metrics,
        "study_interval_days": interval_days
    }

@router.post("/reoptimize")
def reoptimize_timetable(req: ReoptimizeRequest, async_job: bool = False, db: Session = Depends(get_db)):
    gen_req = GenerateRequest(
        name=req.name or "Re-Optimized Schedule (Minimal Change)",
        time_limit_seconds=req.time_limit_seconds,
        mode="minimal_change" if req.mode == "minimal_change" else "full",
        weight_student_burden=req.weight_student_burden,
        weight_exam_spacing=req.weight_exam_spacing,
        weight_daily_imbalance=req.weight_daily_imbalance,
        weight_preference_violation=req.weight_preference_violation,
        weight_room_utilization=req.weight_room_utilization,
        weight_unnecessary_changes=req.weight_unnecessary_changes or 150,
        weight_undesirable_session=req.weight_undesirable_session
    )
    return generate_timetable(req=gen_req, async_job=async_job, db=db)

@router.get("/jobs/{job_id}")
def check_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/validate", response_model=ValidationResult)
def validate_timetable(version_id: Optional[int] = None, db: Session = Depends(get_db)):
    if version_id:
        version = db.query(TimetableVersion).filter_by(id=version_id).first()
    else:
        version = db.query(TimetableVersion).filter_by(is_active=True).first()

    if not version:
        raise HTTPException(status_code=404, detail="No active timetable version found to validate")

    exams = db.query(CourseExam).all()
    rooms = db.query(Room).all()
    slots = db.query(TimeSlot).all()
    students = db.query(Student).all()
    enrollments = db.query(StudentEnrollment).all()
    assignments = db.query(TimetableAssignment).filter_by(timetable_id=version.id).all()

    exam_dicts = [{"id": e.id, "exam_code": e.exam_code, "course_name": e.course_name, "duration_minutes": e.duration_minutes, "required_features": e.required_features or []} for e in exams]
    room_dicts = [{"id": r.id, "room_code": r.room_code, "capacity": r.capacity, "is_available": r.is_available, "features": r.features or [], "blackout_intervals": r.blackout_intervals or []} for r in rooms]
    slot_dicts = [{"id": s.id, "slot_code": s.slot_code, "date": s.date, "start_time": s.start_time, "duration_minutes": s.duration_minutes, "is_available": s.is_available, "is_blackout": s.is_blackout, "blackout_reason": s.blackout_reason} for s in slots]
    
    en_map = {e.id: set() for e in exams}
    for en in enrollments:
        if en.exam_id in en_map:
            en_map[en.exam_id].add(en.student_id)

    ass_dicts = [{"exam_id": a.exam_id, "timeslot_id": a.timeslot_id, "room_id": a.room_id, "is_locked": a.is_locked} for a in assignments]
    locked_map = {a.exam_id: (a.timeslot_id, a.room_id) for a in assignments if a.is_locked and a.timeslot_id and a.room_id}

    is_pre_opt = (
        version.solver_status in ("PRE_OPTIMIZATION", "DRAFT", "PENDING")
        or (version.quality_score or 0.0) == 0.0
        or len(assignments) == 0
    )

    validator = TimetableValidator(
        exams=exam_dicts,
        rooms=room_dicts,
        timeslots=slot_dicts,
        enrollments=en_map,
        assignments=ass_dicts,
        locked_assignments=locked_map,
        students={s.id: {"student_id": s.student_id, "name": s.name} for s in students},
        is_pre_optimization=is_pre_opt
    )
    result = validator.validate()
    return result

@router.patch("/assignments/{id}")
def update_assignment_manually(id: int, req: ManualAssignmentEditRequest, db: Session = Depends(get_db)):
    assignment = db.query(TimetableAssignment).filter_by(id=id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    new_slot_id = req.timeslot_id if req.timeslot_id is not None else assignment.timeslot_id
    new_room_id = req.room_id if req.room_id is not None else assignment.room_id
    new_locked = req.is_locked if req.is_locked is not None else assignment.is_locked

    # Check hard constraints before committing manual change
    if not req.force_apply:
        exam = assignment.exam
        slot = db.query(TimeSlot).filter_by(id=new_slot_id).first() if new_slot_id else None
        room = db.query(Room).filter_by(id=new_room_id).first() if new_room_id else None

        if slot and room and exam:
            # Check duration
            if exam.duration_minutes > slot.duration_minutes:
                raise HTTPException(
                    status_code=400,
                    detail=f"Duration violation: Exam requires {exam.duration_minutes}m, slot is {slot.duration_minutes}m."
                )
            # Check capacity
            enrolled_cnt = db.query(StudentEnrollment).filter_by(exam_id=exam.id).count()
            if enrolled_cnt > room.capacity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Capacity violation: Room '{room.room_code}' capacity is {room.capacity}, but exam has {enrolled_cnt} students."
                )
            # Check blackout
            if slot.is_blackout or not slot.is_available:
                raise HTTPException(
                    status_code=400,
                    detail=f"Time slot '{slot.slot_code}' is marked blackout ({slot.blackout_reason or 'holiday'})."
                )
            # Check room double booking
            other_in_room = (
                db.query(TimetableAssignment)
                .filter(
                    TimetableAssignment.timetable_id == assignment.timetable_id,
                    TimetableAssignment.timeslot_id == new_slot_id,
                    TimetableAssignment.room_id == new_room_id,
                    TimetableAssignment.id != assignment.id
                )
                .first()
            )
            if other_in_room:
                raise HTTPException(
                    status_code=400,
                    detail=f"Room '{room.room_code}' is already booked for exam '{other_in_room.exam.exam_code}' at slot '{slot.slot_code}'."
                )

    assignment.timeslot_id = new_slot_id
    assignment.room_id = new_room_id
    assignment.is_locked = new_locked
    assignment.source = "MANUAL"
    db.commit()
    db.refresh(assignment)

    return _format_assignment_response(assignment)

@router.patch("/assignments/{id}/lock")
def toggle_assignment_lock(id: int, lock: Optional[bool] = None, db: Session = Depends(get_db)):
    assignment = db.query(TimetableAssignment).filter_by(id=id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment.is_locked = (not assignment.is_locked) if lock is None else lock
    # Also keep exam.is_locked synced
    if assignment.exam:
        assignment.exam.is_locked = assignment.is_locked
    db.commit()
    return {"id": assignment.id, "exam_code": assignment.exam.exam_code if assignment.exam else None, "is_locked": assignment.is_locked}

@router.get("/versions", response_model=List[VersionResponse])
def get_timetable_versions(db: Session = Depends(get_db)):
    versions = db.query(TimetableVersion).order_by(TimetableVersion.version_number.desc()).all()
    results = []
    for v in versions:
        vr = VersionResponse.model_validate(v)
        vr.total_assignments = len(v.assignments)
        vr.scheduled_count = len([a for a in v.assignments if a.timeslot_id and a.room_id])
        vr.unscheduled_count = vr.total_assignments - vr.scheduled_count
        results.append(vr)
    return results

@router.post("/restore/{version_id}", response_model=MessageResponse)
def restore_version(version_id: int, db: Session = Depends(get_db)):
    target = db.query(TimetableVersion).filter_by(id=version_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Version not found")
    db.query(TimetableVersion).update({"is_active": False})
    target.is_active = True
    db.add(AuditLog(action="RESTORE", entity_type="TIMETABLE", entity_id=str(version_id), details={"version_number": target.version_number}))
    db.commit()
    return MessageResponse(message=f"Version v{target.version_number} ('{target.name}') restored as active timetable.")

@router.get("/compare", response_model=BaselineComparisonResponse)
def compare_timetable_versions(
    baseline_id: Optional[int] = None,
    current_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    if baseline_id:
        baseline_ver = db.query(TimetableVersion).filter_by(id=baseline_id).first()
    else:
        # Lowest version number or baseline version
        baseline_ver = db.query(TimetableVersion).order_by(TimetableVersion.version_number.asc()).first()

    if current_id:
        current_ver = db.query(TimetableVersion).filter_by(id=current_id).first()
    else:
        current_ver = db.query(TimetableVersion).filter_by(is_active=True).first()

    if not baseline_ver or not current_ver:
        raise HTTPException(status_code=400, detail="Need at least one active or saved timetable version to compare")

    b_metrics = baseline_ver.metrics or {}
    c_metrics = current_ver.metrics or {}

    keys_to_compare = [
        ("quality_score", "Quality Score (0-100)", True),
        ("pct_multiple_same_day", "% Students with Multiple Exams/Day", False),
        ("back_to_back_exam_count", "Back-to-Back Exam Sessions", False),
        ("avg_gap_days", "Average Gap Between Exams (Days)", True),
        ("room_utilization_pct", "Room Seating Utilization %", True),
        ("daily_imbalance_std", "Daily Exam Skew (Std Dev)", False),
        ("total_objective_cost", "Total Weighted Penalty Cost", False)
    ]

    comparisons = []
    for key, label, higher_is_better in keys_to_compare:
        b_val = float(b_metrics.get(key, 0.0))
        c_val = float(c_metrics.get(key, 0.0))
        diff = round(c_val - b_val, 2)
        pct = round((diff / b_val) * 100, 1) if b_val != 0 else None
        is_imp = (diff > 0) if higher_is_better else (diff < 0)

        comparisons.append(BaselineComparisonItem(
            metric_key=key,
            metric_label=label,
            baseline_value=b_val,
            current_value=c_val,
            absolute_diff=diff,
            percentage_change=pct,
            is_improvement=is_imp
        ))

    return BaselineComparisonResponse(
        baseline_version_id=baseline_ver.id,
        baseline_version_name=baseline_ver.name,
        current_version_id=current_ver.id,
        current_version_name=current_ver.name,
        comparisons=comparisons
    )
