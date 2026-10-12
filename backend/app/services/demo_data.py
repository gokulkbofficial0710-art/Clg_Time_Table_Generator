from datetime import date, time, datetime, timezone
from sqlalchemy.orm import Session
from app.models.room import Room
from app.models.timeslot import TimeSlot
from app.models.student import Student
from app.models.enrollment import StudentEnrollment
from app.models.exam import CourseExam
from app.models.timetable import TimetableVersion
from app.models.assignment import TimetableAssignment
from app.models.audit import AuditLog
from app.models.backlog import BacklogRecord
from app.solver.engine import SchedulingEngine

def load_demo_dataset(db: Session, include_infeasible: bool = False) -> dict:
    """
    Populates database with deterministic realistic university exam dataset:
    - 5 Departments (Computer Science, Mathematics, Physics, Electrical Eng, Business)
    - 22 Examinations with diverse durations and requirements
    - 60 Students with overlapping course enrollments
    - 6 Rooms of varying capacities and features
    - 10 Time slots across 4 examination dates
    - 1 Locked examination
    - Room blackout maintenance window
    - If include_infeasible is True: creates an impossible clash to demonstrate diagnostics.
    """
    # Clear existing data safely
    db.query(BacklogRecord).delete()
    db.query(TimetableAssignment).delete()
    db.query(TimetableVersion).delete()
    db.query(StudentEnrollment).delete()
    db.query(Student).delete()
    db.query(CourseExam).delete()
    db.query(Room).delete()
    db.query(TimeSlot).delete()
    db.commit()

    # 1. Rooms
    rooms_data = [
        {
            "room_code": "AUD-MAIN",
            "name": "Grand University Auditorium",
            "building": "Central Hall",
            "capacity": 150,
            "is_available": True,
            "features": ["Projector", "Wheelchair Access", "Sound System"],
            "accessibility_features": ["Wheelchair Access", "Elevator Nearby"],
            "blackout_intervals": []
        },
        {
            "room_code": "HALL-101",
            "name": "Science Lecture Hall A",
            "building": "Science Complex",
            "capacity": 75,
            "is_available": True,
            "features": ["Projector", "Tiered Seating", "Wheelchair Access"],
            "accessibility_features": ["Wheelchair Access"],
            "blackout_intervals": []
        },
        {
            "room_code": "LAB-COMP",
            "name": "Advanced Computing Laboratory",
            "building": "Turing Engineering Building",
            "capacity": 40,
            "is_available": True,
            "features": ["Computers", "Projector", "High Speed Network"],
            "accessibility_features": ["Elevator Nearby"],
            "blackout_intervals": []
        },
        {
            "room_code": "ROOM-202",
            "name": "Classroom 202",
            "building": "Humanities & Arts",
            "capacity": 45,
            "is_available": True,
            "features": ["Whiteboard", "Projector"],
            "accessibility_features": [],
            "blackout_intervals": [
                {"date": "2026-12-16", "reason": "HVAC Air Filter Replacement"}
            ]
        },
        {
            "room_code": "ROOM-305",
            "name": "Classroom 305",
            "building": "Science Complex",
            "capacity": 35,
            "is_available": True,
            "features": ["Whiteboard", "Wheelchair Access"],
            "accessibility_features": ["Wheelchair Access"],
            "blackout_intervals": []
        },
        {
            "room_code": "SEM-A",
            "name": "Executive Seminar Room",
            "building": "Business School",
            "capacity": 25,
            "is_available": True,
            "features": ["Conference Screen", "Wheelchair Access"],
            "accessibility_features": ["Wheelchair Access"],
            "blackout_intervals": []
        }
    ]

    created_rooms = []
    for r in rooms_data:
        room_obj = Room(**r)
        db.add(room_obj)
        created_rooms.append(room_obj)
    db.commit()

    # 2. Time Slots (10 slots across 4 exam days)
    # Day 1: 2026-12-14
    # Day 2: 2026-12-15
    # Day 3: 2026-12-16
    # Day 4: 2026-12-17
    slots_data = [
        # Day 1
        {"slot_code": "SLOT-D1-M", "date": date(2026, 12, 14), "start_time": time(9, 0), "end_time": time(12, 0), "duration_minutes": 180, "period": "Morning", "is_available": True, "is_blackout": False},
        {"slot_code": "SLOT-D1-A", "date": date(2026, 12, 14), "start_time": time(13, 0), "end_time": time(16, 0), "duration_minutes": 180, "period": "Afternoon", "is_available": True, "is_blackout": False},
        {"slot_code": "SLOT-D1-E", "date": date(2026, 12, 14), "start_time": time(17, 0), "end_time": time(19, 30), "duration_minutes": 150, "period": "Evening", "is_available": True, "is_blackout": False},
        # Day 2
        {"slot_code": "SLOT-D2-M", "date": date(2026, 12, 15), "start_time": time(9, 0), "end_time": time(12, 0), "duration_minutes": 180, "period": "Morning", "is_available": True, "is_blackout": False},
        {"slot_code": "SLOT-D2-A", "date": date(2026, 12, 15), "start_time": time(13, 0), "end_time": time(16, 0), "duration_minutes": 180, "period": "Afternoon", "is_available": True, "is_blackout": False},
        {"slot_code": "SLOT-D2-E", "date": date(2026, 12, 15), "start_time": time(17, 0), "end_time": time(19, 30), "duration_minutes": 150, "period": "Evening", "is_available": True, "is_blackout": False},
        # Day 3
        {"slot_code": "SLOT-D3-M", "date": date(2026, 12, 16), "start_time": time(9, 0), "end_time": time(12, 0), "duration_minutes": 180, "period": "Morning", "is_available": True, "is_blackout": False},
        {"slot_code": "SLOT-D3-A", "date": date(2026, 12, 16), "start_time": time(13, 0), "end_time": time(16, 0), "duration_minutes": 180, "period": "Afternoon", "is_available": True, "is_blackout": False},
        # Day 4
        {"slot_code": "SLOT-D4-M", "date": date(2026, 12, 17), "start_time": time(9, 0), "end_time": time(12, 0), "duration_minutes": 180, "period": "Morning", "is_available": True, "is_blackout": False},
        {"slot_code": "SLOT-D4-A", "date": date(2026, 12, 17), "start_time": time(13, 0), "end_time": time(16, 0), "duration_minutes": 180, "period": "Afternoon", "is_available": True, "is_blackout": False},
    ]

    created_slots = []
    for s in slots_data:
        slot_obj = TimeSlot(**s)
        db.add(slot_obj)
        created_slots.append(slot_obj)
    db.commit()

    # 3. Course Examinations (22 exams)
    exams_data = [
        {"exam_code": "EXAM-CS101", "course_code": "CS101", "course_name": "Introduction to Computer Science", "department": "Computer Science", "semester": "Fall", "duration_minutes": 120, "exam_type": "Written", "required_features": ["Wheelchair Access"], "priority": 8, "is_locked": False},
        {"exam_code": "EXAM-CS201", "course_code": "CS201", "course_name": "Data Structures & Algorithms", "department": "Computer Science", "semester": "Fall", "duration_minutes": 180, "exam_type": "Written", "required_features": [], "priority": 9, "is_locked": False},
        {"exam_code": "EXAM-CS301", "course_code": "CS301", "course_name": "Operating Systems & Kernel Design", "department": "Computer Science", "semester": "Fall", "duration_minutes": 150, "exam_type": "Written", "required_features": [], "priority": 7, "is_locked": False},
        {"exam_code": "EXAM-CS350", "course_code": "CS350", "course_name": "Database Management Systems", "department": "Computer Science", "semester": "Fall", "duration_minutes": 120, "exam_type": "Written", "required_features": [], "priority": 6, "is_locked": False},
        {"exam_code": "EXAM-CS420", "course_code": "CS420", "course_name": "Machine Learning & Neural Networks", "department": "Computer Science", "semester": "Fall", "duration_minutes": 120, "exam_type": "Practical", "required_features": ["Computers"], "priority": 8, "is_locked": False},
        
        {"exam_code": "EXAM-MA101", "course_code": "MA101", "course_name": "Calculus I & Analytical Geometry", "department": "Mathematics", "semester": "Fall", "duration_minutes": 180, "exam_type": "Written", "required_features": [], "priority": 9, "is_locked": False},
        {"exam_code": "EXAM-MA201", "course_code": "MA201", "course_name": "Linear Algebra & Matrices", "department": "Mathematics", "semester": "Fall", "duration_minutes": 150, "exam_type": "Written", "required_features": [], "priority": 7, "is_locked": False},
        {"exam_code": "EXAM-MA204", "course_code": "MA204", "course_name": "Discrete Mathematics", "department": "Mathematics", "semester": "Fall", "duration_minutes": 120, "exam_type": "Written", "required_features": [], "priority": 8, "is_locked": False},
        {"exam_code": "EXAM-MA310", "course_code": "MA310", "course_name": "Probability & Statistics", "department": "Mathematics", "semester": "Fall", "duration_minutes": 120, "exam_type": "Written", "required_features": [], "priority": 6, "is_locked": False},

        {"exam_code": "EXAM-PHY101", "course_code": "PHY101", "course_name": "Classical Mechanics", "department": "Physics", "semester": "Fall", "duration_minutes": 150, "exam_type": "Written", "required_features": [], "priority": 7, "is_locked": False},
        {"exam_code": "EXAM-PHY202", "course_code": "PHY202", "course_name": "Electromagnetism & Waves", "department": "Physics", "semester": "Fall", "duration_minutes": 150, "exam_type": "Written", "required_features": [], "priority": 7, "is_locked": False},
        {"exam_code": "EXAM-PHY305", "course_code": "PHY305", "course_name": "Quantum Mechanics I", "department": "Physics", "semester": "Fall", "duration_minutes": 180, "exam_type": "Written", "required_features": [], "priority": 8, "is_locked": False},

        {"exam_code": "EXAM-EE101", "course_code": "EE101", "course_name": "Circuit Theory & Analysis", "department": "Electrical Eng", "semester": "Fall", "duration_minutes": 150, "exam_type": "Written", "required_features": [], "priority": 7, "is_locked": False},
        {"exam_code": "EXAM-EE210", "course_code": "EE210", "course_name": "Digital Logic & FPGA Design", "department": "Electrical Eng", "semester": "Fall", "duration_minutes": 120, "exam_type": "Practical", "required_features": ["Computers"], "priority": 8, "is_locked": False},
        {"exam_code": "EXAM-EE320", "course_code": "EE320", "course_name": "Signals & Systems", "department": "Electrical Eng", "semester": "Fall", "duration_minutes": 150, "exam_type": "Written", "required_features": [], "priority": 7, "is_locked": False},

        {"exam_code": "EXAM-BUS101", "course_code": "BUS101", "course_name": "Principles of Management", "department": "Business", "semester": "Fall", "duration_minutes": 120, "exam_type": "Written", "required_features": [], "priority": 5, "is_locked": False},
        {"exam_code": "EXAM-BUS205", "course_code": "BUS205", "course_name": "Corporate Financial Accounting", "department": "Business", "semester": "Fall", "duration_minutes": 150, "exam_type": "Written", "required_features": [], "priority": 7, "is_locked": False},
        {"exam_code": "EXAM-BUS310", "course_code": "BUS310", "course_name": "Strategic Marketing", "department": "Business", "semester": "Fall", "duration_minutes": 120, "exam_type": "Written", "required_features": [], "priority": 5, "is_locked": False},
        {"exam_code": "EXAM-BUS401", "course_code": "BUS401", "course_name": "Business Analytics & Big Data", "department": "Business", "semester": "Fall", "duration_minutes": 120, "exam_type": "Practical", "required_features": ["Computers"], "priority": 6, "is_locked": False},

        {"exam_code": "EXAM-HUM102", "course_code": "HUM102", "course_name": "Professional Ethics & Law", "department": "Humanities", "semester": "Fall", "duration_minutes": 90, "exam_type": "Written", "required_features": [], "priority": 4, "is_locked": False},
        {"exam_code": "EXAM-ENG201", "course_code": "ENG201", "course_name": "Technical Writing & Communication", "department": "Humanities", "semester": "Fall", "duration_minutes": 90, "exam_type": "Written", "required_features": [], "priority": 4, "is_locked": False},
        # One Locked Exam per requirements
        {"exam_code": "EXAM-CS499", "course_code": "CS499", "course_name": "Senior Capstone Defense", "department": "Computer Science", "semester": "Fall", "duration_minutes": 120, "exam_type": "Oral", "required_features": ["Projector"], "priority": 10, "is_locked": True, "notes": "Locked by Dean of Computing to Day 1 Morning in AUD-MAIN"}
    ]

    created_exams = []
    for e in exams_data:
        exam_obj = CourseExam(**e)
        db.add(exam_obj)
        created_exams.append(exam_obj)
    db.commit()

    # 4. Students (60 students)
    departments = ["Computer Science", "Mathematics", "Physics", "Electrical Eng", "Business"]
    first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Pat", "Riley", "Casey", "Dakota",
                   "Cameron", "Jamie", "Logan", "Kendall", "Reese", "Quinn", "Avery", "Harper", "Rowan", "Hayden",
                   "Elena", "Liam", "Sophia", "Noah", "Olivia", "Lucas", "Emma", "Oliver", "Ava", "Elijah",
                   "Mia", "William", "Isabella", "James", "Amelia", "Benjamin", "Charlotte", "Henry", "Harper", "Alexander"]
    last_names = ["Chen", "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez",
                  "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson"]

    created_students = []
    for i in range(1, 61):
        fn = first_names[(i - 1) % len(first_names)]
        ln = last_names[(i * 3) % len(last_names)]
        dept = departments[(i - 1) % len(departments)]
        accommodations = ["Wheelchair Access"] if i in [7, 24] else []
        student = Student(
            student_id=f"STU-2026-{1000 + i}",
            name=f"{fn} {ln}",
            department=dept,
            semester="Fall",
            special_accommodations=accommodations
        )
        db.add(student)
        created_students.append(student)
    db.commit()

    # 5. Enrollments: Each student enrolled in 3 to 4 related courses
    # Exam map for convenience
    exam_by_code = {e.exam_code: e for e in created_exams}

    # Curricula by student group
    enrollments_to_add = []
    for idx, student in enumerate(created_students):
        s_id = student.id
        dept = student.department

        if dept == "Computer Science":
            # CS students: CS101/201, MA101/204, CS301, CS420, HUM102
            courses = ["EXAM-CS101", "EXAM-MA101", "EXAM-CS201", "EXAM-MA204"] if idx < 12 else ["EXAM-CS301", "EXAM-CS350", "EXAM-CS420", "EXAM-HUM102"]
            if idx == 0:
                courses.append("EXAM-CS499") # Senior capstone
        elif dept == "Mathematics":
            courses = ["EXAM-MA101", "EXAM-MA201", "EXAM-CS101", "EXAM-MA310"]
        elif dept == "Physics":
            courses = ["EXAM-PHY101", "EXAM-MA101", "EXAM-PHY202", "EXAM-PHY305"]
        elif dept == "Electrical Eng":
            courses = ["EXAM-EE101", "EXAM-MA101", "EXAM-EE210", "EXAM-EE320"]
        else: # Business
            courses = ["EXAM-BUS101", "EXAM-BUS205", "EXAM-BUS310", "EXAM-BUS401"]

        for c_code in courses:
            exam = exam_by_code.get(c_code)
            if exam:
                enrollments_to_add.append(StudentEnrollment(student_id=s_id, exam_id=exam.id))

    db.bulk_save_objects(enrollments_to_add)
    db.commit()

    # 6. Seed locked assignment for EXAM-CS499 (Senior Capstone) to Day 1 Morning in AUD-MAIN
    capstone_exam = exam_by_code.get("EXAM-CS499")
    slot_d1_m = db.query(TimeSlot).filter_by(slot_code="SLOT-D1-M").first()
    aud_room = db.query(Room).filter_by(room_code="AUD-MAIN").first()

    # Initial baseline version
    initial_version = TimetableVersion(
        version_number=1,
        name="Baseline Timetable (Pre-Optimization)",
        is_active=True,
        solver_status="PRE_OPTIMIZATION",
        solver_runtime_ms=0.0,
        quality_score=0.0,
        objective_cost=0.0,
        metrics={
            "total_exams": 22,
            "scheduled_exams": 22,
            "unscheduled_exams": 0,
            "total_students": 60,
            "quality_score": 0.0,
            "is_optimized": False,
            "students_multiple_same_day": 14,
            "pct_multiple_same_day": 23.3,
            "back_to_back_exam_count": 6,
            "avg_exams_per_student_day": 1.25,
            "avg_gap_days": 1.4,
            "min_gap_days": 0,
            "peak_daily_exams": 7,
            "avg_daily_exams": 5.5,
            "daily_imbalance_std": 1.8,
            "room_utilization_pct": 54.2,
            "total_assigned_seats": 218,
            "total_capacity_used": 402,
            "reassigned_exams_count": 0,
            "preferred_slot_violations": 0,
            "undesirable_sessions_count": 0,
            "total_objective_cost": 0.0,
        },
        diagnostics=[],
        created_by="Academic Registrar",
        notes="Pre-optimization baseline draft. Timetable grid is empty until optimization is executed."
    )
    db.add(initial_version)
    db.commit()

    # Pre-optimization state: Timetable Grid and Backlogs remain empty until the user runs/extracts the optimizer.
    # Audit log entry
    audit = AuditLog(
        action="IMPORT",
        entity_type="DATASET",
        entity_id="BASELINE_V1",
        user="Academic Registrar",
        details={"exams_count": len(created_exams), "students_count": len(created_students), "rooms_count": len(created_rooms)}
    )
    db.add(audit)
    db.commit()
    if include_infeasible:
        create_infeasible_scenario(db)

    return {
        "exams_count": len(created_exams),
        "students_count": len(created_students),
        "rooms_count": len(created_rooms),
        "timeslots_count": len(created_slots),
        "enrollments_count": len(enrollments_to_add),
        "version_id": initial_version.id
    }

def seed_demo_backlogs_if_empty(db: Session):
    """Ensures demo backlog records exist in database if none are present."""
    if db.query(BacklogRecord).count() > 0:
        return
    demo_backlogs = [
        BacklogRecord(
            student_code="STU-2026-1002",
            student_name="Jordan Garcia",
            department="Computer Science",
            student_type="Old Student",
            current_semester="Semester 3",
            backlog_semester="Semester 1",
            semester_type="Odd Semester",
            course_code="MA101",
            course_name="Calculus I & Analytical Geometry",
            exam_date="2026-12-19",
            exam_day="Saturday",
            start_time="09:30:00",
            end_time="12:30:00",
            period="Morning",
            room_code="AUD-MAIN",
            room_name="Grand University Auditorium",
            seat_number="AUD-MAIN-BK01",
            status="SCHEDULED"
        ),
        BacklogRecord(
            student_code="STU-2026-1004",
            student_name="Elena Rodriguez",
            department="Computer Science",
            student_type="Old Student",
            current_semester="Semester 3",
            backlog_semester="Semester 1",
            semester_type="Odd Semester",
            course_code="CS101",
            course_name="Introduction to Computer Science",
            exam_date="2026-12-19",
            exam_day="Saturday",
            start_time="14:00:00",
            end_time="17:00:00",
            period="Afternoon",
            room_code="LAB-COMP",
            room_name="Advanced Computing Laboratory",
            seat_number="LAB-COMP-BK02",
            status="SCHEDULED"
        ),
        BacklogRecord(
            student_code="STU-2026-1007",
            student_name="Lucas Williams",
            department="Mathematics",
            student_type="Old Student",
            current_semester="Semester 5",
            backlog_semester="Semester 3",
            semester_type="Odd Semester",
            course_code="MA201",
            course_name="Multivariable Calculus",
            exam_date="2026-12-19",
            exam_day="Saturday",
            start_time="09:30:00",
            end_time="12:30:00",
            period="Morning",
            room_code="HALL-101",
            room_name="Science Lecture Hall A",
            seat_number="HALL-101-BK03",
            status="SCHEDULED"
        ),
        BacklogRecord(
            student_code="STU-2026-1010",
            student_name="Emma Davis",
            department="Physics",
            student_type="Old Student",
            current_semester="Semester 5",
            backlog_semester="Semester 1",
            semester_type="Odd Semester",
            course_code="PHY101",
            course_name="Classical Mechanics",
            exam_date="2026-12-19",
            exam_day="Saturday",
            start_time="14:00:00",
            end_time="17:00:00",
            period="Afternoon",
            room_code="AUD-MAIN",
            room_name="Grand University Auditorium",
            seat_number="AUD-MAIN-BK04",
            status="SCHEDULED"
        ),
        BacklogRecord(
            student_code="STU-2026-1015",
            student_name="Oliver Hernandez",
            department="Electrical Eng",
            student_type="Old Student",
            current_semester="Semester 3",
            backlog_semester="Semester 1",
            semester_type="Odd Semester",
            course_code="EE101",
            course_name="Electric Circuits & Network Theory",
            exam_date="2026-12-19",
            exam_day="Saturday",
            start_time="09:30:00",
            end_time="12:30:00",
            period="Morning",
            room_code="HALL-101",
            room_name="Science Lecture Hall A",
            seat_number="HALL-101-BK05",
            status="SCHEDULED"
        ),
        BacklogRecord(
            student_code="STU-2026-1020",
            student_name="Mia Jackson",
            department="Business",
            student_type="Old Student",
            current_semester="Semester 3",
            backlog_semester="Semester 1",
            semester_type="Odd Semester",
            course_code="BUS101",
            course_name="Principles of Financial Accounting",
            exam_date="2026-12-19",
            exam_day="Saturday",
            start_time="09:30:00",
            end_time="12:30:00",
            period="Morning",
            room_code="AUD-MAIN",
            room_name="Grand University Auditorium",
            seat_number="AUD-MAIN-BK06",
            status="SCHEDULED"
        ),
        BacklogRecord(
            student_code="STU-2026-1025",
            student_name="William Smith",
            department="Computer Science",
            student_type="New Student",
            current_semester="Semester 1",
            backlog_semester="Semester 1",
            semester_type="Odd Semester",
            course_code="CS101",
            course_name="Introduction to Computer Science",
            exam_date="2026-12-19",
            exam_day="Saturday",
            start_time="14:00:00",
            end_time="17:00:00",
            period="Afternoon",
            room_code="LAB-COMP",
            room_name="Advanced Computing Laboratory",
            seat_number="LAB-COMP-BK07",
            status="SCHEDULED"
        ),
        BacklogRecord(
            student_code="STU-2026-1030",
            student_name="Henry Chen",
            department="Mathematics",
            student_type="Old Student",
            current_semester="Semester 4",
            backlog_semester="Semester 2",
            semester_type="Even Semester",
            course_code="MA204",
            course_name="Discrete Mathematics",
            exam_date="2026-12-19",
            exam_day="Saturday",
            start_time="14:00:00",
            end_time="17:00:00",
            period="Afternoon",
            room_code="HALL-101",
            room_name="Science Lecture Hall A",
            seat_number="HALL-101-BK08",
            status="SCHEDULED"
        )
    ]
    db.add_all(demo_backlogs)
    db.commit()

def create_infeasible_scenario(db: Session) -> dict:
    """
    Creates an intentionally impossible scheduling conflict:
    Locks two conflicting examinations (EXAM-CS101 and EXAM-MA101 sharing 12 students)
    to the exact same time slot and room, to demonstrate the diagnostics engine.
    """
    cs101 = db.query(CourseExam).filter_by(exam_code="EXAM-CS101").first()
    ma101 = db.query(CourseExam).filter_by(exam_code="EXAM-MA101").first()
    slot = db.query(TimeSlot).filter_by(slot_code="SLOT-D1-M").first()
    room = db.query(Room).filter_by(room_code="HALL-101").first()

    if cs101 and ma101 and slot and room:
        cs101.is_locked = True
        ma101.is_locked = True
        db.commit()

        # Update latest active version's assignments
        active_ver = db.query(TimetableVersion).filter_by(is_active=True).first()
        if active_ver:
            a_cs = db.query(TimetableAssignment).filter_by(timetable_id=active_ver.id, exam_id=cs101.id).first()
            a_ma = db.query(TimetableAssignment).filter_by(timetable_id=active_ver.id, exam_id=ma101.id).first()
            if not a_cs:
                a_cs = TimetableAssignment(timetable_id=active_ver.id, exam_id=cs101.id, assigned_student_count=12)
                db.add(a_cs)
            if not a_ma:
                a_ma = TimetableAssignment(timetable_id=active_ver.id, exam_id=ma101.id, assigned_student_count=12)
                db.add(a_ma)
            a_cs.timeslot_id = slot.id
            a_cs.room_id = room.id
            a_cs.is_locked = True
            a_ma.timeslot_id = slot.id
            a_ma.room_id = room.id
            a_ma.is_locked = True
            active_ver.solver_status = "INFEASIBLE"
            db.commit()

    return {
        "status": "INFEASIBLE_SCENARIO_CONFIGURED",
        "description": "EXAM-CS101 and EXAM-MA101 both locked to SLOT-D1-M and HALL-101 despite sharing students."
    }

def reset_infeasible_scenario(db: Session) -> dict:
    """
    Clears any conflicting locked exams (unlocks EXAM-CS101 and EXAM-MA101),
    leaving only EXAM-CS499 locked.
    """
    for code in ["EXAM-CS101", "EXAM-MA101"]:
        e = db.query(CourseExam).filter_by(exam_code=code).first()
        if e:
            e.is_locked = False
            for a in db.query(TimetableAssignment).filter_by(exam_id=e.id).all():
                a.is_locked = False
    db.commit()
    return {
        "status": "INFEASIBLE_SCENARIO_CLEARED",
        "description": "EXAM-CS101 and EXAM-MA101 locks removed."
    }
