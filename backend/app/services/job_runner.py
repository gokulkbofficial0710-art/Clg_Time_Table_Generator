import threading
import uuid
import time
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.room import Room
from app.models.timeslot import TimeSlot
from app.models.student import Student
from app.models.enrollment import StudentEnrollment
from app.models.exam import CourseExam
from app.models.timetable import TimetableVersion
from app.models.assignment import TimetableAssignment
from app.models.audit import AuditLog
from app.solver.engine import SchedulingEngine
from app.services.demo_data import seed_demo_backlogs_if_empty

# In-memory job registry for optimization jobs
job_store: Dict[str, Dict[str, Any]] = {}

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    return job_store.get(job_id)

def start_optimization_job(
    mode: str = "full",
    time_limit_seconds: int = 30,
    version_name: Optional[str] = None,
    weights: Optional[Dict[str, int]] = None,
    base_version_id: Optional[int] = None,
    user: str = "Administrator"
) -> str:
    job_id = str(uuid.uuid4())
    job_store[job_id] = {
        "job_id": job_id,
        "status": "PENDING", # PENDING, RUNNING, COMPLETED, FAILED, INFEASIBLE
        "progress": 0,
        "created_at": time.time(),
        "started_at": None,
        "completed_at": None,
        "mode": mode,
        "result": None,
        "error": None
    }

    thread = threading.Thread(
        target=_run_optimization_worker,
        args=(job_id, mode, time_limit_seconds, version_name, weights, base_version_id, user),
        daemon=True
    )
    thread.start()
    return job_id

def _run_optimization_worker(
    job_id: str,
    mode: str,
    time_limit_seconds: int,
    version_name: Optional[str],
    weights: Optional[Dict[str, int]],
    base_version_id: Optional[int],
    user: str
):
    job = job_store.get(job_id)
    if not job:
        return

    job["status"] = "RUNNING"
    job["started_at"] = time.time()
    job["progress"] = 10

    db: Session = SessionLocal()
    try:
        # Load all exams, rooms, slots, enrollments, students
        exams = db.query(CourseExam).all()
        rooms = db.query(Room).all()
        slots = db.query(TimeSlot).all()
        students = db.query(Student).all()
        enrollments = db.query(StudentEnrollment).all()

        job["progress"] = 25

        exam_dicts = [
            {
                "id": e.id,
                "exam_code": e.exam_code,
                "course_code": e.course_code,
                "course_name": e.course_name,
                "department": e.department,
                "duration_minutes": e.duration_minutes,
                "required_features": e.required_features or [],
                "eligible_slot_ids": e.eligible_slot_ids or [],
                "preferred_slot_ids": e.preferred_slot_ids or [],
                "priority": e.priority,
                "is_locked": e.is_locked
            }
            for e in exams
        ]

        room_dicts = [
            {
                "id": r.id,
                "room_code": r.room_code,
                "name": r.name,
                "building": r.building,
                "capacity": r.capacity,
                "is_available": r.is_available,
                "features": r.features or [],
                "accessibility_features": r.accessibility_features or [],
                "blackout_intervals": r.blackout_intervals or []
            }
            for r in rooms
        ]

        slot_dicts = [
            {
                "id": s.id,
                "slot_code": s.slot_code,
                "date": s.date,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "duration_minutes": s.duration_minutes,
                "period": s.period,
                "is_available": s.is_available,
                "is_blackout": s.is_blackout,
                "blackout_reason": s.blackout_reason
            }
            for s in slots
        ]

        student_dict = {
            s.id: {"student_id": s.student_id, "name": s.name, "department": s.department}
            for s in students
        }

        enrollments_by_exam = {}
        for e in exams:
            enrollments_by_exam[e.id] = set()
        for en in enrollments:
            if en.exam_id in enrollments_by_exam:
                enrollments_by_exam[en.exam_id].add(en.student_id)

        job["progress"] = 40

        # Retrieve previous assignments and locked assignments
        locked_assignments = {}
        previous_assignments = []

        # Find active or base timetable version
        target_version = None
        if base_version_id:
            target_version = db.query(TimetableVersion).filter_by(id=base_version_id).first()
        if not target_version:
            target_version = db.query(TimetableVersion).filter_by(is_active=True).first()

        if target_version:
            prev_assignments_objs = db.query(TimetableAssignment).filter_by(timetable_id=target_version.id).all()
            for pa in prev_assignments_objs:
                previous_assignments.append({
                    "exam_id": pa.exam_id,
                    "timeslot_id": pa.timeslot_id,
                    "room_id": pa.room_id,
                    "is_locked": pa.is_locked
                })
                # If exam itself is locked or assignment is locked
                exam_obj = next((ex for ex in exams if ex.id == pa.exam_id), None)
                if (pa.is_locked or (exam_obj and exam_obj.is_locked)) and pa.timeslot_id and pa.room_id:
                    locked_assignments[pa.exam_id] = (pa.timeslot_id, pa.room_id)

        job["progress"] = 50

        # Run scheduler
        engine = SchedulingEngine(
            exams=exam_dicts,
            rooms=room_dicts,
            timeslots=slot_dicts,
            enrollments=enrollments_by_exam,
            students=student_dict,
            locked_assignments=locked_assignments,
            previous_assignments=previous_assignments,
            time_limit_seconds=time_limit_seconds,
            mode=mode,
            weights=weights
        )

        job["progress"] = 65
        solve_result = engine.solve()
        job["progress"] = 85

        # Check solver result
        if not solve_result.get("is_feasible"):
            job["status"] = "INFEASIBLE"
            job["result"] = solve_result
            job["completed_at"] = time.time()
            job["progress"] = 100
            return

        # Transactional update: Create a new version
        max_ver = db.query(TimetableVersion).order_by(TimetableVersion.version_number.desc()).first()
        next_ver_num = (max_ver.version_number + 1) if max_ver else 1

        ver_title = version_name or f"Optimized Schedule v{next_ver_num} ({'Minimal Change' if mode == 'minimal_change' else 'Full Optim'})"

        # Mark previous versions as inactive
        db.query(TimetableVersion).filter(TimetableVersion.is_active == True).update({"is_active": False})

        new_version = TimetableVersion(
            version_number=next_ver_num,
            name=ver_title,
            is_active=True,
            solver_status=solve_result["solver_status"],
            solver_runtime_ms=solve_result["solver_runtime_ms"],
            quality_score=solve_result["quality_score"],
            objective_cost=solve_result["objective_cost"],
            metrics=solve_result["metrics"],
            diagnostics=solve_result.get("diagnostics", []),
            created_by=user,
            notes=f"Generated via OR-Tools CP-SAT ({mode} mode) in {solve_result['solver_runtime_ms']}ms."
        )
        db.add(new_version)
        db.flush() # get new_version.id

        # Insert new assignments
        new_assignments_objs = []
        for a in solve_result["assignments"]:
            new_assignments_objs.append(TimetableAssignment(
                timetable_id=new_version.id,
                exam_id=a["exam_id"],
                timeslot_id=a["timeslot_id"],
                room_id=a["room_id"],
                assigned_student_count=a["assigned_student_count"],
                is_locked=a["is_locked"],
                source="AUTOMATIC",
                validation_status=a["validation_status"],
                conflict_reasons=a.get("conflict_reasons", [])
            ))
        db.bulk_save_objects(new_assignments_objs)

        # Audit log
        db.add(AuditLog(
            action="GENERATE" if mode == "full" else "REOPTIMIZE",
            entity_type="TIMETABLE",
            entity_id=str(new_version.id),
            user=user,
            details={
                "version_number": next_ver_num,
                "solver_status": solve_result["solver_status"],
                "quality_score": solve_result["quality_score"],
                "runtime_ms": solve_result["solver_runtime_ms"]
            }
        ))

        db.commit()
        seed_demo_backlogs_if_empty(db)


        job["status"] = "COMPLETED"
        job["progress"] = 100
        job["completed_at"] = time.time()
        job["result"] = {
            "version_id": new_version.id,
            "version_number": new_version.version_number,
            "name": new_version.name,
            "solver_status": new_version.solver_status,
            "solver_runtime_ms": new_version.solver_runtime_ms,
            "quality_score": new_version.quality_score,
            "objective_cost": new_version.objective_cost,
            "metrics": new_version.metrics
        }

    except Exception as exc:
        db.rollback()
        job["status"] = "FAILED"
        job["error"] = str(exc)
        job["completed_at"] = time.time()
    finally:
        db.close()
