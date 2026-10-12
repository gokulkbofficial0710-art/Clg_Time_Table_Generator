from typing import List, Dict, Any, Optional
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.timetable import TimetableVersion
from app.models.assignment import TimetableAssignment
from app.models.exam import CourseExam
from app.models.room import Room
from app.models.timeslot import TimeSlot
from app.models.student import Student
from app.models.enrollment import StudentEnrollment
from app.schemas.analytics import DashboardSummary, DayDistributionItem, RoomUtilizationItem, StudentLoadItem

router = APIRouter(prefix="/analytics", tags=["Analytics & Dashboard"])

@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_exams = db.query(CourseExam).count()
    total_students = db.query(Student).count()
    available_rooms = db.query(Room).filter(Room.is_available == True).count()
    available_slots = db.query(TimeSlot).filter(TimeSlot.is_available == True, TimeSlot.is_blackout == False).count()
    locked_exams = db.query(CourseExam).filter(CourseExam.is_locked == True).count()

    active_ver = db.query(TimetableVersion).filter_by(is_active=True).first()
    if not active_ver:
        return DashboardSummary(
            total_exams=total_exams,
            total_students=total_students,
            available_rooms=available_rooms,
            available_timeslots=available_slots,
            scheduled_exams=0,
            unscheduled_exams=total_exams,
            student_clash_count=0,
            room_clash_count=0,
            capacity_violation_count=0,
            locked_exam_count=locked_exams,
            quality_score=0.0,
            solver_status="NO_TIMETABLE",
            is_valid_timetable=False
        )

    assignments = db.query(TimetableAssignment).filter_by(timetable_id=active_ver.id).all()
    scheduled_count = len([a for a in assignments if a.timeslot_id and a.room_id])
    unscheduled_count = total_exams - scheduled_count

    metrics = active_ver.metrics or {}
    is_pre_optimization = (
        active_ver.solver_status in ("PRE_OPTIMIZATION", "DRAFT", "PENDING")
        or "pre-optimization" in (active_ver.name or "").lower()
        or metrics.get("is_optimized") is False
    )
    if is_pre_optimization:
        quality_score = 0.0
    else:
        quality_score = float(active_ver.quality_score or 0.0)

    # Fast conflict counts from assignments
    slot_groups = defaultdict(list)
    room_slot_groups = defaultdict(list)
    capacity_violations = 0

    for a in assignments:
        if a.timeslot_id and a.room_id:
            slot_groups[a.timeslot_id].append(a.exam_id)
            room_slot_groups[(a.room_id, a.timeslot_id)].append(a.exam_id)
            if a.room and a.assigned_student_count > a.room.capacity:
                capacity_violations += 1

    room_clashes = sum(1 for el in room_slot_groups.values() if len(el) > 1)
    
    # Check student clashes
    student_clashes = 0
    # Pre-map enrollments
    exam_students = defaultdict(set)
    for en in db.query(StudentEnrollment).all():
        exam_students[en.exam_id].add(en.student_id)

    for slot_id, exam_ids in slot_groups.items():
        n = len(exam_ids)
        for i in range(n):
            for j in range(i + 1, n):
                if exam_students[exam_ids[i]].intersection(exam_students[exam_ids[j]]):
                    student_clashes += 1

    is_valid = (student_clashes == 0 and room_clashes == 0 and capacity_violations == 0 and unscheduled_count == 0)

    return DashboardSummary(
        total_exams=total_exams,
        total_students=total_students,
        available_rooms=available_rooms,
        available_timeslots=available_slots,
        scheduled_exams=scheduled_count,
        unscheduled_exams=unscheduled_count,
        student_clash_count=student_clashes,
        room_clash_count=room_clashes,
        capacity_violation_count=capacity_violations,
        locked_exam_count=locked_exams,
        quality_score=quality_score if is_valid else 0.0,
        solver_status=active_ver.solver_status,
        active_version_id=active_ver.id,
        active_version_name=active_ver.name,
        last_optimized_at=str(active_ver.created_at),
        is_valid_timetable=is_valid
    )

@router.get("/distributions")
def get_distribution_analytics(db: Session = Depends(get_db)):
    active_ver = db.query(TimetableVersion).filter_by(is_active=True).first()
    if not active_ver:
        return {"dates": [], "rooms": [], "student_loads": []}

    assignments = db.query(TimetableAssignment).filter_by(timetable_id=active_ver.id).all()

    # 1. Date distribution
    date_counts = defaultdict(lambda: {"exam_count": 0, "student_sessions": 0})
    for a in assignments:
        if a.timeslot:
            d_str = str(a.timeslot.date)
            date_counts[d_str]["exam_count"] += 1
            date_counts[d_str]["student_sessions"] += a.assigned_student_count

    date_items = []
    for d_str in sorted(date_counts.keys()):
        date_items.append({
            "date": d_str,
            "exam_count": date_counts[d_str]["exam_count"],
            "student_sessions": date_counts[d_str]["student_sessions"]
        })

    # 2. Room utilization
    room_stats = defaultdict(lambda: {"sessions": 0, "seats": 0, "capacity": 0, "name": ""})
    all_rooms = db.query(Room).all()
    for r in all_rooms:
        room_stats[r.room_code]["capacity"] = r.capacity
        room_stats[r.room_code]["name"] = r.name

    for a in assignments:
        if a.room:
            room_stats[a.room.room_code]["sessions"] += 1
            room_stats[a.room.room_code]["seats"] += a.assigned_student_count

    room_items = []
    for code, data in room_stats.items():
        total_possible = data["capacity"] * max(1, data["sessions"])
        rate = round((data["seats"] / total_possible) * 100, 1) if total_possible > 0 else 0.0
        room_items.append({
            "room_code": code,
            "room_name": data["name"],
            "capacity": data["capacity"],
            "sessions": data["sessions"],
            "seats_allocated": data["seats"],
            "utilization_rate": rate
        })

    # 3. Student Daily Load Distribution
    student_day_counts = defaultdict(lambda: defaultdict(int))
    for a in assignments:
        if a.timeslot and a.exam:
            for en in a.exam.enrollments:
                student_day_counts[en.student_id][str(a.timeslot.date)] += 1

    load_buckets = {"1 Exam / Day": 0, "2 Exams / Day": 0, "3+ Exams / Day": 0}
    total_student_days = 0
    for sid, day_map in student_day_counts.items():
        for d, count in day_map.items():
            total_student_days += 1
            if count == 1:
                load_buckets["1 Exam / Day"] += 1
            elif count == 2:
                load_buckets["2 Exams / Day"] += 1
            else:
                load_buckets["3+ Exams / Day"] += 1

    load_items = []
    for cat, cnt in load_buckets.items():
        pct = round((cnt / max(1, total_student_days)) * 100, 1)
        load_items.append({
            "burden_category": cat,
            "count": cnt,
            "percentage": pct
        })

    return {
        "dates": date_items,
        "rooms": room_items,
        "student_loads": load_items,
        "metrics": active_ver.metrics or {}
    }
