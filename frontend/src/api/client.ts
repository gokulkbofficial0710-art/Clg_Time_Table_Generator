import {
  Exam, Student, Room, TimeSlot, Assignment, TimetableVersion,
  DashboardSummary, ConflictResponse, BaselineComparisonResponse,
  GenerateParams, StudentTimetableItem, StudentSeatingResponse, DepartmentSeatingSummary,
  BacklogRecord, BacklogCreateInput, BacklogSummary
} from '../types';

const BASE_URL = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    let errMessage = `HTTP error ${res.status}`;
    try {
      const errData = await res.json();
      errMessage = errData.detail || errData.message || errMessage;
    } catch {
      // ignore
    }
    throw new Error(errMessage);
  }

  return res.json();
}

export const api = {
  // Dashboard & Analytics
  getDashboard: () => fetchJson<DashboardSummary>('/analytics/dashboard'),
  getDistributions: () => fetchJson<any>('/analytics/distributions'),

  // Examinations
  getExams: (params?: { department?: string; is_locked?: boolean; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.department) q.append('department', params.department);
    if (params?.is_locked !== undefined) q.append('is_locked', String(params.is_locked));
    if (params?.search) q.append('search', params.search);
    return fetchJson<Exam[]>(`/exams?${q.toString()}`);
  },
  getExam: (id: number) => fetchJson<Exam>(`/exams/${id}`),
  createExam: (data: Partial<Exam>) => fetchJson<Exam>('/exams', { method: 'POST', body: JSON.stringify(data) }),
  updateExam: (id: number, data: Partial<Exam>) => fetchJson<Exam>(`/exams/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteExam: (id: number) => fetchJson<{ message: string }>(`/exams/${id}`, { method: 'DELETE' }),
  toggleExamLock: (id: number, lock?: boolean) => {
    const q = lock !== undefined ? `?lock=${lock}` : '';
    return fetchJson<{ message: string }>(`/exams/${id}/lock${q}`, { method: 'PATCH' });
  },
  getExamStudents: (id: number) => fetchJson<Student[]>(`/exams/${id}/students`),

  // Students
  getStudents: (params?: { department?: string; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.department) q.append('department', params.department);
    if (params?.search) q.append('search', params.search);
    return fetchJson<Student[]>(`/students?${q.toString()}`);
  },
  getStudent: (id: number) => fetchJson<Student>(`/students/${id}`),
  createStudent: (data: Partial<Student>) => fetchJson<Student>('/students', { method: 'POST', body: JSON.stringify(data) }),
  updateStudent: (id: number, data: Partial<Student>) => fetchJson<Student>(`/students/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteStudent: (id: number) => fetchJson<{ message: string }>(`/students/${id}`, { method: 'DELETE' }),
  getStudentTimetable: (id: number) => fetchJson<StudentTimetableItem[]>(`/students/${id}/timetable`),

  // Rooms
  getRooms: () => fetchJson<Room[]>('/rooms'),
  getRoom: (id: number) => fetchJson<Room>(`/rooms/${id}`),
  createRoom: (data: Partial<Room>) => fetchJson<Room>('/rooms', { method: 'POST', body: JSON.stringify(data) }),
  updateRoom: (id: number, data: Partial<Room>) => fetchJson<Room>(`/rooms/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteRoom: (id: number) => fetchJson<{ message: string }>(`/rooms/${id}`, { method: 'DELETE' }),
  getRoomOccupancy: (id: number) => fetchJson<any>(`/rooms/${id}/occupancy`),

  // Time Slots
  getTimeSlots: () => fetchJson<TimeSlot[]>('/time-slots'),
  getTimeSlot: (id: number) => fetchJson<TimeSlot>(`/time-slots/${id}`),
  createTimeSlot: (data: Partial<TimeSlot>) => fetchJson<TimeSlot>('/time-slots', { method: 'POST', body: JSON.stringify(data) }),
  updateTimeSlot: (id: number, data: Partial<TimeSlot>) => fetchJson<TimeSlot>(`/time-slots/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteTimeSlot: (id: number) => fetchJson<{ message: string }>(`/time-slots/${id}`, { method: 'DELETE' }),

  // Timetable & Optimization
  getTimetable: (params?: { version_id?: number; department?: string; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.version_id) q.append('version_id', String(params.version_id));
    if (params?.department) q.append('department', params.department);
    if (params?.search) q.append('search', params.search);
    return fetchJson<Assignment[]>(`/timetable?${q.toString()}`);
  },
  generateTimetable: (params: GenerateParams) => fetchJson<any>('/timetable/generate', { method: 'POST', body: JSON.stringify(params) }),
  reoptimizeTimetable: (params: GenerateParams) => fetchJson<any>('/timetable/reoptimize', { method: 'POST', body: JSON.stringify(params) }),
  applyStudyInterval: (intervalDays: number) => fetchJson<any>(`/timetable/apply-interval?interval_days=${intervalDays}`, { method: 'POST' }),
  validateTimetable: (version_id?: number) => {
    const q = version_id ? `?version_id=${version_id}` : '';
    return fetchJson<any>(`/timetable/validate${q}`, { method: 'POST' });
  },
  updateAssignment: (id: number, data: { timeslot_id?: number | null; room_id?: number | null; is_locked?: boolean; force_apply?: boolean }) =>
    fetchJson<Assignment>(`/timetable/assignments/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  toggleAssignmentLock: (id: number, lock?: boolean) => {
    const q = lock !== undefined ? `?lock=${lock}` : '';
    return fetchJson<any>(`/timetable/assignments/${id}/lock${q}`, { method: 'PATCH' });
  },
  getVersions: () => fetchJson<TimetableVersion[]>('/timetable/versions'),
  restoreVersion: (id: number) => fetchJson<{ message: string }>(`/timetable/restore/${id}`, { method: 'POST' }),
  compareVersions: (baselineId?: number, currentId?: number) => {
    const q = new URLSearchParams();
    if (baselineId) q.append('baseline_id', String(baselineId));
    if (currentId) q.append('current_id', String(currentId));
    return fetchJson<BaselineComparisonResponse>(`/timetable/compare?${q.toString()}`);
  },

  // Conflicts
  getConflicts: (params?: { severity?: string; rule?: string }) => {
    const q = new URLSearchParams();
    if (params?.severity) q.append('severity', params.severity);
    if (params?.rule) q.append('rule', params.rule);
    return fetchJson<ConflictResponse>(`/conflicts?${q.toString()}`);
  },
  autoResolveConflicts: () => fetchJson<any>('/conflicts/auto-resolve', { method: 'POST' }),

  // Demo Data & Infeasible Scenario
  loadDemoData: (includeInfeasible?: boolean) => {
    const q = includeInfeasible ? '?include_infeasible=true' : '';
    return fetchJson<{ message: string }>(`/data/load-demo${q}`, { method: 'POST' });
  },
  loadInfeasibleScenario: () => fetchJson<{ message: string }>('/data/load-infeasible', { method: 'POST' }),
  resetInfeasibleScenario: () => fetchJson<{ message: string }>('/data/reset-infeasible', { method: 'POST' }),

  // Import / Export
  previewImport: async (entityType: string, file: File) => {
    const formData = new FormData();
    formData.append('entity_type', entityType);
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/import/preview`, { method: 'POST', body: formData });
    if (!res.ok) throw new Error('Failed to preview import');
    return res.json();
  },
  commitImport: (entityType: string, items: any[], overwrite = false) =>
    fetchJson<{ message: string }>('/import/commit', {
      method: 'POST',
      body: JSON.stringify({ entity_type: entityType, items, overwrite_existing: overwrite }),
    }),

  // Student Seatings & Hall Allocations
  getStudentSeatings: (params?: { department?: string; search?: string; version_id?: number }) => {
    const q = new URLSearchParams();
    if (params?.department && params.department !== 'ALL') q.append('department', params.department);
    if (params?.search) q.append('search', params.search);
    if (params?.version_id) q.append('version_id', String(params.version_id));
    return fetchJson<StudentSeatingResponse[]>(`/students/seatings?${q.toString()}`);
  },
  getDepartmentSeatingSummaries: (version_id?: number) => {
    const q = version_id ? `?version_id=${version_id}` : '';
    return fetchJson<DepartmentSeatingSummary[]>(`/students/seatings/departments${q}`);
  },
  getDepartmentSeatingPdfUrl: (department?: string, version_id?: number) => {
    const q = new URLSearchParams();
    if (department && department !== 'ALL') q.append('department', department);
    if (version_id) q.append('version_id', String(version_id));
    return `${BASE_URL}/export/students/seatings/pdf?${q.toString()}`;
  },
  getStudentHallTicketPdfUrl: (studentId: number, version_id?: number) => {
    const q = version_id ? `?version_id=${version_id}` : '';
    return `${BASE_URL}/export/students/${studentId}/hall-ticket/pdf${q}`;
  },
  getDepartmentSeatingCsvUrl: (department?: string, version_id?: number) => {
    const q = new URLSearchParams();
    if (department && department !== 'ALL') q.append('department', department);
    if (version_id) q.append('version_id', String(version_id));
    return `${BASE_URL}/export/students/seatings/csv?${q.toString()}`;
  },

  // Backlogs & Arrears Examination Registry (Weekend Sessions)
  getBacklogs: (params?: {
    department?: string;
    student_type?: string;
    semester_type?: string;
    current_semester?: string;
    search?: string;
  }) => {
    const q = new URLSearchParams();
    if (params?.department && params.department !== 'ALL') q.append('department', params.department);
    if (params?.student_type && params.student_type !== 'ALL') q.append('student_type', params.student_type);
    if (params?.semester_type && params.semester_type !== 'ALL') q.append('semester_type', params.semester_type);
    if (params?.current_semester && params.current_semester !== 'ALL') q.append('current_semester', params.current_semester);
    if (params?.search) q.append('search', params.search);
    return fetchJson<BacklogRecord[]>(`/backlogs?${q.toString()}`);
  },
  createBacklog: (data: BacklogCreateInput) =>
    fetchJson<BacklogRecord>('/backlogs', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  deleteBacklog: (id: number) =>
    fetchJson<{ message: string; id: number }>(`/backlogs/${id}`, {
      method: 'DELETE',
    }),
  getBacklogSummary: (department?: string) => {
    const q = department && department !== 'ALL' ? `?department=${encodeURIComponent(department)}` : '';
    return fetchJson<BacklogSummary>(`/backlogs/summary${q}`);
  },
  getBacklogAdmitCardPdfUrl: (id: number) => `${BASE_URL}/backlogs/${id}/admit-card/pdf`,
  getBacklogPdfUrl: (params?: { department?: string; student_type?: string }) => {
    const q = new URLSearchParams();
    if (params?.department && params.department !== 'ALL') q.append('department', params.department);
    if (params?.student_type && params.student_type !== 'ALL') q.append('student_type', params.student_type);
    return `${BASE_URL}/backlogs/export/pdf?${q.toString()}`;
  },
  getBacklogCsvUrl: (params?: { department?: string; student_type?: string }) => {
    const q = new URLSearchParams();
    if (params?.department && params.department !== 'ALL') q.append('department', params.department);
    if (params?.student_type && params.student_type !== 'ALL') q.append('student_type', params.student_type);
    return `${BASE_URL}/backlogs/export/csv?${q.toString()}`;
  },
};
