import sys
from collections import defaultdict
from app.core.database import SessionLocal
from app.models.room import Room
from app.models.timeslot import TimeSlot
from app.models.exam import CourseExam
from app.models.student import Student
from app.models.enrollment import StudentEnrollment
from app.solver.engine import SchedulingEngine
from app.solver.validator import TimetableValidator
from app.solver.metrics import QualityMetricsCalculator
from app.services.seating_service import compute_department_alternating_seatings

def test_alternating_enrollments():
    db = SessionLocal()
    rooms_db = db.query(Room).all()
    slots_db = db.query(TimeSlot).all()
    exams_db = db.query(CourseExam).all()
    students_db = db.query(Student).all()

    rooms = [
        {
            'id': r.id, 'room_code': r.room_code, 'name': r.name,
            'capacity': r.capacity, 'is_available': r.is_available,
            'features': r.features or [], 'blackout_intervals': r.blackout_intervals or []
        }
        for r in rooms_db
    ]
    slots = [
        {
            'id': s.id, 'slot_code': s.slot_code, 'date': s.date,
            'start_time': s.start_time, 'end_time': s.end_time,
            'duration_minutes': s.duration_minutes, 'period': s.period,
            'is_available': s.is_available, 'is_blackout': s.is_blackout
        }
        for s in slots_db
    ]
    exams = [
        {
            'id': e.id, 'exam_code': e.exam_code, 'course_code': e.course_code,
            'course_name': e.course_name, 'department': e.department,
            'duration_minutes': e.duration_minutes, 'priority': e.priority,
            'is_locked': e.is_locked, 'required_features': e.required_features or []
        }
        for e in exams_db
    ]

    exam_by_code = {e['exam_code']: e for e in exams}

    # Group students by department
    students_by_dept = defaultdict(list)
    for st in students_db:
        students_by_dept[st.department].append(st)

    for dept, s_list in students_by_dept.items():
        print(f"Dept {dept}: {len(s_list)} students")

    # Let's design 3-4 exams per student
    # Each dept has 12 students. Let's divide each dept into 2 cohorts of 6 students:
    # Cohort 1: students 0..5
    # Cohort 2: students 6..11
    #
    # We have 22 exams. Let's specify for each exam which (dept, cohort) takes it:
    # Notice: Each exam gets 2 cohorts from 2 different departments! (6 + 6 = 12 students)
    # 12 students fits into SEM-A (capacity 25), ROOM-305 (35), LAB-COMP (40), etc.
    # Every exam has students from exactly 2 departments!
    
    exam_pairings = {
        # CS exams
        "EXAM-CS101": [("Computer Science", 0), ("Mathematics", 0)],
        "EXAM-CS201": [("Computer Science", 0), ("Business", 0)],
        "EXAM-CS301": [("Computer Science", 1), ("Electrical Eng", 0)],
        "EXAM-CS350": [("Computer Science", 1), ("Business", 1)],
        "EXAM-CS420": [("Computer Science", 1), ("Mathematics", 1)], # Practical
        "EXAM-CS499": [("Computer Science", 0), ("Electrical Eng", 1)], # Capstone, locked AUD-MAIN
        
        # Math exams
        "EXAM-MA101": [("Mathematics", 0), ("Physics", 0)],
        "EXAM-MA201": [("Mathematics", 0), ("Physics", 1)],
        "EXAM-MA204": [("Mathematics", 1), ("Computer Science", 0)],
        "EXAM-MA310": [("Mathematics", 1), ("Business", 0)],
        
        # Physics exams
        "EXAM-PHY101": [("Physics", 0), ("Mathematics", 1)],
        "EXAM-PHY202": [("Physics", 0), ("Electrical Eng", 0)],
        "EXAM-PHY305": [("Physics", 1), ("Electrical Eng", 1)],
        
        # EE exams
        "EXAM-EE101": [("Electrical Eng", 0), ("Physics", 0)],
        "EXAM-EE210": [("Electrical Eng", 0), ("Computer Science", 1)], # Practical
        "EXAM-EE320": [("Electrical Eng", 1), ("Mathematics", 0)],
        
        # Business exams
        "EXAM-BUS101": [("Business", 0), ("Physics", 1)],
        "EXAM-BUS205": [("Business", 0), ("Electrical Eng", 1)],
        "EXAM-BUS310": [("Business", 1), ("Physics", 0)],
        "EXAM-BUS401": [("Business", 1), ("Computer Science", 0)], # Practical
        
        # Humanities exams
        "EXAM-HUM102": [("Computer Science", 1), ("Business", 1)],
        "EXAM-ENG201": [("Electrical Eng", 1), ("Mathematics", 1)],
    }

    enrollments = defaultdict(set) # exam_id -> set of student_ids
    student_exams = defaultdict(list) # student_id -> list of exam_codes

    for ex_code, pairs in exam_pairings.items():
        ex = exam_by_code[ex_code]
        for dept, cohort_idx in pairs:
            dept_students = students_by_dept[dept]
            if cohort_idx == 0:
                selected_students = dept_students[:6]
            else:
                selected_students = dept_students[6:]
            for st in selected_students:
                enrollments[ex['id']].add(st.id)
                student_exams[st.id].append(ex_code)

    print("\nEnrollment counts per exam:")
    for ex_code in exam_pairings:
        ex = exam_by_code[ex_code]
        cnt = len(enrollments[ex['id']])
        depts_in_exam = {st.department for st in students_db if st.id in enrollments[ex['id']]}
        print(f"  {ex_code}: {cnt} students, depts: {depts_in_exam}")

    print("\nExams per student distribution:")
    exam_counts = [len(exams_list) for exams_list in student_exams.values()]
    print(f"  Min exams: {min(exam_counts)}, Max exams: {max(exam_counts)}, Avg: {sum(exam_counts)/len(exam_counts):.2f}")

    # Check locked assignment
    capstone = exam_by_code["EXAM-CS499"]
    slot_d1_m = next(s for s in slots if s['slot_code'] == "SLOT-D1-M")
    aud_room = next(r for r in rooms if r['room_code'] == "AUD-MAIN")
    locked = {capstone['id']: (slot_d1_m['id'], aud_room['id'])}

    # Run solver
    print("\nRunning SchedulingEngine...")
    engine = SchedulingEngine(
        exams=exams,
        rooms=rooms,
        timeslots=slots,
        enrollments=enrollments,
        locked_assignments=locked,
        time_limit_seconds=15
    )
    result = engine.solve()
    print("Solver status:", result.get("solver_status"))
    print("Is feasible:", result.get("is_feasible"))
    print("Is complete:", result.get("is_complete"))
    print("Quality score:", result.get("quality_score"))
    print("Scheduled count:", len(result.get("assignments", [])))

    if not result.get("is_feasible"):
        print("Diagnostics:", result.get("diagnostics"))
        print("Violations:", result.get("validation", {}).get("violations"))
        return False

    validator = TimetableValidator(
        exams=exams,
        rooms=rooms,
        timeslots=slots,
        enrollments=enrollments,
        assignments=result.get("assignments", []),
        locked_assignments=locked
    )
    val_res = validator.validate()
    print("Validation hard violations:", len(val_res.violations))
    for v in val_res.violations:
        print("  Violation:", v.rule, v.title, v.description)

    return True

if __name__ == "__main__":
    test_alternating_enrollments()
