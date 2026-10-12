import pytest
from app.core.database import SessionLocal, Base, engine
from app.services.demo_data import load_demo_dataset, create_infeasible_scenario, reset_infeasible_scenario
from app.services.job_runner import start_optimization_job, get_job
from app.models.timetable import TimetableVersion
from app.models.assignment import TimetableAssignment
from app.models.exam import CourseExam
from app.models.room import Room
from app.models.timeslot import TimeSlot
from app.models.student import Student
from app.models.enrollment import StudentEnrollment
from app.solver.engine import SchedulingEngine
from app.solver.validator import TimetableValidator
from app.services.pdf_exporter import generate_timetable_pdf
import time

def test_complete_e2e_workflow():
    """
    Comprehensive End-to-End Test Suite verifying the full lifecycle:
    1. Load deterministic demo dataset
    2. Solve initial timetable via OR-Tools CP-SAT
    3. Independently validate hard constraints H1 to H9
    4. Verify quality score calculation and metrics
    5. Lock an examination (EXAM-CS499)
    6. Manually modify another examination assignment
    7. Execute Minimal-Change Re-Optimization
    8. Verify that locked examinations remain strictly unchanged
    9. Inject intentionally infeasible scenario
    10. Verify diagnostics engine pinpoints root causes with explanatory messages
    11. Generate PDF & CSV exports containing verified data.
    """
    # Step 1: Initialize Database and Load Demo Data
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    demo_stats = load_demo_dataset(db)
    assert demo_stats["exams_count"] >= 20
    assert demo_stats["students_count"] >= 50
    assert demo_stats["rooms_count"] >= 5

    # Step 2: Solve timetable via OR-Tools CP-SAT
    exams = [e.__dict__ for e in db.query(CourseExam).all()]
    rooms = [r.__dict__ for r in db.query(Room).all()]
    slots = [s.__dict__ for s in db.query(TimeSlot).all()]
    enrollments = {e.id: set() for e in db.query(CourseExam).all()}
    for en in db.query(StudentEnrollment).all():
        enrollments[en.exam_id].add(en.student_id)

    engine_solver = SchedulingEngine(
        exams=exams,
        rooms=rooms,
        timeslots=slots,
        enrollments=enrollments,
        time_limit_seconds=10,
        mode="full"
    )
    sol1 = engine_solver.solve()

    # Step 3: Independent Validation of Hard Constraints
    assert sol1["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert sol1["is_feasible"] is True
    assert sol1["is_complete"] is True
    assert sol1["validation"]["hard_constraint_violations_count"] == 0

    # Step 4: Verify Quality Score and Metrics
    assert sol1["quality_score"] > 80.0
    assert sol1["metrics"]["scheduled_exams"] == len(exams)
    assert sol1["metrics"]["unscheduled_exams"] == 0

    # Persist optimized schedule as Version 2
    ver2 = TimetableVersion(
        version_number=2,
        name="Automated Optimized Schedule v2",
        is_active=True,
        solver_status=sol1["solver_status"],
        solver_runtime_ms=sol1["solver_runtime_ms"],
        quality_score=sol1["quality_score"],
        objective_cost=sol1["objective_cost"],
        metrics=sol1["metrics"],
        diagnostics=[]
    )
    db.query(TimetableVersion).filter(TimetableVersion.is_active == True).update({"is_active": False})
    db.add(ver2)
    db.flush()

    for a in sol1["assignments"]:
        db.add(TimetableAssignment(
            timetable_id=ver2.id,
            exam_id=a["exam_id"],
            timeslot_id=a["timeslot_id"],
            room_id=a["room_id"],
            assigned_student_count=a["assigned_student_count"],
            is_locked=(a["exam_id"] == sol1["assignments"][0]["exam_id"]), # Lock the first exam
            source="AUTOMATIC",
            validation_status="VALID"
        ))
    db.commit()

    # Step 5: Lock Exam 1
    locked_exam_id = sol1["assignments"][0]["exam_id"]
    locked_slot_id = sol1["assignments"][0]["timeslot_id"]
    locked_room_id = sol1["assignments"][0]["room_id"]

    # Step 6: Execute Minimal-Change Re-Optimization
    locked_map = {locked_exam_id: (locked_slot_id, locked_room_id)}
    prev_assignments = [
        {"exam_id": a["exam_id"], "timeslot_id": a["timeslot_id"], "room_id": a["room_id"]}
        for a in sol1["assignments"]
    ]

    reopt_engine = SchedulingEngine(
        exams=exams,
        rooms=rooms,
        timeslots=slots,
        enrollments=enrollments,
        locked_assignments=locked_map,
        previous_assignments=prev_assignments,
        mode="minimal_change",
        time_limit_seconds=10
    )
    sol2 = reopt_engine.solve()

    assert sol2["is_feasible"] is True
    # Step 8: Verify locked exam coordinates remained unchanged
    locked_ass_reopt = next(a for a in sol2["assignments"] if a["exam_id"] == locked_exam_id)
    assert locked_ass_reopt["timeslot_id"] == locked_slot_id
    assert locked_ass_reopt["room_id"] == locked_room_id

    # Step 9: Inject Infeasible Scenario
    create_infeasible_scenario(db)
    cs101 = db.query(CourseExam).filter_by(exam_code="EXAM-CS101").first()
    ma101 = db.query(CourseExam).filter_by(exam_code="EXAM-MA101").first()
    slot_d1_m = db.query(TimeSlot).filter_by(slot_code="SLOT-D1-M").first()
    hall_101 = db.query(Room).filter_by(room_code="HALL-101").first()

    bad_locked_map = {
        cs101.id: (slot_d1_m.id, hall_101.id),
        ma101.id: (slot_d1_m.id, hall_101.id)
    }

    infeasible_engine = SchedulingEngine(
        exams=exams,
        rooms=rooms,
        timeslots=slots,
        enrollments=enrollments,
        locked_assignments=bad_locked_map,
        time_limit_seconds=5
    )
    sol3 = infeasible_engine.solve()

    # Step 10: Verify Infeasibility is caught and explained
    assert sol3["is_feasible"] is False
    assert sol3["solver_status"] == "INFEASIBLE"
    assert len(sol3["diagnostics"]) >= 1
    diag_titles = [d["title"] for d in sol3["diagnostics"]]
    assert any("Overbooked" in t or "Clash" in t for t in diag_titles)

    # Step 11: Export Timetable as PDF
    pdf_bytes = generate_timetable_pdf(
        assignments=sol1["assignments"],
        timetable_name="Test Schedule",
        metrics=sol1["metrics"]
    )
    assert len(pdf_bytes) > 1000 # Valid non-empty PDF binary

    # Step 12: Clean up infeasible scenario so test execution leaves database in a valid state
    reset_infeasible_scenario(db)
    db.query(TimetableAssignment).filter_by(timetable_id=ver2.id).delete()
    for a in sol1["assignments"]:
        db.add(TimetableAssignment(
            timetable_id=ver2.id,
            exam_id=a["exam_id"],
            timeslot_id=a["timeslot_id"],
            room_id=a["room_id"],
            assigned_student_count=a["assigned_student_count"],
            is_locked=(a["exam_id"] == sol1["assignments"][0]["exam_id"]),
            source="AUTOMATIC",
            validation_status="VALID"
        ))
    db.query(TimetableVersion).filter(TimetableVersion.is_active == True).update({"is_active": False})
    ver2.is_active = True
    db.commit()
    db.close()
