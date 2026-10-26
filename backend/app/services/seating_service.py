from typing import List, Dict, Tuple, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.timetable import TimetableVersion
from app.models.assignment import TimetableAssignment
from app.models.student import Student
from app.models.enrollment import StudentEnrollment
from app.models.exam import CourseExam
from app.models.room import Room
from app.models.timeslot import TimeSlot

# Standard university department ordering for alternating seat distribution
DEFAULT_DEPT_PRIORITY = [
    "Computer Science",
    "Business",
    "Mathematics",
    "Physics",
    "Electrical Eng",
    "Humanities"
]

class SeatingAssignmentResult:
    def __init__(
        self,
        seatings_map: Dict[Tuple[int, int], Dict[str, Any]],
        hall_charts: List[Dict[str, Any]]
    ):
        self.seatings_map = seatings_map
        self.hall_charts = hall_charts


def compute_department_alternating_seatings(
    db: Session,
    version_id: Optional[int] = None
) -> SeatingAssignmentResult:
    """
    Computes deterministic, department-wise alternating desk numbers for students
    across all examination hall sessions.

    Principle (Anti-Cheating & Exam Integrity):
    - For each exam hall / room session (at a given date & time slot):
      Candidates are partitioned by academic department (e.g. Computer Science, Business, Mathematics, etc.).
    - Candidates within each department are sorted deterministically by Student ID.
    - Desks/Benches are allocated in round-robin alternating fashion across departments:
        Bench 1 (D01): Computer Science
        Bench 2 (D02): Business
        Bench 3 (D03): Mathematics (or Computer Science)
        Bench 4 (D04): Business
        ...
      This guarantees that candidates sitting at adjacent benches do not belong to the same
      department whenever multiple departments are scheduled in the session.
    """
    if version_id:
        ver = db.query(TimetableVersion).filter_by(id=version_id).first()
    else:
        ver = db.query(TimetableVersion).filter_by(is_active=True).first()

    if not ver:
        return SeatingAssignmentResult(seatings_map={}, hall_charts=[])

    # If timetable is pre-optimization / draft, seatings are cleared
    is_pre_opt = (
        ver.solver_status in ("PRE_OPTIMIZATION", "DRAFT", "PENDING")
        or (ver.quality_score == 0.0)
        or "pre-optimization" in (ver.name or "").lower()
        or (ver.metrics and ver.metrics.get("is_optimized") is False)
    )
    if is_pre_opt:
        return SeatingAssignmentResult(seatings_map={}, hall_charts=[])

    assignments = db.query(TimetableAssignment).filter_by(timetable_id=ver.id).all()
    all_students = db.query(Student).all()
    students_by_id = {s.id: s for s in all_students}

    all_enrollments = db.query(StudentEnrollment).all()
    exam_students_map: Dict[int, List[int]] = {}
    for en in all_enrollments:
        exam_students_map.setdefault(en.exam_id, []).append(en.student_id)

    # Group assignments by session: (timeslot_id, room_id)
    session_assignments: Dict[Tuple[int, int], List[TimetableAssignment]] = {}
    assigned_exam_ids = set()

    for a in assignments:
        if a.timeslot_id and a.room_id and a.timeslot and a.room:
            session_key = (a.timeslot_id, a.room_id)
            session_assignments.setdefault(session_key, []).append(a)
            assigned_exam_ids.add(a.exam_id)

    seatings_map: Dict[Tuple[int, int], Dict[str, Any]] = {}
    hall_charts: List[Dict[str, Any]] = []

    # Sort sessions chronologically by date and start_time, then room_code
    sorted_sessions = sorted(
        session_assignments.items(),
        key=lambda item: (
            str(item[1][0].timeslot.date),
            str(item[1][0].timeslot.start_time),
            item[1][0].room.room_code
        )
    )

    for (slot_id, room_id), ass_list in sorted_sessions:
        slot = ass_list[0].timeslot
        room = ass_list[0].room

        date_str = str(slot.date)
        try:
            date_dt = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = date_dt.strftime("%A")
        except Exception:
            day_name = "Exam Day"

        # 1. Collect all candidates taking an exam in this room during this timeslot
        # Each item: (student_obj, exam_obj, assignment_obj)
        session_candidates: List[Tuple[Student, CourseExam, TimetableAssignment]] = []
        seen_candidates_in_session = set()

        for a in ass_list:
            exam = a.exam
            if not exam:
                continue
            enrolled_sids = exam_students_map.get(exam.id, [])
            for sid in enrolled_sids:
                if sid in seen_candidates_in_session:
                    continue
                st = students_by_id.get(sid)
                if st:
                    session_candidates.append((st, exam, a))
                    seen_candidates_in_session.add(sid)

        # 2. Group candidates by department
        dept_groups: Dict[str, List[Tuple[Student, CourseExam, TimetableAssignment]]] = {}
        for st, ex, a in session_candidates:
            dept_groups.setdefault(st.department, []).append((st, ex, a))

        # Sort candidates within each department by student_id deterministically
        for dept in dept_groups:
            dept_groups[dept].sort(key=lambda item: (item[0].student_id, item[0].id))

        # 3. Order departments: Preferred priority first, then remaining alphabetically
        ordered_depts = [d for d in DEFAULT_DEPT_PRIORITY if d in dept_groups]
        for d in sorted(dept_groups.keys()):
            if d not in ordered_depts:
                ordered_depts.append(d)

        # 4. Interleave candidates across departments in round-robin fashion
        # Bench 1: Dept 1 (e.g. Computer Science)
        # Bench 2: Dept 2 (e.g. Business)
        # Bench 3: Dept 3 (or Computer Science)
        # Bench 4: Dept 4 (or Business)
        # ...
        dept_queues = {d: list(dept_groups[d]) for d in ordered_depts}
        benches: List[Dict[str, Any]] = []
        bench_idx = 1

        while any(dept_queues.values()):
            for dept in ordered_depts:
                if dept_queues[dept]:
                    st, ex, a = dept_queues[dept].pop(0)
                    seat_str = f"{room.room_code}-D{bench_idx:02d}"

                    seat_info = {
                        "seat_number": seat_str,
                        "bench_number": bench_idx,
                        "room_code": room.room_code,
                        "room_name": room.name,
                        "building": room.building,
                        "room_capacity": room.capacity,
                        "timeslot_id": slot.id,
                        "slot_code": slot.slot_code,
                        "date": date_str,
                        "day_name": day_name,
                        "start_time": str(slot.start_time),
                        "end_time": str(slot.end_time),
                        "period": slot.period or "",
                        "is_locked": a.is_locked,
                        "exam_id": ex.id,
                        "exam_code": ex.exam_code,
                        "course_code": ex.course_code,
                        "course_name": ex.course_name,
                        "student_id": st.student_id,
                        "student_name": st.name,
                        "department": st.department,
                        "semester": st.semester
                    }

                    seatings_map[(st.id, ex.id)] = seat_info

                    benches.append({
                        "bench_number": bench_idx,
                        "seat_number": seat_str,
                        "student_id": st.student_id,
                        "student_name": st.name,
                        "department": st.department,
                        "semester": st.semester,
                        "course_code": ex.course_code,
                        "course_name": ex.course_name,
                        "exam_code": ex.exam_code,
                        "special_accommodations": st.special_accommodations or []
                    })

                    bench_idx += 1

        hall_charts.append({
            "session_key": f"{slot.slot_code}_{room.room_code}",
            "timeslot_id": slot.id,
            "slot_code": slot.slot_code,
            "date": date_str,
            "day_name": day_name,
            "start_time": str(slot.start_time),
            "end_time": str(slot.end_time),
            "period": slot.period or "",
            "room_id": room.id,
            "room_code": room.room_code,
            "room_name": room.name,
            "building": room.building,
            "room_capacity": room.capacity,
            "total_assigned": len(benches),
            "participating_departments": ordered_depts,
            "is_alternating": len(ordered_depts) > 1,
            "benches": benches
        })

    # 5. Handle any exams not assigned to a room/slot (fallback)
    all_exams = db.query(CourseExam).all()
    for ex in all_exams:
        if ex.id not in assigned_exam_ids:
            enrolled_sids = exam_students_map.get(ex.id, [])
            if not enrolled_sids:
                continue
            dept_groups = {}
            for sid in enrolled_sids:
                st = students_by_id.get(sid)
                if st:
                    dept_groups.setdefault(st.department, []).append(st)
            for d in dept_groups:
                dept_groups[d].sort(key=lambda s: (s.student_id, s.id))
            ordered_depts = [d for d in DEFAULT_DEPT_PRIORITY if d in dept_groups] + [d for d in sorted(dept_groups.keys()) if d not in DEFAULT_DEPT_PRIORITY]
            dept_queues = {d: list(dept_groups[d]) for d in ordered_depts}
            b_idx = 1
            while any(dept_queues.values()):
                for d in ordered_depts:
                    if dept_queues[d]:
                        st = dept_queues[d].pop(0)
                        seat_str = f"ROOM-D{b_idx:02d}"
                        seatings_map[(st.id, ex.id)] = {
                            "seat_number": seat_str,
                            "bench_number": b_idx,
                            "room_code": "UNASSIGNED",
                            "room_name": "TBD",
                            "building": "Campus",
                            "room_capacity": 50,
                            "timeslot_id": 0,
                            "slot_code": "TBD",
                            "date": "TBD",
                            "day_name": "TBD",
                            "start_time": "09:00:00",
                            "end_time": "12:00:00",
                            "period": "Morning",
                            "is_locked": False,
                            "exam_id": ex.id,
                            "exam_code": ex.exam_code,
                            "course_code": ex.course_code,
                            "course_name": ex.course_name,
                            "student_id": st.student_id,
                            "student_name": st.name,
                            "department": st.department,
                            "semester": st.semester
                        }
                        b_idx += 1

    return SeatingAssignmentResult(seatings_map=seatings_map, hall_charts=hall_charts)
