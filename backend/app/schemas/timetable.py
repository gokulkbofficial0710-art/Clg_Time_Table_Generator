from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    timetable_id: int
    exam_id: int
    exam_code: str
    course_code: str
    course_name: str
    department: str
    duration_minutes: int
    timeslot_id: Optional[int] = None
    slot_code: Optional[str] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    period: Optional[str] = None
    room_id: Optional[int] = None
    room_code: Optional[str] = None
    room_name: Optional[str] = None
    building: Optional[str] = None
    room_capacity: Optional[int] = None
    assigned_student_count: int
    is_locked: bool
    source: str # AUTOMATIC or MANUAL
    validation_status: str # VALID, CONFLICT, UNSCHEDULED
    conflict_reasons: List[str] = Field(default_factory=list)
    updated_at: datetime

class VersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    version_number: int
    name: str
    is_active: bool
    solver_status: str
    solver_runtime_ms: float
    quality_score: float
    objective_cost: float
    metrics: Dict[str, Any]
    diagnostics: List[Dict[str, Any]] = Field(default_factory=list)
    created_by: str
    notes: Optional[str] = None
    created_at: datetime
    total_assignments: int = 0
    scheduled_count: int = 0
    unscheduled_count: int = 0

class GenerateRequest(BaseModel):
    name: Optional[str] = None
    time_limit_seconds: int = Field(30, ge=1, le=300)
    mode: str = Field("full", description="full or minimal_change")
    study_interval_days: Optional[int] = Field(1, ge=0, le=7, description="Number of mandatory revision/study holiday days between consecutive exam days")
    weight_student_burden: Optional[int] = Field(None, ge=0, le=1000)
    weight_exam_spacing: Optional[int] = Field(None, ge=0, le=1000)
    weight_daily_imbalance: Optional[int] = Field(None, ge=0, le=1000)
    weight_preference_violation: Optional[int] = Field(None, ge=0, le=1000)
    weight_room_utilization: Optional[int] = Field(None, ge=0, le=1000)
    weight_unnecessary_changes: Optional[int] = Field(None, ge=0, le=1000)
    weight_undesirable_session: Optional[int] = Field(None, ge=0, le=1000)

class ReoptimizeRequest(GenerateRequest):
    mode: str = Field("minimal_change", description="minimal_change or full")
    base_version_id: Optional[int] = None

class ManualAssignmentEditRequest(BaseModel):
    timeslot_id: Optional[int] = None
    room_id: Optional[int] = None
    is_locked: Optional[bool] = None
    force_apply: bool = False # If false, rejects on hard constraint violation

class ConflictViolation(BaseModel):
    rule: str # H1 to H9
    severity: str # CRITICAL, WARNING
    title: str
    description: str
    exam_id: Optional[int] = None
    exam_code: Optional[str] = None
    related_exam_code: Optional[str] = None
    room_id: Optional[int] = None
    room_code: Optional[str] = None
    timeslot_id: Optional[int] = None
    date: Optional[str] = None
    affected_students_count: int = 0
    affected_student_ids: List[str] = Field(default_factory=list)
    suggested_action: str

class ValidationResult(BaseModel):
    is_feasible: bool
    is_complete: bool
    hard_constraint_violations_count: int
    violations: List[ConflictViolation]
    summary: str

class BaselineComparisonItem(BaseModel):
    metric_key: str
    metric_label: str
    baseline_value: float
    current_value: float
    absolute_diff: float
    percentage_change: Optional[float] = None
    is_improvement: bool

class BaselineComparisonResponse(BaseModel):
    baseline_version_id: int
    baseline_version_name: str
    current_version_id: int
    current_version_name: str
    comparisons: List[BaselineComparisonItem]
