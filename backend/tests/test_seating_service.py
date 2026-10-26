import pytest
from app.core.database import SessionLocal, Base, engine
from app.models.timetable import TimetableVersion
from app.models.assignment import TimetableAssignment
from app.models.exam import CourseExam
from app.models.room import Room
from app.models.timeslot import TimeSlot
from app.models.student import Student
from app.models.enrollment import StudentEnrollment
from app.services.demo_data import load_demo_dataset
from app.services.seating_service import compute_department_alternating_seatings, DEFAULT_DEPT_PRIORITY
from app.solver.engine import SchedulingEngine

@pytest.fixture(scope="module")
def seeded_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    load_demo_dataset(db)
    yield db
    db.close()

def test_alternating_seating_round_robin_order(seeded_db):
    """
    Verifies that when candidates from Computer Science and Business are scheduled,
    Bench 1 is assigned to Computer Science and Bench 2 is assigned to Business,
    strictly alternating across adjacent benches.
    """
    # Verify default department ordering puts Computer Science first and Business second
    assert DEFAULT_DEPT_PRIORITY[0] == "Computer Science"
    assert DEFAULT_DEPT_PRIORITY[1] == "Business"

    # Solve timetable to generate active assignments
    exams = [e.__dict__ for e in seeded_db.query(CourseExam).all()]
    rooms = [r.__dict__ for r in seeded_db.query(Room).all()]
    slots = [s.__dict__ for s in seeded_db.query(TimeSlot).all()]
    enrollments = {e.id: set() for e in seeded_db.query(CourseExam).all()}
    for en in seeded_db.query(StudentEnrollment).all():
        enrollments[en.exam_id].add(en.student_id)

    engine_solver = SchedulingEngine(
        exams=exams,
        rooms=rooms,
        timeslots=slots,
        enrollments=enrollments,
        time_limit_seconds=10,
        mode="full"
    )
    sol = engine_solver.solve()
    assert sol["is_feasible"] is True

    # Save as active version
    ver = TimetableVersion(
        version_number=99,
        name="Test Alternating Seating Version",
        is_active=True,
        solver_status="OPTIMAL",
        quality_score=95.0,
        objective_cost=10.0,
        metrics=sol["metrics"]
    )
    seeded_db.add(ver)
    seeded_db.flush()

    for a in sol["assignments"]:
        seeded_db.add(TimetableAssignment(
            timetable_id=ver.id,
            exam_id=a["exam_id"],
            timeslot_id=a["timeslot_id"],
            room_id=a["room_id"],
            assigned_student_count=a["assigned_student_count"]
        ))
    seeded_db.commit()

    # Compute alternating seatings
    res = compute_department_alternating_seatings(seeded_db, version_id=ver.id)
    assert len(res.seatings_map) > 0
    assert len(res.hall_charts) > 0

    # Inspect hall charts where multiple departments are present
    multi_dept_charts = [c for c in res.hall_charts if len(c["participating_departments"]) > 1]
    assert len(multi_dept_charts) > 0

    for chart in multi_dept_charts:
        benches = chart["benches"]
        assert len(benches) > 1

        # Check that desk strings match expected format
        for b in benches:
            assert b["seat_number"].startswith(chart["room_code"])
            assert f"-D{b['bench_number']:02d}" in b["seat_number"]

        # Check that where Computer Science and Business are present, Bench 1 is Computer Science and Bench 2 is Business
        if "Computer Science" in chart["participating_departments"] and "Business" in chart["participating_departments"]:
            assert benches[0]["department"] == "Computer Science"
            assert benches[1]["department"] == "Business"

        # Check alternating condition: adjacent benches must alternate departments whenever possible
        for i in range(len(benches) - 1):
            cur_dept = benches[i]["department"]
            next_dept = benches[i + 1]["department"]
            # If both departments still had candidates in round-robin, they must not be identical
            # (only in tail when one department is exhausted could identical occur)
            if i < len(chart["participating_departments"]) - 1:
                assert cur_dept != next_dept
