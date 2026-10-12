from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.exam import CourseExam
from app.models.student import Student
from app.models.enrollment import StudentEnrollment
from app.models.audit import AuditLog
from app.schemas.exam import ExamCreate, ExamUpdate, ExamResponse
from app.schemas.student import StudentResponse
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/exams", tags=["Examinations"])

@router.get("", response_model=List[ExamResponse])
def get_all_exams(
    department: Optional[str] = None,
    is_locked: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(CourseExam)
    if department:
        query = query.filter(CourseExam.department == department)
    if is_locked is not None:
        query = query.filter(CourseExam.is_locked == is_locked)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (CourseExam.exam_code.ilike(s)) |
            (CourseExam.course_name.ilike(s)) |
            (CourseExam.course_code.ilike(s))
        )
    exams = query.order_by(CourseExam.id).all()

    result = []
    for e in exams:
        student_ids = [en.student_id for en in e.enrollments]
        resp = ExamResponse.model_validate(e)
        resp.enrollment_count = len(student_ids)
        resp.enrolled_student_ids = student_ids
        result.append(resp)
    return result

@router.get("/{id}", response_model=ExamResponse)
def get_exam_by_id(id: int, db: Session = Depends(get_db)):
    exam = db.query(CourseExam).filter_by(id=id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    student_ids = [en.student_id for en in exam.enrollments]
    resp = ExamResponse.model_validate(exam)
    resp.enrollment_count = len(student_ids)
    resp.enrolled_student_ids = student_ids
    return resp

@router.post("", response_model=ExamResponse)
def create_exam(req: ExamCreate, db: Session = Depends(get_db)):
    existing = db.query(CourseExam).filter_by(exam_code=req.exam_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Exam with code '{req.exam_code}' already exists")
    
    exam = CourseExam(
        exam_code=req.exam_code,
        course_code=req.course_code,
        course_name=req.course_name,
        department=req.department,
        semester=req.semester,
        academic_year=req.academic_year,
        duration_minutes=req.duration_minutes,
        exam_type=req.exam_type,
        required_features=req.required_features,
        eligible_slot_ids=req.eligible_slot_ids,
        preferred_slot_ids=req.preferred_slot_ids,
        priority=req.priority,
        is_locked=req.is_locked,
        notes=req.notes
    )
    db.add(exam)
    db.flush()

    if req.enrolled_student_ids:
        for sid in req.enrolled_student_ids:
            db.add(StudentEnrollment(student_id=sid, exam_id=exam.id))

    db.add(AuditLog(action="CREATE", entity_type="EXAM", entity_id=str(exam.id), details={"exam_code": exam.exam_code}))
    db.commit()
    db.refresh(exam)

    student_ids = [en.student_id for en in exam.enrollments]
    resp = ExamResponse.model_validate(exam)
    resp.enrollment_count = len(student_ids)
    resp.enrolled_student_ids = student_ids
    return resp

@router.put("/{id}", response_model=ExamResponse)
def update_exam(id: int, req: ExamUpdate, db: Session = Depends(get_db)):
    exam = db.query(CourseExam).filter_by(id=id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if req.exam_code and req.exam_code != exam.exam_code:
        conflict = db.query(CourseExam).filter_by(exam_code=req.exam_code).first()
        if conflict:
            raise HTTPException(status_code=400, detail=f"Exam code '{req.exam_code}' already taken")
        exam.exam_code = req.exam_code

    if req.course_code is not None:
        exam.course_code = req.course_code
    if req.course_name is not None:
        exam.course_name = req.course_name
    if req.department is not None:
        exam.department = req.department
    if req.duration_minutes is not None:
        exam.duration_minutes = req.duration_minutes
    if req.exam_type is not None:
        exam.exam_type = req.exam_type
    if req.required_features is not None:
        exam.required_features = req.required_features
    if req.eligible_slot_ids is not None:
        exam.eligible_slot_ids = req.eligible_slot_ids
    if req.preferred_slot_ids is not None:
        exam.preferred_slot_ids = req.preferred_slot_ids
    if req.priority is not None:
        exam.priority = req.priority
    if req.is_locked is not None:
        exam.is_locked = req.is_locked
    if req.notes is not None:
        exam.notes = req.notes

    if req.enrolled_student_ids is not None:
        # Sync enrollments
        db.query(StudentEnrollment).filter_by(exam_id=exam.id).delete()
        for sid in req.enrolled_student_ids:
            db.add(StudentEnrollment(student_id=sid, exam_id=exam.id))

    db.add(AuditLog(action="UPDATE", entity_type="EXAM", entity_id=str(exam.id), details={"exam_code": exam.exam_code}))
    db.commit()
    db.refresh(exam)

    student_ids = [en.student_id for en in exam.enrollments]
    resp = ExamResponse.model_validate(exam)
    resp.enrollment_count = len(student_ids)
    resp.enrolled_student_ids = student_ids
    return resp

@router.delete("/{id}", response_model=MessageResponse)
def delete_exam(id: int, db: Session = Depends(get_db)):
    exam = db.query(CourseExam).filter_by(id=id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    exam_code = exam.exam_code
    db.delete(exam)
    db.add(AuditLog(action="DELETE", entity_type="EXAM", entity_id=str(id), details={"exam_code": exam_code}))
    db.commit()
    return MessageResponse(message=f"Exam '{exam_code}' deleted successfully.")

@router.patch("/{id}/lock", response_model=MessageResponse)
def toggle_exam_lock(id: int, lock: Optional[bool] = None, db: Session = Depends(get_db)):
    exam = db.query(CourseExam).filter_by(id=id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    exam.is_locked = (not exam.is_locked) if lock is None else lock
    db.add(AuditLog(action="LOCK" if exam.is_locked else "UNLOCK", entity_type="EXAM", entity_id=str(id), details={"is_locked": exam.is_locked}))
    db.commit()
    return MessageResponse(message=f"Exam '{exam.exam_code}' is now {'locked' if exam.is_locked else 'unlocked'}.")

@router.get("/{id}/students", response_model=List[StudentResponse])
def get_exam_students(id: int, db: Session = Depends(get_db)):
    exam = db.query(CourseExam).filter_by(id=id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    students = [en.student for en in exam.enrollments]
    return [
        StudentResponse(
            id=s.id,
            student_id=s.student_id,
            name=s.name,
            department=s.department,
            semester=s.semester,
            special_accommodations=s.special_accommodations or [],
            enrolled_exam_ids=[e.exam_id for e in s.enrollments]
        )
        for s in students
    ]
