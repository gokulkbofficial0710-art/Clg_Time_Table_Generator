import time
from typing import List, Dict, Set, Any, Tuple, Optional
from collections import defaultdict
from ortools.sat.python import cp_model

from app.solver.conflict_graph import ExamConflictGraph
from app.solver.validator import TimetableValidator
from app.solver.diagnostics import SchedulingDiagnostics
from app.solver.metrics import QualityMetricsCalculator

class SchedulingEngine:
    """
    Intelligent Examination Timetable Optimization Engine.
    Uses Google OR-Tools CP-SAT for exact constraint satisfaction and multi-objective optimization.
    """
    def __init__(
        self,
        exams: List[Dict[str, Any]],
        rooms: List[Dict[str, Any]],
        timeslots: List[Dict[str, Any]],
        enrollments: Dict[int, Set[int]], # exam_id -> set of student_ids
        students: Dict[int, Dict[str, Any]] = None,
        locked_assignments: Dict[int, Tuple[int, int]] = None, # exam_id -> (timeslot_id, room_id)
        previous_assignments: List[Dict[str, Any]] = None,
        time_limit_seconds: int = 30,
        mode: str = "full", # "full" or "minimal_change"
        weights: Dict[str, int] = None
    ):
        self.exams = exams
        self.rooms = rooms
        self.timeslots = timeslots
        self.enrollments = enrollments
        self.students = students or {}
        self.locked_assignments = locked_assignments or {}
        self.previous_assignments = previous_assignments or []
        self.time_limit_seconds = max(1, min(300, time_limit_seconds))
        self.mode = mode
        self.weights = {
            "burden": 200,
            "spacing": 100,
            "imbalance": 60,
            "preference": 20,
            "utilization": 2,
            "reassignment": 150 if mode == "minimal_change" else 20,
            "undesirable": 80
        }
        if weights:
            self.weights.update(weights)

        self.exam_map = {e["id"]: e for e in exams}
        self.room_map = {r["id"]: r for r in rooms}
        self.slot_map = {s["id"]: s for s in timeslots}

        # Build conflict graph
        exam_ids = [e["id"] for e in exams]
        self.conflict_graph = ExamConflictGraph(exam_ids, enrollments)

    def solve(self) -> Dict[str, Any]:
        start_time = time.time()

        # Step 1: Pre-solve diagnostics check
        diagnostics_checker = SchedulingDiagnostics(
            exams=self.exams,
            rooms=self.rooms,
            timeslots=self.timeslots,
            enrollments=self.enrollments,
            locked_assignments=self.locked_assignments
        )
        pre_diagnostics = diagnostics_checker.diagnose_all()
        fatal_issues = [d for d in pre_diagnostics if d.get("severity") == "FATAL"]

        # If there are already proven impossible constraints (e.g. locked exam clash or room too small)
        if fatal_issues:
            elapsed_ms = (time.time() - start_time) * 1000.0
            return {
                "solver_status": "INFEASIBLE",
                "solver_runtime_ms": round(elapsed_ms, 2),
                "assignments": [],
                "diagnostics": pre_diagnostics,
                "is_feasible": False,
                "is_complete": False,
                "quality_score": 0.0,
                "objective_cost": 999999.0,
                "metrics": {},
                "validation": {
                    "is_feasible": False,
                    "is_complete": False,
                    "hard_constraint_violations_count": len(fatal_issues),
                    "violations": [
                        {
                            "rule": "H-DIAG",
                            "severity": "CRITICAL",
                            "title": f["title"],
                            "description": f["message"],
                            "suggested_action": f["corrective_action"]
                        } for f in fatal_issues
                    ],
                    "summary": f"Infeasibility proven during pre-solve validation: {fatal_issues[0]['message']}"
                }
            }

        # Step 2: Build CP-SAT Model
        model = cp_model.CpModel()

        # Filter available slots and available rooms
        valid_slots = [
            s for s in self.timeslots 
            if s.get("is_available", True) and not s.get("is_blackout", False)
        ]
        valid_rooms = [r for r in self.rooms if r.get("is_available", True)]

        if not valid_slots or not valid_rooms:
            elapsed_ms = (time.time() - start_time) * 1000.0
            diag = [{
                "type": "RESOURCES_UNAVAILABLE",
                "severity": "FATAL",
                "title": "No Available Time Slots or Rooms",
                "message": "Scheduling cannot proceed because either available rooms or available time slots count is zero.",
                "affected_exams": [e["exam_code"] for e in self.exams],
                "corrective_action": "Enable time slots and rooms in management settings."
            }]
            return {
                "solver_status": "INFEASIBLE",
                "solver_runtime_ms": round(elapsed_ms, 2),
                "assignments": [],
                "diagnostics": diag,
                "is_feasible": False,
                "is_complete": False,
                "quality_score": 0.0,
                "objective_cost": 999999.0,
                "metrics": {},
                "validation": {
                    "is_feasible": False,
                    "is_complete": False,
                    "hard_constraint_violations_count": 1,
                    "violations": [],
                    "summary": "No available rooms or time slots."
                }
            }

        # Decision Variables: X[e_id, s_id, r_id]
        # And auxiliary slot assignment variables: Y[e_id, s_id]
        X: Dict[Tuple[int, int, int], cp_model.IntVar] = {}
        Y: Dict[Tuple[int, int], cp_model.IntVar] = {}

        candidates_per_exam: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
        exam_candidates_room_for_slot: Dict[Tuple[int, int], List[int]] = defaultdict(list)

        # Compute candidates respecting Hard Constraints H2, H3 (blackouts), H4, H5, H7
        for exam in self.exams:
            e_id = exam["id"]
            e_dur = exam["duration_minutes"]
            e_req_features = set(exam.get("required_features", []))
            e_eligible_slots = set(exam.get("eligible_slot_ids", []))
            enrolled_count = len(self.enrollments.get(e_id, set()))

            is_locked = e_id in self.locked_assignments
            locked_slot_id, locked_room_id = self.locked_assignments.get(e_id, (None, None))

            for slot in valid_slots:
                s_id = slot["id"]

                # H5 / eligible slot check
                if e_eligible_slots and s_id not in e_eligible_slots:
                    continue

                # H4: Duration check
                if e_dur > slot["duration_minutes"]:
                    continue

                for room in valid_rooms:
                    r_id = room["id"]

                    # H2: Capacity check
                    if enrolled_count > room["capacity"]:
                        continue

                    # H7: Room features check
                    r_features = set(room.get("features", []))
                    if not e_req_features.issubset(r_features):
                        continue

                    # H3: Room blackout intervals
                    has_room_blackout = False
                    for bo in room.get("blackout_intervals", []):
                        if bo.get("date") and str(slot["date"]) == str(bo["date"]):
                            has_room_blackout = True
                            break
                    if has_room_blackout:
                        continue

                    # H6: If locked, this exam MUST only match its locked (slot, room)
                    if is_locked and (s_id != locked_slot_id or r_id != locked_room_id):
                        continue

                    var_name = f"x_e{e_id}_s{s_id}_r{r_id}"
                    x_var = model.NewBoolVar(var_name)
                    X[(e_id, s_id, r_id)] = x_var
                    candidates_per_exam[e_id].append((s_id, r_id))
                    exam_candidates_room_for_slot[(e_id, s_id)].append(r_id)

        # Create Y[e_id, s_id] variables
        for exam in self.exams:
            e_id = exam["id"]
            for slot in valid_slots:
                s_id = slot["id"]
                matching_rooms = exam_candidates_room_for_slot.get((e_id, s_id), [])
                if matching_rooms:
                    y_var = model.NewBoolVar(f"y_e{e_id}_s{s_id}")
                    Y[(e_id, s_id)] = y_var
                    # Link: Y[e, s] == sum_r X[e, s, r]
                    model.Add(y_var == sum(X[(e_id, s_id, r)] for r in matching_rooms))

        # Check if any exam has 0 candidates
        for exam in self.exams:
            e_id = exam["id"]
            if not candidates_per_exam[e_id]:
                elapsed_ms = (time.time() - start_time) * 1000.0
                diag = [{
                    "type": "NO_FEASIBLE_CANDIDATE_ASSIGNMENTS",
                    "severity": "FATAL",
                    "title": f"No Feasible Slot/Room for {exam['exam_code']}",
                    "message": f"Examination '{exam['exam_code']}' has no compatible combination of time slot and room satisfying capacity ({len(self.enrollments.get(e_id, set()))} seats), duration ({exam['duration_minutes']}m), and required features.",
                    "affected_exams": [exam["exam_code"]],
                    "corrective_action": "Check room capacities, features, and slot durations."
                }]
                return {
                    "solver_status": "INFEASIBLE",
                    "solver_runtime_ms": round(elapsed_ms, 2),
                    "assignments": [],
                    "diagnostics": diag,
                    "is_feasible": False,
                    "is_complete": False,
                    "quality_score": 0.0,
                    "objective_cost": 999999.0,
                    "metrics": {},
                    "validation": {
                        "is_feasible": False,
                        "is_complete": False,
                        "hard_constraint_violations_count": 1,
                        "violations": [],
                        "summary": f"No feasible candidates for {exam['exam_code']}."
                    }
                }

        # Constraint H9: Assignment completeness: Every exam scheduled exactly once
        for exam in self.exams:
            e_id = exam["id"]
            vars_for_exam = [X[(e_id, s, r)] for (s, r) in candidates_per_exam[e_id]]
            model.Add(sum(vars_for_exam) == 1)

        # Constraint H3: Room availability: Room cannot host two overlapping exams at same slot
        for slot in valid_slots:
            s_id = slot["id"]
            for room in valid_rooms:
                r_id = room["id"]
                room_slot_vars = [
                    X[(e_id, s_id, r_id)]
                    for e_id in self.exam_map.keys()
                    if (e_id, s_id, r_id) in X
                ]
                if len(room_slot_vars) > 1:
                    model.Add(sum(room_slot_vars) <= 1)

        # Constraint H1: Student clash prevention:
        # Two exams sharing at least 1 student cannot be scheduled at the same slot
        # Using conflict graph edges
        for (u, v), shared_count in self.conflict_graph.shared_counts.items():
            if shared_count > 0:
                for slot in valid_slots:
                    s_id = slot["id"]
                    y_u = Y.get((u, s_id))
                    y_v = Y.get((v, s_id))
                    if y_u is not None and y_v is not None:
                        model.Add(y_u + y_v <= 1)

        # Constraint H6: Enforce locked exams
        for e_id, (locked_slot, locked_room) in self.locked_assignments.items():
            if (e_id, locked_slot, locked_room) in X:
                model.Add(X[(e_id, locked_slot, locked_room)] == 1)
            else:
                # Impossible locked assignment
                elapsed_ms = (time.time() - start_time) * 1000.0
                e = self.exam_map.get(e_id, {})
                diag = [{
                    "type": "LOCKED_ASSIGNMENT_UNSATISFIABLE",
                    "severity": "FATAL",
                    "title": f"Locked Assignment Invalid: {e.get('exam_code')}",
                    "message": f"Locked exam '{e.get('exam_code')}' cannot be accommodated in slot {locked_slot} and room {locked_room}.",
                    "affected_exams": [e.get("exam_code")],
                    "corrective_action": "Unlock this examination or adjust room/slot parameters."
                }]
                return {
                    "solver_status": "INFEASIBLE",
                    "solver_runtime_ms": round(elapsed_ms, 2),
                    "assignments": [],
                    "diagnostics": diag,
                    "is_feasible": False,
                    "is_complete": False,
                    "quality_score": 0.0,
                    "objective_cost": 999999.0,
                    "metrics": {},
                    "validation": {
                        "is_feasible": False,
                        "is_complete": False,
                        "hard_constraint_violations_count": 1,
                        "violations": [],
                        "summary": "Locked assignment unsatisfiable."
                    }
                }

        # Step 3: Soft Constraints & Objective Function (S1 - S8)
        objective_terms = []

        # S1: Student daily burden: minimize multiple exams on the same date
        # Group valid slots by date
        slots_by_date: Dict[str, List[int]] = defaultdict(list)
        for s in valid_slots:
            slots_by_date[str(s["date"])].append(s["id"])

        weight_burden = self.weights.get("burden", 100)
        if weight_burden > 0 and len(slots_by_date) > 1:
            for (u, v), shared_count in self.conflict_graph.shared_counts.items():
                if shared_count > 0:
                    for d_str, slot_ids in slots_by_date.items():
                        if len(slot_ids) > 1:
                            u_vars = [Y[(u, s)] for s in slot_ids if (u, s) in Y]
                            v_vars = [Y[(v, s)] for s in slot_ids if (v, s) in Y]
                            if u_vars and v_vars:
                                same_day_bool = model.NewBoolVar(f"same_day_u{u}_v{v}_d{d_str}")
                                # same_day_bool >= sum(u_vars) + sum(v_vars) - 1
                                model.Add(same_day_bool >= sum(u_vars) + sum(v_vars) - 1)
                                objective_terms.append(same_day_bool * (weight_burden * shared_count))

        # S2: Spacing & Rest: minimize consecutive / back-to-back sessions on same day
        weight_spacing = self.weights.get("spacing", 50)
        if weight_spacing > 0:
            # Sort slots within each date by start_time
            for d_str, slot_ids in slots_by_date.items():
                if len(slot_ids) >= 2:
                    sorted_d_slots = sorted(slot_ids, key=lambda sid: self.slot_map[sid]["start_time"])
                    for i in range(len(sorted_d_slots) - 1):
                        s1 = sorted_d_slots[i]
                        s2 = sorted_d_slots[i + 1]
                        for (u, v), shared_count in self.conflict_graph.shared_counts.items():
                            if shared_count > 0:
                                y_u1 = Y.get((u, s1))
                                y_v2 = Y.get((v, s2))
                                if y_u1 is not None and y_v2 is not None:
                                    b2b_var = model.NewBoolVar(f"b2b_u{u}_v{v}_{s1}_{s2}")
                                    model.Add(b2b_var >= y_u1 + y_v2 - 1)
                                    objective_terms.append(b2b_var * (weight_spacing * shared_count))

        # S4: Preferred time slots
        weight_pref = self.weights.get("preference", 20)
        if weight_pref > 0:
            for exam in self.exams:
                e_id = exam["id"]
                preferred = set(exam.get("preferred_slot_ids", []))
                if preferred:
                    for slot in valid_slots:
                        s_id = slot["id"]
                        if s_id not in preferred and (e_id, s_id) in Y:
                            objective_terms.append(Y[(e_id, s_id)] * weight_pref)

        # S5: Room capacity efficiency (penalize wasted seating capacity)
        weight_util = self.weights.get("utilization", 1)
        if weight_util > 0:
            for (e_id, s_id, r_id), x_var in X.items():
                room = self.room_map[r_id]
                enrolled = len(self.enrollments.get(e_id, set()))
                seat_waste = max(0, room["capacity"] - enrolled)
                if seat_waste > 0:
                    objective_terms.append(x_var * (weight_util * min(50, seat_waste // 5)))

        # S6: Minimal changes during re-optimization
        weight_reassign = self.weights.get("reassignment", 80)
        if weight_reassign > 0 and self.previous_assignments:
            prev_map = {
                p["exam_id"]: (p.get("timeslot_id"), p.get("room_id"))
                for p in self.previous_assignments
                if p.get("timeslot_id") and p.get("room_id")
            }
            for exam in self.exams:
                e_id = exam["id"]
                if e_id in prev_map and e_id not in self.locked_assignments:
                    prev_slot, prev_room = prev_map[e_id]
                    if (e_id, prev_slot, prev_room) in X:
                        # If exam stays at same (slot, room), penalty is 0, otherwise penalty
                        objective_terms.append((1 - X[(e_id, prev_slot, prev_room)]) * weight_reassign)

        # S7: Undesirable sessions (e.g. evening)
        weight_undesirable = self.weights.get("undesirable", 80)
        if weight_undesirable > 0:
            for slot in valid_slots:
                if slot.get("period", "").lower() == "evening":
                    s_id = slot["id"]
                    for exam in self.exams:
                        e_id = exam["id"]
                        if (e_id, s_id) in Y:
                            objective_terms.append(Y[(e_id, s_id)] * weight_undesirable)

        # S3 / S8: Daily load balance across exam dates
        weight_imbalance = self.weights.get("imbalance", 60)
        if weight_imbalance > 0 and len(slots_by_date) > 1:
            ideal_daily = len(self.exams) // len(slots_by_date)
            for d_str, slot_ids in slots_by_date.items():
                day_vars = [Y[(e_id, s_id)] for e_id in self.exam_map.keys() for s_id in slot_ids if (e_id, s_id) in Y]
                if day_vars:
                    diff_var = model.NewIntVar(-len(self.exams), len(self.exams), f"day_dev_{d_str}")
                    model.Add(diff_var == sum(day_vars) - ideal_daily)
                    abs_diff = model.NewIntVar(0, len(self.exams), f"abs_day_dev_{d_str}")
                    model.AddAbsEquality(abs_diff, diff_var)
                    objective_terms.append(abs_diff * weight_imbalance)

        # Set objective
        if objective_terms:
            model.Minimize(sum(objective_terms))

        # Step 4: Solver Configuration
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(self.time_limit_seconds)
        solver.parameters.num_workers = 4
        solver.parameters.random_seed = 42

        # Variable order heuristic: prioritize heavily constrained exams
        decision_vars = []
        ordered_exams = self.conflict_graph.degree_ordered_exams()
        for e_id in ordered_exams:
            for (s_id, r_id) in candidates_per_exam[e_id]:
                if (e_id, s_id, r_id) in X:
                    decision_vars.append(X[(e_id, s_id, r_id)])
        if decision_vars:
            model.AddDecisionStrategy(
                decision_vars,
                cp_model.CHOOSE_FIRST,
                cp_model.SELECT_MAX_VALUE
            )

        # Step 5: Solve
        status = solver.Solve(model)
        elapsed_ms = (time.time() - start_time) * 1000.0

        # Handle all solver statuses strictly per Section 7:
        # OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN, MODEL_INVALID
        status_map = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.UNKNOWN: "UNKNOWN",
            cp_model.MODEL_INVALID: "MODEL_INVALID"
        }
        solver_status_str = status_map.get(status, "UNKNOWN")

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            # No solution found
            diagnostics = diagnostics_checker.diagnose_all()
            if not diagnostics:
                diagnostics.append({
                    "type": "SOLVER_INFEASIBLE_GLOBAL",
                    "severity": "FATAL",
                    "title": "Constraint System Infeasible",
                    "message": "The solver concluded that the combination of student clashes, room capacities, and time slots cannot all be simultaneously satisfied.",
                    "corrective_action": "Add more time slots, expand room capacities, or unlock conflicting examinations."
                })

            return {
                "solver_status": solver_status_str,
                "solver_runtime_ms": round(elapsed_ms, 2),
                "assignments": [],
                "diagnostics": diagnostics,
                "is_feasible": False,
                "is_complete": False,
                "quality_score": 0.0,
                "objective_cost": 999999.0,
                "metrics": {},
                "validation": {
                    "is_feasible": False,
                    "is_complete": False,
                    "hard_constraint_violations_count": len(diagnostics),
                    "violations": [
                        {
                            "rule": "H-SOLVER",
                            "severity": "CRITICAL",
                            "title": d.get("title", "Infeasible"),
                            "description": d.get("message", "Model constraints cannot all be satisfied."),
                            "suggested_action": d.get("corrective_action", "Adjust constraints.")
                        } for d in diagnostics
                    ],
                    "summary": f"Solver finished with status {solver_status_str}."
                }
            }

        # Step 6: Extract assignments
        final_assignments = []
        for exam in self.exams:
            e_id = exam["id"]
            assigned_slot = None
            assigned_room = None
            for (s_id, r_id) in candidates_per_exam[e_id]:
                if solver.Value(X[(e_id, s_id, r_id)]) == 1:
                    assigned_slot = s_id
                    assigned_room = r_id
                    break

            enrolled_count = len(self.enrollments.get(e_id, set()))
            final_assignments.append({
                "exam_id": e_id,
                "timeslot_id": assigned_slot,
                "room_id": assigned_room,
                "assigned_student_count": enrolled_count,
                "is_locked": e_id in self.locked_assignments,
                "source": "AUTOMATIC",
                "validation_status": "VALID" if (assigned_slot and assigned_room) else "UNSCHEDULED",
                "conflict_reasons": []
            })

        # Step 7: Independent Validation
        validator = TimetableValidator(
            exams=self.exams,
            rooms=self.rooms,
            timeslots=self.timeslots,
            enrollments=self.enrollments,
            assignments=final_assignments,
            locked_assignments=self.locked_assignments,
            students=self.students
        )
        val_result = validator.validate()

        # Step 8: Calculate Quality Metrics
        metrics_calc = QualityMetricsCalculator(
            exams=self.exams,
            rooms=self.rooms,
            timeslots=self.timeslots,
            enrollments=self.enrollments,
            assignments=final_assignments,
            previous_assignments=self.previous_assignments,
            weights=self.weights
        )
        computed_metrics = metrics_calc.compute()

        # If independent validation found violations, mark status as CONFLICT / INFEASIBLE
        if not val_result.is_feasible:
            solver_status_str = "FEASIBLE_WITH_VIOLATIONS"
            computed_metrics["quality_score"] = 0.0

        return {
            "solver_status": solver_status_str,
            "solver_runtime_ms": round(elapsed_ms, 2),
            "assignments": final_assignments,
            "diagnostics": [],
            "is_feasible": val_result.is_feasible,
            "is_complete": val_result.is_complete,
            "quality_score": computed_metrics["quality_score"],
            "objective_cost": computed_metrics["total_objective_cost"],
            "metrics": computed_metrics,
            "validation": val_result.model_dump()
        }
