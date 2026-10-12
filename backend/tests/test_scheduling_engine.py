import pytest
from app.solver.engine import SchedulingEngine
from app.solver.validator import TimetableValidator
from app.solver.conflict_graph import ExamConflictGraph

def test_conflict_graph_clash_detection():
    exam_ids = [1, 2, 3]
    enrollments = {
        1: {101, 102},
        2: {102, 103}, # shares student 102 with exam 1
        3: {104, 105}  # disjoint
    }
    graph = ExamConflictGraph(exam_ids, enrollments)
    assert graph.has_conflict(1, 2) is True
    assert graph.has_conflict(1, 3) is False
    assert graph.get_shared_student_count(1, 2) == 1
    assert graph.get_shared_student_count(1, 3) == 0

def test_hard_constraint_student_clash_prevention():
    """H1: Two exams sharing students must NOT be placed in the same time slot."""
    exams = [
        {"id": 1, "exam_code": "EXAM-1", "duration_minutes": 60, "required_features": []},
        {"id": 2, "exam_code": "EXAM-2", "duration_minutes": 60, "required_features": []}
    ]
    rooms = [
        {"id": 1, "room_code": "R1", "capacity": 50, "is_available": True, "features": []},
        {"id": 2, "room_code": "R2", "capacity": 50, "is_available": True, "features": []}
    ]
    slots = [
        {"id": 1, "slot_code": "S1", "date": "2026-12-14", "start_time": "09:00:00", "duration_minutes": 120, "is_available": True, "is_blackout": False},
        {"id": 2, "slot_code": "S2", "date": "2026-12-14", "start_time": "13:00:00", "duration_minutes": 120, "is_available": True, "is_blackout": False}
    ]
    enrollments = {
        1: {10, 11},
        2: {11, 12} # student 11 in both
    }

    engine = SchedulingEngine(exams=exams, rooms=rooms, timeslots=slots, enrollments=enrollments, time_limit_seconds=5)
    sol = engine.solve()

    assert sol["is_feasible"] is True
    a1 = next(a for a in sol["assignments"] if a["exam_id"] == 1)
    a2 = next(a for a in sol["assignments"] if a["exam_id"] == 2)
    # Must be in different slots
    assert a1["timeslot_id"] != a2["timeslot_id"]

def test_hard_constraint_room_capacity_enforced():
    """H2: Room capacity must be >= enrolled student count."""
    exams = [
        {"id": 1, "exam_code": "EXAM-BIG", "duration_minutes": 60, "required_features": []}
    ]
    rooms = [
        {"id": 1, "room_code": "R-SMALL", "capacity": 10, "is_available": True, "features": []},
        {"id": 2, "room_code": "R-LARGE", "capacity": 100, "is_available": True, "features": []}
    ]
    slots = [
        {"id": 1, "slot_code": "S1", "date": "2026-12-14", "start_time": "09:00:00", "duration_minutes": 120, "is_available": True, "is_blackout": False}
    ]
    enrollments = {
        1: set(range(1, 41)) # 40 students
    }

    engine = SchedulingEngine(exams=exams, rooms=rooms, timeslots=slots, enrollments=enrollments, time_limit_seconds=5)
    sol = engine.solve()

    assert sol["is_feasible"] is True
    ass = sol["assignments"][0]
    # Must pick R-LARGE (id=2), never R-SMALL
    assert ass["room_id"] == 2

def test_hard_constraint_room_non_overlap():
    """H3: A room cannot host two exams at the same time slot."""
    exams = [
        {"id": 1, "exam_code": "EXAM-A", "duration_minutes": 60, "required_features": []},
        {"id": 2, "exam_code": "EXAM-B", "duration_minutes": 60, "required_features": []}
    ]
    # Only 1 room available!
    rooms = [
        {"id": 1, "room_code": "ONLY-ROOM", "capacity": 50, "is_available": True, "features": []}
    ]
    slots = [
        {"id": 1, "slot_code": "S1", "date": "2026-12-14", "start_time": "09:00:00", "duration_minutes": 120, "is_available": True, "is_blackout": False},
        {"id": 2, "slot_code": "S2", "date": "2026-12-14", "start_time": "13:00:00", "duration_minutes": 120, "is_available": True, "is_blackout": False}
    ]
    enrollments = {1: {1}, 2: {2}} # disjoint students

    engine = SchedulingEngine(exams=exams, rooms=rooms, timeslots=slots, enrollments=enrollments, time_limit_seconds=5)
    sol = engine.solve()

    assert sol["is_feasible"] is True
    a1 = next(a for a in sol["assignments"] if a["exam_id"] == 1)
    a2 = next(a for a in sol["assignments"] if a["exam_id"] == 2)
    # Since only 1 room, they must be in different slots
    assert a1["timeslot_id"] != a2["timeslot_id"]

def test_hard_constraint_locked_exam_preserved():
    """H6: Locked assignments must be preserved."""
    exams = [
        {"id": 1, "exam_code": "EXAM-LOCKED", "duration_minutes": 60, "required_features": [], "is_locked": True},
        {"id": 2, "exam_code": "EXAM-FREE", "duration_minutes": 60, "required_features": [], "is_locked": False}
    ]
    rooms = [
        {"id": 1, "room_code": "R1", "capacity": 50, "is_available": True, "features": []},
        {"id": 2, "room_code": "R2", "capacity": 50, "is_available": True, "features": []}
    ]
    slots = [
        {"id": 1, "slot_code": "S1", "date": "2026-12-14", "start_time": "09:00:00", "duration_minutes": 120, "is_available": True, "is_blackout": False},
        {"id": 2, "slot_code": "S2", "date": "2026-12-14", "start_time": "13:00:00", "duration_minutes": 120, "is_available": True, "is_blackout": False}
    ]
    enrollments = {1: {1}, 2: {2}}
    locked_map = {1: (2, 2)} # Exam 1 locked strictly to Slot 2, Room 2

    engine = SchedulingEngine(exams=exams, rooms=rooms, timeslots=slots, enrollments=enrollments, locked_assignments=locked_map, time_limit_seconds=5)
    sol = engine.solve()

    assert sol["is_feasible"] is True
    a1 = next(a for a in sol["assignments"] if a["exam_id"] == 1)
    assert a1["timeslot_id"] == 2
    assert a1["room_id"] == 2

def test_hard_constraint_required_room_features():
    """H7: Room suitability: Exam requiring 'Computers' must get a room with 'Computers'."""
    exams = [
        {"id": 1, "exam_code": "EXAM-LAB", "duration_minutes": 60, "required_features": ["Computers"]}
    ]
    rooms = [
        {"id": 1, "room_code": "R-STANDARD", "capacity": 50, "is_available": True, "features": ["Projector"]},
        {"id": 2, "room_code": "R-COMPUTERS", "capacity": 50, "is_available": True, "features": ["Computers", "Projector"]}
    ]
    slots = [
        {"id": 1, "slot_code": "S1", "date": "2026-12-14", "start_time": "09:00:00", "duration_minutes": 120, "is_available": True, "is_blackout": False}
    ]
    enrollments = {1: {1}}

    engine = SchedulingEngine(exams=exams, rooms=rooms, timeslots=slots, enrollments=enrollments, time_limit_seconds=5)
    sol = engine.solve()

    assert sol["is_feasible"] is True
    assert sol["assignments"][0]["room_id"] == 2
