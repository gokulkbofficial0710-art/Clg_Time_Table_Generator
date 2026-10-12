from typing import List, Dict, Set, Any, Tuple
from app.solver.conflict_graph import ExamConflictGraph

class SchedulingDiagnostics:
    """
    Dedicated Diagnostics Module for Infeasibility and Conflict Root-Cause Analysis.
    Identifies exact structural, capacity, feature, duration, and locked-exam bottlenecks.
    """
    def __init__(
        self,
        exams: List[Dict[str, Any]],
        rooms: List[Dict[str, Any]],
        timeslots: List[Dict[str, Any]],
        enrollments: Dict[int, Set[int]],
        locked_assignments: Dict[int, Tuple[int, int]] = None
    ):
        self.exams = exams
        self.rooms = rooms
        self.timeslots = timeslots
        self.enrollments = enrollments
        self.locked_assignments = locked_assignments or {}
        self.exam_map = {e["id"]: e for e in exams}
        self.room_map = {r["id"]: r for r in rooms}
        self.slot_map = {s["id"]: s for s in timeslots}

        exam_ids = [e["id"] for e in exams]
        self.conflict_graph = ExamConflictGraph(exam_ids, enrollments)

    def diagnose_all(self) -> List[Dict[str, Any]]:
        diagnostics = []

        # 1. Diagnose Locked Examination Clashes
        diagnostics.extend(self._diagnose_locked_exam_clashes())

        # 2. Diagnose Duration Impossibilities
        diagnostics.extend(self._diagnose_duration_infeasibility())

        # 3. Diagnose Room Capacity Impossibilities
        diagnostics.extend(self._diagnose_room_capacity_infeasibility())

        # 4. Diagnose Room Feature Deficiencies
        diagnostics.extend(self._diagnose_feature_infeasibility())

        # 5. Diagnose Restricted Slot Infeasibility
        diagnostics.extend(self._diagnose_restricted_slots())

        # 6. Diagnose Global Pigeonhole Slot Bottleneck
        diagnostics.extend(self._diagnose_global_pigeonhole())

        # 7. Diagnose Blackout Collisions on Locked Exams
        diagnostics.extend(self._diagnose_locked_blackouts())

        return diagnostics

    def _diagnose_locked_exam_clashes(self) -> List[Dict[str, Any]]:
        issues = []
        locked_items = list(self.locked_assignments.items())
        n = len(locked_items)
        for i in range(n):
            for j in range(i + 1, n):
                e1_id, (s1_id, r1_id) = locked_items[i]
                e2_id, (s2_id, r2_id) = locked_items[j]

                # Same room at same slot
                if s1_id == s2_id and r1_id == r2_id:
                    e1 = self.exam_map.get(e1_id, {})
                    e2 = self.exam_map.get(e2_id, {})
                    r = self.room_map.get(r1_id, {})
                    s = self.slot_map.get(s1_id, {})
                    issues.append({
                        "type": "LOCKED_ROOM_DOUBLE_BOOKING",
                        "severity": "FATAL",
                        "title": f"Locked Room Clash: {r.get('room_code')} Overbooked",
                        "message": (
                            f"Scheduling conflict: '{e1.get('exam_code')}' and '{e2.get('exam_code')}' "
                            f"are both locked to room '{r.get('room_code')}' during slot '{s.get('slot_code')}' "
                            f"({s.get('date')} {s.get('start_time')})."
                        ),
                        "affected_exams": [e1.get("exam_code"), e2.get("exam_code")],
                        "corrective_action": "Unlock or reassign one of the examinations to another room."
                    })

                # Shared students at same slot
                if s1_id == s2_id:
                    shared = self.conflict_graph.get_shared_students(e1_id, e2_id)
                    if shared:
                        e1 = self.exam_map.get(e1_id, {})
                        e2 = self.exam_map.get(e2_id, {})
                        s = self.slot_map.get(s1_id, {})
                        issues.append({
                            "type": "LOCKED_STUDENT_CLASH",
                            "severity": "FATAL",
                            "title": f"Locked Student Clash: {e1.get('exam_code')} & {e2.get('exam_code')}",
                            "message": (
                                f"Scheduling conflict: '{e1.get('exam_code')}' and '{e2.get('exam_code')}' "
                                f"share {len(shared)} student(s), but both are locked to overlapping time slot "
                                f"'{s.get('slot_code')}' on {s.get('date')} {s.get('start_time')}."
                            ),
                            "affected_exams": [e1.get("exam_code"), e2.get("exam_code")],
                            "affected_students_count": len(shared),
                            "corrective_action": "Unlock or reschedule one of the examinations to a different time slot."
                        })
        return issues

    def _diagnose_duration_infeasibility(self) -> List[Dict[str, Any]]:
        issues = []
        max_slot_dur = max([s["duration_minutes"] for s in self.timeslots if s.get("is_available") and not s.get("is_blackout")], default=0)
        for e in self.exams:
            dur = e.get("duration_minutes", 120)
            if dur > max_slot_dur:
                issues.append({
                    "type": "DURATION_EXCEEDS_MAX_SLOT",
                    "severity": "FATAL",
                    "title": f"Duration Exceeded: {e.get('exam_code')}",
                    "message": (
                        f"Examination '{e.get('exam_code')}' requires {dur} minutes, but the maximum available "
                        f"time slot in the institution schedule is only {max_slot_dur} minutes."
                    ),
                    "affected_exams": [e.get("exam_code")],
                    "corrective_action": f"Create a time slot of at least {dur} minutes or reduce the examination duration."
                })
        return issues

    def _diagnose_room_capacity_infeasibility(self) -> List[Dict[str, Any]]:
        issues = []
        max_room_cap = max([r["capacity"] for r in self.rooms if r.get("is_available")], default=0)
        for e in self.exams:
            count = len(self.enrollments.get(e["id"], set()))
            if count > max_room_cap:
                issues.append({
                    "type": "NO_ROOM_WITH_ENOUGH_CAPACITY",
                    "severity": "FATAL",
                    "title": f"Insufficient Capacity: {e.get('exam_code')}",
                    "message": (
                        f"Examination '{e.get('exam_code')}' has {count} enrolled students, but the largest "
                        f"available room has a capacity of only {max_room_cap} seats."
                    ),
                    "affected_exams": [e.get("exam_code")],
                    "corrective_action": f"Add an auditorium or larger room with at least {count} seats, or split the course."
                })
        return issues

    def _diagnose_feature_infeasibility(self) -> List[Dict[str, Any]]:
        issues = []
        for e in self.exams:
            req_features = set(e.get("required_features", []))
            if not req_features:
                continue
            matching_rooms = [
                r for r in self.rooms 
                if r.get("is_available") and req_features.issubset(set(r.get("features", [])))
            ]
            if not matching_rooms:
                issues.append({
                    "type": "NO_COMPATIBLE_ROOM_FEATURES",
                    "severity": "FATAL",
                    "title": f"Room Feature Mismatch: {e.get('exam_code')}",
                    "message": (
                        f"Examination '{e.get('exam_code')}' requires features {list(req_features)}, but no "
                        f"available room possesses all of these required features."
                    ),
                    "affected_exams": [e.get("exam_code")],
                    "corrective_action": f"Configure room features to include: {', '.join(req_features)}."
                })
        return issues

    def _diagnose_restricted_slots(self) -> List[Dict[str, Any]]:
        issues = []
        available_slot_ids = {s["id"] for s in self.timeslots if s.get("is_available") and not s.get("is_blackout")}
        for e in self.exams:
            eligible = e.get("eligible_slot_ids")
            if eligible is not None and len(eligible) > 0:
                valid_eligible = set(eligible).intersection(available_slot_ids)
                if not valid_eligible:
                    issues.append({
                        "type": "NO_ELIGIBLE_AVAILABLE_SLOTS",
                        "severity": "FATAL",
                        "title": f"No Eligible Slot: {e.get('exam_code')}",
                        "message": (
                            f"Examination '{e.get('exam_code')}' is restricted to slot IDs {eligible}, but none "
                            f"of these slots are currently active and available."
                        ),
                        "affected_exams": [e.get("exam_code")],
                        "corrective_action": "Expand eligible time slots or remove slot restriction."
                    })
        return issues

    def _diagnose_global_pigeonhole(self) -> List[Dict[str, Any]]:
        issues = []
        avail_slots = [s for s in self.timeslots if s.get("is_available") and not s.get("is_blackout")]
        avail_rooms = [r for r in self.rooms if r.get("is_available")]
        total_slots = len(avail_slots)
        total_rooms = len(avail_rooms)
        total_room_slots = total_slots * total_rooms

        if len(self.exams) > total_room_slots:
            issues.append({
                "type": "ROOM_SLOT_PIGEONHOLE_DEFICIT",
                "severity": "FATAL",
                "title": "Insufficient Total Room-Slots",
                "message": (
                    f"There are {len(self.exams)} examinations to schedule, but only {total_slots} slots × "
                    f"{total_rooms} rooms = {total_room_slots} total scheduling opportunities exist."
                ),
                "affected_exams": [e.get("exam_code") for e in self.exams],
                "corrective_action": "Add more exam dates/time slots or configure additional rooms."
            })

        # Conflict graph clique lower bound
        min_slots_needed = self.conflict_graph.estimate_min_slots_clique()
        if min_slots_needed > total_slots:
            issues.append({
                "type": "CLIQUE_CONFLICT_SLOT_DEFICIT",
                "severity": "FATAL",
                "title": "Conflict Graph Density Exceeds Available Slots",
                "message": (
                    f"A mutual conflict clique of size {min_slots_needed} was identified (exams sharing common students), "
                    f"requiring at least {min_slots_needed} distinct time slots. Only {total_slots} slots are available."
                ),
                "affected_exams": [e.get("exam_code") for e in self.exams],
                "corrective_action": f"Expand examination period to at least {min_slots_needed} time slots."
            })

        return issues

    def _diagnose_locked_blackouts(self) -> List[Dict[str, Any]]:
        issues = []
        for e_id, (s_id, r_id) in self.locked_assignments.items():
            slot = self.slot_map.get(s_id)
            if slot and (not slot.get("is_available") or slot.get("is_blackout")):
                e = self.exam_map.get(e_id, {})
                issues.append({
                    "type": "LOCKED_ON_BLACKOUT_SLOT",
                    "severity": "FATAL",
                    "title": f"Locked on Blackout Slot: {e.get('exam_code')}",
                    "message": (
                        f"Locked examination '{e.get('exam_code')}' is assigned to blackout/holiday slot "
                        f"'{slot.get('slot_code')}' ({slot.get('blackout_reason', 'Blackout')})."
                    ),
                    "affected_exams": [e.get("exam_code")],
                    "corrective_action": "Unlock or reassign the examination to an open date."
                })
        return issues
