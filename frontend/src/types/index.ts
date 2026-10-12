export interface Exam {
  id: number;
  exam_code: string;
  course_code: string;
  course_name: string;
  department: string;
  semester: string;
  academic_year: string;
  duration_minutes: number;
  exam_type: string;
  required_features: string[];
  eligible_slot_ids: number[];
  preferred_slot_ids: number[];
  priority: number;
  is_locked: boolean;
  notes?: string;
  enrollment_count: number;
  enrolled_student_ids: number[];
}

export interface Student {
  id: number;
  student_id: string;
  name: string;
  department: string;
  semester: string;
  special_accommodations: string[];
  enrolled_exam_ids: number[];
}

export interface StudentTimetableItem {
  exam_code: string;
  course_code: string;
  course_name: string;
  date: string;
  start_time: string;
  end_time: string;
  room_code: string;
  room_name: string;
  building: string;
  is_locked: boolean;
}

export interface Room {
  id: number;
  room_code: string;
  name: string;
  building: string;
  capacity: number;
  is_available: boolean;
  features: string[];
  accessibility_features: string[];
  blackout_intervals: { date?: string; reason?: string }[];
}

export interface TimeSlot {
  id: number;
  slot_code: string;
  date: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  period: string;
  is_available: boolean;
  is_blackout: boolean;
  blackout_reason?: string;
}

export interface Assignment {
  id: number;
  timetable_id: number;
  exam_id: number;
  exam_code: string;
  course_code: string;
  course_name: string;
  department: string;
  duration_minutes: number;
  timeslot_id: number | null;
  slot_code: string | null;
  date: string | null;
  start_time: string | null;
  end_time: string | null;
  period: string | null;
  room_id: number | null;
  room_code: string | null;
  room_name: string | null;
  building: string | null;
  room_capacity: number | null;
  assigned_student_count: number;
  is_locked: boolean;
  source: string;
  validation_status: string;
  conflict_reasons: string[];
  updated_at: string;
}

export interface TimetableVersion {
  id: number;
  version_number: number;
  name: string;
  is_active: boolean;
  solver_status: string;
  solver_runtime_ms: number;
  quality_score: number;
  objective_cost: number;
  metrics: Record<string, any>;
  diagnostics: any[];
  created_by: string;
  notes?: string;
  created_at: string;
  total_assignments: number;
  scheduled_count: number;
  unscheduled_count: number;
}

export interface DashboardSummary {
  total_exams: number;
  total_students: number;
  available_rooms: number;
  available_timeslots: number;
  scheduled_exams: number;
  unscheduled_exams: number;
  student_clash_count: number;
  room_clash_count: number;
  capacity_violation_count: number;
  locked_exam_count: number;
  quality_score: number;
  solver_status: string;
  active_version_id?: number;
  active_version_name?: string;
  last_optimized_at?: string;
  is_valid_timetable: boolean;
}

export interface ConflictItem {
  source: string;
  rule: string;
  severity: string;
  title: string;
  description: string;
  exam_code?: string;
  related_exam_code?: string;
  room_code?: string;
  date?: string;
  affected_students_count: number;
  suggested_action: string;
}

export interface ConflictResponse {
  is_feasible: boolean;
  is_complete: boolean;
  total_conflicts: number;
  hard_violations_count: number;
  conflicts: ConflictItem[];
}

export interface BaselineComparisonItem {
  metric_key: string;
  metric_label: string;
  baseline_value: number;
  current_value: number;
  absolute_diff: number;
  percentage_change?: number;
  is_improvement: boolean;
}

export interface BaselineComparisonResponse {
  baseline_version_id: number;
  baseline_version_name: string;
  current_version_id: number;
  current_version_name: string;
  comparisons: BaselineComparisonItem[];
}

export interface GenerateParams {
  name?: string;
  time_limit_seconds: number;
  mode: 'full' | 'minimal_change';
  study_interval_days?: number;
  weight_student_burden?: number;
  weight_exam_spacing?: number;
  weight_daily_imbalance?: number;
  weight_preference_violation?: number;
  weight_room_utilization?: number;
  weight_unnecessary_changes?: number;
  weight_undesirable_session?: number;
}

export interface StudentExamSeating {
  exam_id: number;
  exam_code: string;
  course_code: string;
  course_name: string;
  date: string;
  day_name?: string;
  start_time: string;
  end_time: string;
  period?: string;
  room_code: string;
  room_name: string;
  building: string;
  room_capacity?: number;
  seat_number: string;
  is_locked: boolean;
}

export interface StudentSeatingResponse {
  id: number;
  student_id: string;
  name: string;
  department: string;
  semester: string;
  special_accommodations: string[];
  subjects_count: number;
  distinct_halls_count: number;
  exams: StudentExamSeating[];
}

export interface DepartmentSeatingSummary {
  department: string;
  students_count: number;
  total_sittings: number;
  distinct_exams_count: number;
}

export interface BacklogRecord {
  id: number;
  student_code: string;
  student_name: string;
  department: string;
  student_type: string;
  current_semester: string;
  backlog_semester: string;
  semester_type: string;
  course_code: string;
  course_name: string;
  exam_date: string;
  exam_day: string;
  start_time: string;
  end_time: string;
  period: string;
  room_code: string;
  room_name: string;
  seat_number: string;
  status: string;
  created_at?: string;
}

export interface BacklogCreateInput {
  student_code: string;
  student_name: string;
  department: string;
  student_type?: string;
  current_semester: string;
  backlog_semester: string;
  semester_type?: string;
  course_code: string;
  course_name: string;
  exam_date?: string;
  exam_day?: string;
  start_time?: string;
  end_time?: string;
  period?: string;
  room_code?: string;
  room_name?: string;
  seat_number?: string;
}

export interface BacklogSummary {
  total_backlogs: number;
  old_students_count: number;
  new_students_count: number;
  odd_sem_backlogs_count: number;
  even_sem_backlogs_count: number;
  weekend_sessions_count: number;
  venues_allocated_count: number;
  department_counts?: Record<string, number>;
  active_department?: string;
  is_pre_optimization?: boolean;
}


