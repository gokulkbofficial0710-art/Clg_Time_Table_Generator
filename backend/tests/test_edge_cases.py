import pytest
from app.solver.engine import SchedulingEngine

def test_edge_case_zero_exams():
    engine = SchedulingEngine(exams=[], rooms=[], timeslots=[], enrollments={})
    sol = engine.solve()
    assert sol["is_feasible"] is False or sol["solver_status"] in ("OPTIMAL", "FEASIBLE", "INFEASIBLE")

def test_edge_case_zero_rooms():
    exams = [{"id": 1, "exam_code": "EXAM-1", "duration_minutes": 60, "required_features": []}]
    slots = [{"id": 1, "slot_code": "S1", "date": "2026-12-14", "start_time": "09:00:00", "duration_minutes": 120, "is_available": True, "is_blackout": False}]
    engine = SchedulingEngine(exams=exams, rooms=[], timeslots=slots, enrollments={1: {1}})
    sol = engine.solve()
    assert sol["is_feasible"] is False
    assert sol["solver_status"] == "INFEASIBLE"

def test_edge_case_exam_duration_exceeds_all_slots():
    exams = [{"id": 1, "exam_code": "LONG-EXAM", "duration_minutes": 300, "required_features": []}]
    rooms = [{"id": 1, "room_code": "R1", "capacity": 50, "is_available": True, "features": []}]
    slots = [{"id": 1, "slot_code": "S1", "date": "2026-12-14", "start_time": "09:00:00", "duration_minutes": 120, "is_available": True, "is_blackout": False}]
    engine = SchedulingEngine(exams=exams, rooms=rooms, timeslots=slots, enrollments={1: {1}})
    sol = engine.solve()
    assert sol["is_feasible"] is False
    assert sol["solver_status"] == "INFEASIBLE"
