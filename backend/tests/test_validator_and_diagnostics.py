import pytest
from app.solver.validator import TimetableValidator
from app.solver.diagnostics import SchedulingDiagnostics

def test_validator_detects_student_clash():
    exams = [
        {"id": 1, "exam_code": "CS101", "course_name": "CS", "duration_minutes": 60, "required_features": []},
        {"id": 2, "exam_code": "MA101", "course_name": "Math", "duration_minutes": 60, "required_features": []}
    ]
    rooms = [
        {"id": 1, "room_code": "R1", "capacity": 50, "is_available": True, "features": []},
        {"id": 2, "room_code": "R2", "capacity": 50, "is_available": True, "features": []}
    ]
    slots = [
        {"id": 1, "slot_code": "S1", "date": "2026-12-14", "start_time": "09:00:00", "duration_minutes": 120, "is_available": True, "is_blackout": False}
    ]
    enrollments = {1: {100}, 2: {100}} # Student 100 in both!
    assignments = [
        {"exam_id": 1, "timeslot_id": 1, "room_id": 1, "is_locked": False},
        {"exam_id": 2, "timeslot_id": 1, "room_id": 2, "is_locked": False} # Same slot 1!
    ]

    validator = TimetableValidator(exams, rooms, slots, enrollments, assignments)
    res = validator.validate()

    assert res.is_feasible is False
    assert any(v.rule == "H1" for v in res.violations)

def test_validator_detects_capacity_violation():
    exams = [{"id": 1, "exam_code": "CS101", "course_name": "CS", "duration_minutes": 60, "required_features": []}]
    rooms = [{"id": 1, "room_code": "TINY", "capacity": 10, "is_available": True, "features": []}]
    slots = [{"id": 1, "slot_code": "S1", "date": "2026-12-14", "start_time": "09:00:00", "duration_minutes": 120, "is_available": True, "is_blackout": False}]
    enrollments = {1: set(range(25))} # 25 students in 10 seat room
    assignments = [{"exam_id": 1, "timeslot_id": 1, "room_id": 1, "is_locked": False}]

    validator = TimetableValidator(exams, rooms, slots, enrollments, assignments)
    res = validator.validate()

    assert res.is_feasible is False
    assert any(v.rule == "H2" for v in res.violations)

def test_diagnostics_detects_locked_student_clash():
    exams = [
        {"id": 1, "exam_code": "EXAM-1", "duration_minutes": 60, "required_features": []},
        {"id": 2, "exam_code": "EXAM-2", "duration_minutes": 60, "required_features": []}
    ]
    rooms = [
        {"id": 1, "room_code": "R1", "capacity": 50, "is_available": True, "features": []},
        {"id": 2, "room_code": "R2", "capacity": 50, "is_available": True, "features": []}
    ]
    slots = [
        {"id": 1, "slot_code": "S1", "date": "2026-12-14", "start_time": "09:00:00", "duration_minutes": 120, "is_available": True, "is_blackout": False}
    ]
    enrollments = {1: {55}, 2: {55}}
    locked_map = {1: (1, 1), 2: (1, 2)} # Both locked to slot 1!

    diags = SchedulingDiagnostics(exams, rooms, slots, enrollments, locked_map).diagnose_all()
    assert len(diags) > 0
    assert any(d["type"] == "LOCKED_STUDENT_CLASH" for d in diags)
