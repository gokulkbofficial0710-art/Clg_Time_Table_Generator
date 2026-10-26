import re
import csv
import io
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.student import Student
from app.models.enrollment import StudentEnrollment
from app.models.exam import CourseExam

DEPARTMENT_ALIASES: Dict[str, str] = {
    "cs": "Computer Science",
    "cse": "Computer Science",
    "computer science": "Computer Science",
    "comp sci": "Computer Science",
    "computer science & engineering": "Computer Science",
    "computer science and engineering": "Computer Science",
    "math": "Mathematics",
    "maths": "Mathematics",
    "mathematics": "Mathematics",
    "applied mathematics": "Mathematics",
    "applied math": "Mathematics",
    "bus": "Business",
    "business": "Business",
    "bba": "Business",
    "mba": "Business",
    "business administration": "Business",
    "mgmt": "Business",
    "management": "Business",
    "ee": "Electrical Eng",
    "eee": "Electrical Eng",
    "ece": "Electrical Eng",
    "electrical": "Electrical Eng",
    "electrical engineering": "Electrical Eng",
    "electronics": "Electrical Eng",
    "electronics & communication": "Electrical Eng",
    "phy": "Physics",
    "physics": "Physics",
    "mech": "Mechanical Eng",
    "me": "Mechanical Eng",
    "mechanical": "Mechanical Eng",
    "mechanical engineering": "Mechanical Eng",
    "civil": "Civil Eng",
    "ce": "Civil Eng",
    "civil engineering": "Civil Eng",
    "humanities": "Humanities",
    "arts": "Humanities",
    "english": "Humanities",
    "literature": "Humanities"
}

def normalize_department(raw: str) -> str:
    cleaned = (raw or "").strip()
    if not cleaned:
        return "General"
    lower = cleaned.lower()
    return DEPARTMENT_ALIASES.get(lower, cleaned.title())

def parse_accommodations(raw: Any) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip() and str(x).strip().lower() not in ("none", "nil", "n/a", "no")]
    val = str(raw).strip()
    if val.lower() in ("none", "nil", "n/a", "no", "-"):
        return []
    parts = re.split(r"[|,;]", val)
    return [p.strip() for p in parts if p.strip() and p.strip().lower() not in ("none", "nil", "n/a", "no")]

def parse_courses(raw: Any) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x).strip().upper() for x in raw if str(x).strip()]
    val = str(raw).strip()
    if val.lower() in ("none", "nil", "n/a", "no", "-"):
        return []
    parts = re.split(r"[|,;/\s]+", val)
    clean = []
    for p in parts:
        p_clean = p.strip().upper()
        if p_clean and len(p_clean) >= 2:
            clean.append(p_clean)
    return clean

def detect_block_format(lines: List[str]) -> bool:
    """Detects if lines follow a key-value block format like 'Student ID: ... \n Name: ...'"""
    kv_count = 0
    for line in lines[:30]:
        l = line.strip().lower()
        if re.match(r"^(student\s*id|id|roll\s*(no|number)?|name|department|dept|branch)\s*:\s*.+", l):
            kv_count += 1
    return kv_count >= 3

def parse_block_format(text: str) -> List[Dict[str, Any]]:
    """Parses text formatted as key-value blocks separated by blank lines or delimiters."""
    blocks = re.split(r"\n\s*(?:---+|\*\*\*+|===+|\n+)\s*", text.strip())
    parsed_items = []
    row_num = 1

    for block in blocks:
        lines = [line.strip() for line in block.strip().splitlines() if line.strip() and not line.strip().startswith(("#", "//"))]
        if not lines:
            continue

        item: Dict[str, Any] = {
            "row_number": row_num,
            "student_id": "",
            "name": "",
            "department": "General",
            "semester": "Semester 5",
            "enrolled_courses": [],
            "special_accommodations": [],
            "errors": []
        }

        for line in lines:
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip().lower()
            val = val.strip()

            if key in ("student_id", "student id", "id", "roll", "roll no", "roll_no", "roll number", "reg no", "reg_no"):
                item["student_id"] = val
            elif key in ("name", "student name", "student_name", "full name", "candidate"):
                item["name"] = val
            elif key in ("department", "dept", "branch", "major", "faculty", "stream"):
                item["department"] = normalize_department(val)
            elif key in ("semester", "sem", "year", "term"):
                item["semester"] = val if val.lower().startswith("semester") else f"Semester {val}" if val.isdigit() else val
            elif key in ("courses", "exams", "subjects", "papers", "enrolled", "enrolled_exams"):
                item["enrolled_courses"] = parse_courses(val)
            elif key in ("accommodations", "special_accommodations", "special accommodations", "needs", "notes"):
                item["special_accommodations"] = parse_accommodations(val)

        if not item["student_id"] and not item["name"]:
            continue

        if not item["student_id"]:
            item["errors"].append("Missing required field: student_id")
        if not item["name"]:
            item["errors"].append("Missing required field: name")

        item["status"] = "INVALID" if item["errors"] else "VALID"
        parsed_items.append(item)
        row_num += 1

    return parsed_items

def parse_delimited_format(lines: List[str]) -> List[Dict[str, Any]]:
    """Parses delimited text (comma, tab, pipe, semicolon) with or without headers."""
    # Filter comments and blanks
    clean_lines = [l for l in lines if l.strip() and not l.strip().startswith(("#", "//"))]
    if not clean_lines:
        return []

    # Detect separator from first 5 lines
    sample = "\n".join(clean_lines[:5])
    counts = {
        ",": sample.count(","),
        "|": sample.count("|"),
        "\t": sample.count("\t"),
        ";": sample.count(";")
    }
    delimiter = max(counts, key=counts.get)
    if counts[delimiter] == 0:
        delimiter = ","

    reader = csv.reader(clean_lines, delimiter=delimiter)
    raw_rows = [row for row in reader if row and any(cell.strip() for cell in row)]
    if not raw_rows:
        return []

    # Check if first row is a header (requires at least 2 exact header column matches)
    first_row = [cell.strip().lower() for cell in raw_rows[0]]
    exact_headers = {
        "student_id", "student id", "id", "roll", "roll_no", "roll no", "rollnumber", "roll_number",
        "name", "student_name", "student name", "full_name", "candidate", "candidate_name",
        "department", "dept", "branch", "major", "stream",
        "semester", "sem", "term", "year",
        "course", "courses", "exam", "exams", "subject", "subjects",
        "accommodation", "accommodations", "special_accommodations"
    }
    matches = [
        col for col in first_row
        if col in exact_headers or re.sub(r"[^a-z0-9_]", "_", col).strip("_") in exact_headers
    ]
    has_header = len(matches) >= 2

    header_map: Dict[str, int] = {}
    data_rows = raw_rows

    if has_header:
        for idx, col in enumerate(first_row):
            col_clean = re.sub(r"[^a-z0-9_]", "_", col).strip("_")
            if any(k == col_clean or col_clean.startswith(k) for k in ("student_id", "roll", "reg_no", "enrollment", "id")):
                header_map["student_id"] = idx
            elif any(k == col_clean or col_clean.startswith(k) for k in ("name", "candidate")):
                header_map["name"] = idx
            elif any(k == col_clean or col_clean.startswith(k) for k in ("department", "dept", "branch", "major")):
                header_map["department"] = idx
            elif any(k == col_clean or col_clean.startswith(k) for k in ("semester", "sem", "term")):
                header_map["semester"] = idx
            elif any(k == col_clean or col_clean.startswith(k) for k in ("course", "exam", "subject", "paper")):
                header_map["courses"] = idx
            elif any(k == col_clean or col_clean.startswith(k) for k in ("accommodation", "need", "special")):
                header_map["accommodations"] = idx
        data_rows = raw_rows[1:]
    else:
        # Positional default mapping: 0: student_id, 1: name, 2: department, 3: semester, 4: courses, 5: accommodations
        header_map = {
            "student_id": 0,
            "name": 1,
            "department": 2,
            "semester": 3,
            "courses": 4,
            "accommodations": 5
        }

    parsed_items = []
    for row_idx, row in enumerate(data_rows, start=1):
        clean_row = [c.strip() for c in row]
        if not clean_row or not any(clean_row):
            continue

        errors = []

        # Extract student_id
        sid_col = header_map.get("student_id", 0)
        sid = clean_row[sid_col] if sid_col < len(clean_row) else ""

        # Extract name
        name_col = header_map.get("name", 1)
        name = clean_row[name_col] if name_col < len(clean_row) else ""

        # Extract department
        dept_col = header_map.get("department", 2)
        dept_raw = clean_row[dept_col] if dept_col < len(clean_row) else "General"
        department = normalize_department(dept_raw)

        # Extract semester
        sem_col = header_map.get("semester", 3)
        sem_raw = clean_row[sem_col] if sem_col < len(clean_row) else "Semester 5"
        if not sem_raw:
            sem_raw = "Semester 5"
        elif sem_raw.isdigit():
            sem_raw = f"Semester {sem_raw}"

        # Extract courses / exams
        courses_col = header_map.get("courses", 4)
        courses_raw = clean_row[courses_col] if courses_col < len(clean_row) else ""
        courses = parse_courses(courses_raw)

        # Extract accommodations
        acc_col = header_map.get("accommodations", 5)
        acc_raw = clean_row[acc_col] if acc_col < len(clean_row) else ""
        accommodations = parse_accommodations(acc_raw)

        if not sid:
            errors.append("Missing required field: student_id")
        if not name:
            errors.append("Missing required field: name")

        parsed_items.append({
            "row_number": row_idx,
            "student_id": sid,
            "name": name,
            "department": department,
            "semester": sem_raw,
            "enrolled_courses": courses,
            "special_accommodations": accommodations,
            "status": "INVALID" if errors else "VALID",
            "errors": errors
        })

    return parsed_items

def parse_student_text_file(text_content: str) -> Dict[str, Any]:
    """
    Intelligently parses a plain text or CSV file of student attributes.
    Supports CSV/TSV/Pipe formats and Key-Value block formats.
    """
    raw_lines = text_content.splitlines()
    if detect_block_format(raw_lines):
        items = parse_block_format(text_content)
    else:
        items = parse_delimited_format(raw_lines)

    valid_count = sum(1 for it in items if it["status"] == "VALID")
    invalid_count = len(items) - valid_count

    depts: Dict[str, int] = {}
    for it in items:
        if it["status"] == "VALID" and it.get("department"):
            depts[it["department"]] = depts.get(it["department"], 0) + 1

    return {
        "total_found": len(items),
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "departments_detected": depts,
        "students": items
    }

def commit_student_text_records(
    db: Session,
    students_data: List[Dict[str, Any]],
    overwrite: bool = True,
    auto_enroll: bool = True
) -> Dict[str, Any]:
    """
    Commits parsed student records into the database.
    Creates or updates Student entities, and optionally creates StudentEnrollment mappings.
    """
    created_count = 0
    updated_count = 0
    enrollments_added = 0
    dept_counts: Dict[str, int] = {}

    all_exams = db.query(CourseExam).all()
    exam_by_code = {ex.course_code.upper(): ex for ex in all_exams}
    exam_by_id_code = {ex.exam_code.upper(): ex for ex in all_exams}

    for item in students_data:
        if item.get("status") == "INVALID":
            continue

        sid = item.get("student_id", "").strip()
        name = item.get("name", "").strip()
        dept = item.get("department", "General").strip()
        sem = item.get("semester", "Semester 5").strip()
        accommodations = item.get("special_accommodations", [])
        courses = item.get("enrolled_courses", [])

        if not sid or not name:
            continue

        dept_counts[dept] = dept_counts.get(dept, 0) + 1

        existing = db.query(Student).filter_by(student_id=sid).first()
        student_obj: Optional[Student] = None

        if existing:
            if overwrite:
                existing.name = name
                existing.department = dept
                existing.semester = sem
                existing.special_accommodations = accommodations
                updated_count += 1
            student_obj = existing
        else:
            new_student = Student(
                student_id=sid,
                name=name,
                department=dept,
                semester=sem,
                special_accommodations=accommodations
            )
            db.add(new_student)
            db.flush() # Populate new_student.id
            student_obj = new_student
            created_count += 1

        # Enrollments processing
        if student_obj and student_obj.id:
            existing_enrollments = {
                en.exam_id for en in db.query(StudentEnrollment).filter_by(student_id=student_obj.id).all()
            }

            matched_exams = []
            if courses:
                for c in courses:
                    c_up = c.upper()
                    ex = exam_by_code.get(c_up) or exam_by_id_code.get(c_up)
                    if ex and ex.id not in existing_enrollments:
                        matched_exams.append(ex)
            elif auto_enroll:
                # If no courses provided and auto_enroll is on, match by department
                for ex in all_exams:
                    if ex.department.lower() == dept.lower() and ex.id not in existing_enrollments:
                        matched_exams.append(ex)

            for ex in matched_exams:
                db.add(StudentEnrollment(student_id=student_obj.id, exam_id=ex.id))
                existing_enrollments.add(ex.id)
                enrollments_added += 1

    db.commit()

    return {
        "status": "SUCCESS",
        "message": f"Successfully processed {created_count + updated_count} student records ({created_count} added, {updated_count} updated).",
        "total_processed": created_count + updated_count,
        "created_count": created_count,
        "updated_count": updated_count,
        "enrollments_added": enrollments_added,
        "departments": dept_counts
    }
