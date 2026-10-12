import csv
import io
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.room import Room
from app.models.timeslot import TimeSlot
from app.models.student import Student
from app.models.enrollment import StudentEnrollment
from app.models.exam import CourseExam

CSV_TEMPLATES = {
    "exams": "exam_code,course_code,course_name,department,semester,academic_year,duration_minutes,exam_type,priority,notes\nEXAM-CS101,CS101,Intro to CS,Computer Science,Fall,2026-2027,120,Written,8,Standard written exam\n",
    "students": "student_id,name,department,semester\nSTU-1001,John Doe,Computer Science,Fall\nSTU-1002,Jane Smith,Mathematics,Fall\n",
    "enrollments": "student_id,exam_code\nSTU-1001,EXAM-CS101\nSTU-1002,EXAM-CS101\n",
    "rooms": "room_code,name,building,capacity,features\nHALL-A,Main Auditorium,Central Hall,120,Projector|Wheelchair Access\nLAB-1,Computing Lab,Turing Building,35,Computers|Projector\n",
    "timeslots": "slot_code,date,start_time,end_time,duration_minutes,period\nSLOT-01,2026-12-14,09:00,12:00,180,Morning\nSLOT-02,2026-12-14,13:00,16:00,180,Afternoon\n"
}

def parse_and_preview_csv(entity_type: str, file_content: str) -> Dict[str, Any]:
    reader = csv.DictReader(io.StringIO(file_content))
    rows = list(reader)

    preview_items = []
    valid_count = 0
    invalid_count = 0

    for idx, row in enumerate(rows, start=1):
        errors = []
        # Basic validation per entity
        if entity_type == "exams":
            if not row.get("exam_code"):
                errors.append("Missing required field: exam_code")
            if not row.get("course_code"):
                errors.append("Missing required field: course_code")
            if not row.get("course_name"):
                errors.append("Missing required field: course_name")
            if row.get("duration_minutes"):
                try:
                    dur = int(row["duration_minutes"])
                    if dur < 15:
                        errors.append("Duration must be at least 15 minutes")
                except ValueError:
                    errors.append("duration_minutes must be an integer")
        elif entity_type == "students":
            if not row.get("student_id"):
                errors.append("Missing required field: student_id")
            if not row.get("name"):
                errors.append("Missing required field: name")
        elif entity_type == "rooms":
            if not row.get("room_code"):
                errors.append("Missing required field: room_code")
            if not row.get("capacity"):
                errors.append("Missing required field: capacity")
            else:
                try:
                    cap = int(row["capacity"])
                    if cap < 1:
                        errors.append("Capacity must be >= 1")
                except ValueError:
                    errors.append("Capacity must be an integer")
        elif entity_type == "timeslots":
            if not row.get("slot_code"):
                errors.append("Missing required field: slot_code")
            if not row.get("date"):
                errors.append("Missing required field: date (YYYY-MM-DD)")
            if not row.get("start_time"):
                errors.append("Missing required field: start_time (HH:MM)")

        status = "VALID" if not errors else "INVALID"
        if status == "VALID":
            valid_count += 1
        else:
            invalid_count += 1

        preview_items.append({
            "row_number": idx,
            "data": dict(row),
            "status": status,
            "errors": errors
        })

    return {
        "entity_type": entity_type,
        "total_rows": len(rows),
        "valid_rows": valid_count,
        "invalid_rows": invalid_count,
        "preview_items": preview_items,
        "can_commit": invalid_count == 0 and len(rows) > 0
    }

def commit_imported_data(db: Session, entity_type: str, items: List[Dict[str, Any]], overwrite: bool = False) -> Dict[str, Any]:
    committed_count = 0

    if entity_type == "exams":
        for item in items:
            existing = db.query(CourseExam).filter_by(exam_code=item["exam_code"]).first()
            if existing and not overwrite:
                continue
            if existing and overwrite:
                existing.course_code = item.get("course_code", existing.course_code)
                existing.course_name = item.get("course_name", existing.course_name)
                existing.department = item.get("department", existing.department)
                existing.duration_minutes = int(item.get("duration_minutes", existing.duration_minutes))
            else:
                new_e = CourseExam(
                    exam_code=item["exam_code"],
                    course_code=item.get("course_code", item["exam_code"]),
                    course_name=item.get("course_name", item["exam_code"]),
                    department=item.get("department", "General"),
                    semester=item.get("semester", "Fall"),
                    academic_year=item.get("academic_year", "2026-2027"),
                    duration_minutes=int(item.get("duration_minutes", 120)),
                    exam_type=item.get("exam_type", "Written"),
                    priority=int(item.get("priority", 5)),
                    notes=item.get("notes")
                )
                db.add(new_e)
            committed_count += 1

    elif entity_type == "students":
        for item in items:
            existing = db.query(Student).filter_by(student_id=item["student_id"]).first()
            if existing and not overwrite:
                continue
            if existing and overwrite:
                existing.name = item.get("name", existing.name)
                existing.department = item.get("department", existing.department)
            else:
                new_s = Student(
                    student_id=item["student_id"],
                    name=item["name"],
                    department=item.get("department", "General"),
                    semester=item.get("semester", "Fall")
                )
                db.add(new_s)
            committed_count += 1

    elif entity_type == "rooms":
        for item in items:
            existing = db.query(Room).filter_by(room_code=item["room_code"]).first()
            if existing and not overwrite:
                continue
            feats = [f.strip() for f in item.get("features", "").split("|") if f.strip()]
            if existing and overwrite:
                existing.name = item.get("name", existing.name)
                existing.building = item.get("building", existing.building)
                existing.capacity = int(item.get("capacity", existing.capacity))
                existing.features = feats
            else:
                new_r = Room(
                    room_code=item["room_code"],
                    name=item.get("name", item["room_code"]),
                    building=item.get("building", "Main Campus"),
                    capacity=int(item.get("capacity", 30)),
                    features=feats
                )
                db.add(new_r)
            committed_count += 1

    elif entity_type == "enrollments":
        for item in items:
            student = db.query(Student).filter_by(student_id=item["student_id"]).first()
            exam = db.query(CourseExam).filter_by(exam_code=item["exam_code"]).first()
            if student and exam:
                existing = db.query(StudentEnrollment).filter_by(student_id=student.id, exam_id=exam.id).first()
                if not existing:
                    db.add(StudentEnrollment(student_id=student.id, exam_id=exam.id))
                    committed_count += 1

    db.commit()
    return {"status": "SUCCESS", "committed_count": committed_count}
