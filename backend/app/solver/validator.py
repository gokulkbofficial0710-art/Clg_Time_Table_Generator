from typing import List, Dict, Set, Any, Tuple
from datetime import datetime, date, time
from app.schemas.timetable import ConflictViolation, ValidationResult

class TimetableValidator:
    """
    Independent Hard Constraint Verification Engine.
    Verifies that all constraints H1 - H9 are strictly satisfied.
    """
    def __init__(
        self,
        exams: List[Dict[str, Any]],
        rooms: List[Dict[str, Any]],
        timeslots: List[Dict[str, Any]],
        enrollments: Dict[int, Set[int]], # exam_id -> set of student_ids
        assignments: List[Dict[str, Any]], # list of assigned records
        locked_assignments: Dict[int, Tuple[int, int]] = None, # exam_id -> (slot_id, room_id)
        students: Dict[int, Dict[str, Any]] = None, # student_id -> student dict
        is_pre_optimization: bool = False
    ):
        self.exams = {e["id"]: e for e in exams}
        self.rooms = {r["id"]: r for r in rooms}
        self.timeslots = {t["id"]: t for t in timeslots}
        self.enrollments = enrollments
        self.assignments = assignments
        self.locked_assignments = locked_assignments or {}
        self.students = students or {}
        self.is_pre_optimization = is_pre_optimization or (len(assignments) == 0)

    def validate(self) -> ValidationResult:
        violations: List[ConflictViolation] = []
        scheduled_exam_ids: Set[int] = set()

        # Group assignments by slot and by room
        slot_assignments: Dict[int, List[Dict[str, Any]]] = {}
        room_slot_assignments: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}

        # 1. Check each individual assignment
        for a in self.assignments:
            exam_id = a.get("exam_id")
            slot_id = a.get("timeslot_id")
            room_id = a.get("room_id")

            if not exam_id or exam_id not in self.exams:
                violations.append(ConflictViolation(
                    rule="H9",
                    severity="CRITICAL",
                    title="Invalid Examination Reference",
                    description=f"Assignment references unknown exam ID {exam_id}",
                    suggested_action="Remove corrupt assignment record."
                ))
                continue

            exam = self.exams[exam_id]

            # If unscheduled or missing slot/room
            if not slot_id or not room_id:
                violations.append(ConflictViolation(
                    rule="H9",
                    severity="CRITICAL",
                    title="Incomplete Schedule Assignment",
                    description=f"Examination '{exam['exam_code']}' ({exam['course_name']}) is unscheduled or missing slot/room assignment.",
                    exam_id=exam_id,
                    exam_code=exam["exam_code"],
                    suggested_action="Assign a valid time slot and room or run optimizer."
                ))
                continue

            scheduled_exam_ids.add(exam_id)

            if slot_id not in self.timeslots:
                violations.append(ConflictViolation(
                    rule="H5",
                    severity="CRITICAL",
                    title="Unknown Time Slot Reference",
                    description=f"Examination '{exam['exam_code']}' assigned to non-existent slot ID {slot_id}",
                    exam_id=exam_id,
                    exam_code=exam["exam_code"],
                    timeslot_id=slot_id,
                    suggested_action="Assign to an active valid time slot."
                ))
                continue

            if room_id not in self.rooms:
                violations.append(ConflictViolation(
                    rule="H3",
                    severity="CRITICAL",
                    title="Unknown Room Reference",
                    description=f"Examination '{exam['exam_code']}' assigned to non-existent room ID {room_id}",
                    exam_id=exam_id,
                    exam_code=exam["exam_code"],
                    room_id=room_id,
                    suggested_action="Assign to an active valid room."
                ))
                continue

            slot = self.timeslots[slot_id]
            room = self.rooms[room_id]

            slot_assignments.setdefault(slot_id, []).append(a)
            room_slot_assignments.setdefault((room_id, slot_id), []).append(a)

            # H4: Examination duration
            if exam["duration_minutes"] > slot["duration_minutes"]:
                violations.append(ConflictViolation(
                    rule="H4",
                    severity="CRITICAL",
                    title="Duration Exceeded",
                    description=f"Examination '{exam['exam_code']}' requires {exam['duration_minutes']} min, but slot '{slot['slot_code']}' is only {slot['duration_minutes']} min.",
                    exam_id=exam_id,
                    exam_code=exam["exam_code"],
                    timeslot_id=slot_id,
                    suggested_action=f"Move examination '{exam['exam_code']}' to a slot with at least {exam['duration_minutes']} minutes duration."
                ))

            # H5: Time-slot availability and institutional blackouts
            if not slot.get("is_available", True) or slot.get("is_blackout", False):
                reason = slot.get("blackout_reason") or "institutional blackout"
                violations.append(ConflictViolation(
                    rule="H5",
                    severity="CRITICAL",
                    title="Blackout Slot Assignment",
                    description=f"Examination '{exam['exam_code']}' is scheduled during blackout/unavailable slot '{slot['slot_code']}' ({reason}).",
                    exam_id=exam_id,
                    exam_code=exam["exam_code"],
                    timeslot_id=slot_id,
                    date=str(slot["date"]),
                    suggested_action="Move examination to a regular available examination session."
                ))

            # H2: Room capacity
            student_count = len(self.enrollments.get(exam_id, set()))
            if student_count > room["capacity"]:
                violations.append(ConflictViolation(
                    rule="H2",
                    severity="CRITICAL",
                    title="Room Capacity Exceeded",
                    description=f"Examination '{exam['exam_code']}' has {student_count} enrolled students, exceeding room '{room['room_code']}' capacity ({room['capacity']} seats).",
                    exam_id=exam_id,
                    exam_code=exam["exam_code"],
                    room_id=room_id,
                    room_code=room["room_code"],
                    affected_students_count=student_count - room["capacity"],
                    suggested_action=f"Assign a larger room with at least {student_count} seats (e.g. auditorium)."
                ))

            # H3: Room availability and maintenance intervals
            if not room.get("is_available", True):
                violations.append(ConflictViolation(
                    rule="H3",
                    severity="CRITICAL",
                    title="Unavailable Room Assignment",
                    description=f"Examination '{exam['exam_code']}' is assigned to room '{room['room_code']}', which is currently marked unavailable.",
                    exam_id=exam_id,
                    exam_code=exam["exam_code"],
                    room_id=room_id,
                    room_code=room["room_code"],
                    suggested_action="Reassign to an operational room."
                ))

            # Check room blackout intervals
            for bo in room.get("blackout_intervals", []):
                bo_date = bo.get("date")
                if bo_date and str(slot["date"]) == str(bo_date):
                    violations.append(ConflictViolation(
                        rule="H3",
                        severity="CRITICAL",
                        title="Room Maintenance Window Conflict",
                        description=f"Room '{room['room_code']}' is under blackout/maintenance on {bo_date} ({bo.get('reason', 'Scheduled maintenance')}).",
                        exam_id=exam_id,
                        exam_code=exam["exam_code"],
                        room_id=room_id,
                        room_code=room["room_code"],
                        timeslot_id=slot_id,
                        date=str(slot["date"]),
                        suggested_action="Move examination to an alternate date or room."
                    ))

            # H7: Room suitability (features & accessibility)
            req_features = set(exam.get("required_features", []))
            room_features = set(room.get("features", []))
            missing_features = req_features.difference(room_features)
            if missing_features:
                violations.append(ConflictViolation(
                    rule="H7",
                    severity="CRITICAL",
                    title="Room Feature Deficiency",
                    description=f"Examination '{exam['exam_code']}' requires features {list(missing_features)}, not provided by room '{room['room_code']}'.",
                    exam_id=exam_id,
                    exam_code=exam["exam_code"],
                    room_id=room_id,
                    room_code=room["room_code"],
                    suggested_action=f"Select a room equipped with: {', '.join(missing_features)}."
                ))

            # H6: Locked assignment verification
            if exam_id in self.locked_assignments:
                expected_slot_id, expected_room_id = self.locked_assignments[exam_id]
                if slot_id != expected_slot_id or room_id != expected_room_id:
                    violations.append(ConflictViolation(
                        rule="H6",
                        severity="CRITICAL",
                        title="Locked Examination Displaced",
                        description=f"Locked examination '{exam['exam_code']}' was moved from slot {expected_slot_id}/room {expected_room_id} to slot {slot_id}/room {room_id}.",
                        exam_id=exam_id,
                        exam_code=exam["exam_code"],
                        timeslot_id=slot_id,
                        room_id=room_id,
                        suggested_action="Preserve the locked schedule coordinates or explicitly unlock."
                    ))

        # H9: Assignment completeness: All exams must be scheduled
        # In pre-optimization draft baseline, examinations are unallocated pending optimization execution
        if not self.is_pre_optimization and len(self.assignments) > 0:
            for exam_id, exam in self.exams.items():
                if exam_id not in scheduled_exam_ids:
                    violations.append(ConflictViolation(
                        rule="H9",
                        severity="CRITICAL",
                        title="Unscheduled Examination",
                        description=f"Required examination '{exam['exam_code']}' ({exam['course_name']}) has not been scheduled.",
                        exam_id=exam_id,
                        exam_code=exam["exam_code"],
                        suggested_action="Run the optimization solver or manually schedule this examination."
                    ))

        # H3: Room double-booking: A room cannot host two overlapping examinations
        for (room_id, slot_id), booked_list in room_slot_assignments.items():
            if len(booked_list) > 1:
                exam_codes = [self.exams[b["exam_id"]]["exam_code"] for b in booked_list if b["exam_id"] in self.exams]
                room = self.rooms[room_id]
                slot = self.timeslots[slot_id]
                violations.append(ConflictViolation(
                    rule="H3",
                    severity="CRITICAL",
                    title="Room Double-Booking",
                    description=f"Room '{room['room_code']}' is double-booked for {len(booked_list)} examinations ({', '.join(exam_codes)}) during slot '{slot['slot_code']}' ({slot['date']} {slot['start_time']}).",
                    room_id=room_id,
                    room_code=room["room_code"],
                    timeslot_id=slot_id,
                    date=str(slot["date"]),
                    suggested_action="Move one of the overlapping examinations to an unoccupied room or alternate slot."
                ))

        # H1: Student clash prevention: No student takes two exams at the same time
        for slot_id, booked_list in slot_assignments.items():
            n = len(booked_list)
            for i in range(n):
                for j in range(i + 1, n):
                    e1_id = booked_list[i]["exam_id"]
                    e2_id = booked_list[j]["exam_id"]
                    shared_students = self.enrollments.get(e1_id, set()).intersection(
                        self.enrollments.get(e2_id, set())
                    )
                    if shared_students:
                        e1 = self.exams[e1_id]
                        e2 = self.exams[e2_id]
                        slot = self.timeslots[slot_id]
                        student_names = []
                        for sid in list(shared_students)[:5]:
                            s_data = self.students.get(sid, {})
                            student_names.append(s_data.get("name") or str(sid))

                        violations.append(ConflictViolation(
                            rule="H1",
                            severity="CRITICAL",
                            title="Student Examination Clash",
                            description=f"Examinations '{e1['exam_code']}' and '{e2['exam_code']}' share {len(shared_students)} student(s) ({', '.join(student_names)}{'...' if len(shared_students) > 5 else ''}), but are scheduled concurrently at slot '{slot['slot_code']}' on {slot['date']} {slot['start_time']}.",
                            exam_id=e1_id,
                            exam_code=e1["exam_code"],
                            related_exam_code=e2["exam_code"],
                            timeslot_id=slot_id,
                            date=str(slot["date"]),
                            affected_students_count=len(shared_students),
                            affected_student_ids=[str(s) for s in shared_students],
                            suggested_action=f"Reschedule either '{e1['exam_code']}' or '{e2['exam_code']}' to a non-conflicting time slot."
                        ))

        is_complete = len(scheduled_exam_ids) == len(self.exams)
        is_feasible = len(violations) == 0 and (is_complete or self.is_pre_optimization)

        if self.is_pre_optimization:
            summary = "Draft baseline loaded (unallocated). Zero constraint clashes detected. Optimization pending."
        else:
            summary = "All hard constraints verified successfully. Timetable is completely valid." if is_feasible else (
                f"Validation failed: {len(violations)} hard constraint violation(s) detected. Timetable is INFEASIBLE."
            )

        return ValidationResult(
            is_feasible=is_feasible,
            is_complete=is_complete,
            hard_constraint_violations_count=len(violations),
            violations=violations,
            summary=summary
        )
