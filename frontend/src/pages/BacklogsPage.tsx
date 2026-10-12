import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { BacklogRecord, BacklogCreateInput } from '../types';
import {
  History, Plus, Search, FileDown, FileText, Trash2,
  Calendar, Clock, Building2, Printer, AlertCircle,
  CheckCircle2, Filter, X, Users, CalendarCheck
} from 'lucide-react';

export const BacklogsPage: React.FC = () => {
  const queryClient = useQueryClient();

  // Filters & Search
  const [selectedDept, setSelectedDept] = useState<string>('ALL');
  const [semTypeFilter, setSemTypeFilter] = useState<string>('ALL');
  const [currentSemFilter, setCurrentSemFilter] = useState<string>('ALL');
  const [search, setSearch] = useState<string>('');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  // Form State
  const [formData, setFormData] = useState<BacklogCreateInput>({
    student_code: '',
    student_name: '',
    department: 'Computer Science',
    student_type: 'Old Student',
    current_semester: 'Semester 3',
    backlog_semester: 'Semester 1',
    semester_type: 'Odd Semester',
    course_code: 'MA101',
    course_name: 'Calculus I & Analytical Geometry',
    exam_date: '2026-12-19',
    exam_day: 'Saturday',
    start_time: '09:30:00',
    end_time: '12:30:00',
    period: 'Morning',
    room_code: 'AUD-MAIN',
    room_name: 'Grand University Auditorium',
    seat_number: '',
  });

  // 0. Dashboard query for pre-optimization state check
  const { data: dashboard } = useQuery({
    queryKey: ['dashboard'],
    queryFn: api.getDashboard,
  });

  const isPreOptimization = dashboard ? dashboard.quality_score === 0 : false;

  // 1. Queries for Backlog records
  const { data: backlogs = [], isLoading, isFetching } = useQuery<BacklogRecord[]>({
    queryKey: ['backlogs', selectedDept, semTypeFilter, currentSemFilter, search],
    queryFn: () => api.getBacklogs({
      department: selectedDept !== 'ALL' ? selectedDept : undefined,
      semester_type: semTypeFilter !== 'ALL' ? semTypeFilter : undefined,
      current_semester: currentSemFilter !== 'ALL' ? currentSemFilter : undefined,
      search: search.trim() || undefined,
    }),
  });

  // 2. Department-specific summary query
  const { data: summary } = useQuery({
    queryKey: ['backlog-summary', selectedDept],
    queryFn: () => api.getBacklogSummary(selectedDept !== 'ALL' ? selectedDept : undefined),
  });

  // 3. Overall summary for all department counters
  const { data: overallSummary } = useQuery({
    queryKey: ['backlog-summary-overall'],
    queryFn: () => api.getBacklogSummary(),
  });

  const { data: registeredStudents = [] } = useQuery({
    queryKey: ['students-quick-list'],
    queryFn: () => api.getStudents(),
  });

  const { data: registeredExams = [] } = useQuery({
    queryKey: ['exams-quick-list'],
    queryFn: () => api.getExams(),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (data: BacklogCreateInput) => api.createBacklog(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backlogs'] });
      queryClient.invalidateQueries({ queryKey: ['backlog-summary'] });
      queryClient.invalidateQueries({ queryKey: ['backlog-summary-overall'] });
      setIsModalOpen(false);
      // Reset form
      setFormData({
        student_code: '',
        student_name: '',
        department: 'Computer Science',
        student_type: 'Old Student',
        current_semester: 'Semester 3',
        backlog_semester: 'Semester 1',
        semester_type: 'Odd Semester',
        course_code: 'MA101',
        course_name: 'Calculus I & Analytical Geometry',
        exam_date: '2026-12-19',
        exam_day: 'Saturday',
        start_time: '09:30:00',
        end_time: '12:30:00',
        period: 'Morning',
        room_code: 'AUD-MAIN',
        room_name: 'Grand University Auditorium',
        seat_number: '',
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteBacklog(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backlogs'] });
      queryClient.invalidateQueries({ queryKey: ['backlog-summary'] });
      queryClient.invalidateQueries({ queryKey: ['backlog-summary-overall'] });
    },
  });

  // Handlers
  const handleStudentSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const sId = e.target.value;
    const found = registeredStudents.find(s => s.student_id === sId);
    if (found) {
      setFormData(prev => ({
        ...prev,
        student_code: found.student_id,
        student_name: found.name,
        department: found.department,
        current_semester: 'Semester 3',
      }));
    }
  };

  const handleCourseSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const cCode = e.target.value;
    const found = registeredExams.find(ex => ex.course_code === cCode);
    if (found) {
      setFormData(prev => ({
        ...prev,
        course_code: found.course_code,
        course_name: found.course_name,
      }));
    }
  };

  const handleBacklogSemesterChange = (val: string) => {
    const isOdd = ['Semester 1', 'Semester 3', 'Semester 5', 'Semester 7'].includes(val);
    setFormData(prev => ({
      ...prev,
      backlog_semester: val,
      semester_type: isOdd ? 'Odd Semester' : 'Even Semester',
    }));
  };

  const handleWeekendSlotChange = (slotKey: string) => {
    if (slotKey === 'SAT_M') {
      setFormData(prev => ({ ...prev, exam_date: '2026-12-19', exam_day: 'Saturday', start_time: '09:30:00', end_time: '12:30:00', period: 'Morning' }));
    } else {
      setFormData(prev => ({ ...prev, exam_date: '2026-12-19', exam_day: 'Saturday', start_time: '14:00:00', end_time: '17:00:00', period: 'Afternoon' }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.student_code || !formData.student_name || !formData.course_code) {
      alert('Please fill in candidate details and course code.');
      return;
    }
    createMutation.mutate(formData);
  };

  const pdfExportUrl = api.getBacklogPdfUrl({
    department: selectedDept !== 'ALL' ? selectedDept : undefined,
  });

  const csvExportUrl = api.getBacklogCsvUrl({
    department: selectedDept !== 'ALL' ? selectedDept : undefined,
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Pre-Optimization Notice Banner */}
      {isPreOptimization && (
        <div className="p-4 rounded-xl border border-amber-200 bg-amber-50 text-amber-950 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-amber-100 text-amber-700 shrink-0 mt-0.5">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Pre-Optimization State — Backlog & Arrears Ledger Cleared (Quality: 0%)
              </h3>
              <p className="text-xs text-slate-600 mt-0.5">
                The active timetable is in draft pre-optimization baseline state. Individual candidate weekend arrears allocations, halls, desk numbers, and admit cards are generated upon extracting the optimized timetable.
              </p>
            </div>
          </div>
          <Link
            to="/optimizer"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition shrink-0"
          >
            <CalendarCheck className="w-3.5 h-3.5 text-indigo-200" />
            Extract Optimized Timetable
          </Link>
        </div>
      )}

      {/* 1. Header Card */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white border border-slate-200 p-5 rounded-xl shadow-xs">
        <div className="flex items-center gap-3">
          <span className="p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-amber-700">
            <History className="w-5 h-5" />
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                Backlog & Arrears Examination Registry
              </h1>
              <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-amber-50 text-amber-800 border border-amber-200 uppercase">
                Saturday Sessions Only
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Special Saturday exam schedule for candidates carrying Odd/Even semester backlogs (Sundays Off)
            </p>
          </div>
        </div>

        {/* Header Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors shadow-xs cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Register Backlog Candidate
          </button>

          {isPreOptimization ? (
            <span
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-400 bg-slate-50 border border-slate-200 rounded-lg cursor-not-allowed shadow-2xs"
              title="Backlogs are cleared in pre-optimization state. Extract timetable to export."
            >
              <FileText className="w-3.5 h-3.5 text-slate-400" />
              Export CSV (Pending)
            </span>
          ) : (
            <a
              href={csvExportUrl}
              download
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-2xs"
              title="Export CSV Backlogs Ledger"
            >
              <FileText className="w-3.5 h-3.5 text-slate-500" />
              Export CSV
            </a>
          )}

          {isPreOptimization ? (
            <span
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-400 bg-slate-100 border border-slate-200 rounded-lg cursor-not-allowed shadow-xs"
              title="Backlogs are cleared in pre-optimization state. Extract timetable to export."
            >
              <FileDown className="w-4 h-4 text-slate-400" />
              Export Schedule PDF (Pending)
            </span>
          ) : (
            <a
              href={pdfExportUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors shadow-xs"
              title="Download Official Saturday Backlog Timetable PDF"
            >
              <FileDown className="w-4 h-4 text-slate-300" />
              Export Schedule PDF ({selectedDept === 'ALL' ? 'All' : selectedDept})
            </a>
          )}
        </div>
      </div>

      {/* 2. Institutional Regulation / Policy Banner */}
      <div className="bg-amber-50/80 border border-amber-200 rounded-xl p-4 flex items-start gap-3 text-xs text-amber-950">
        <div className="p-1.5 rounded-md bg-amber-100 text-amber-800 shrink-0 mt-0.5">
          <AlertCircle className="w-4 h-4" />
        </div>
        <div>
          <span className="font-bold">Academic Regulation on Backlogs & Saturday Exam Timings:</span>
          <p className="mt-0.5 text-amber-900 leading-relaxed text-[11px]">
            Regular semester cohorts appear for their current semester exams during official weekdays (Monday to Thursday).
            Students studying in higher semesters (e.g. <strong>Semester 3 or 5</strong>) with backlogs from earlier semesters
            (e.g. <strong>Semester 1</strong> odd semester backlog) are scheduled exclusively on <strong>Saturday Sessions (Saturday Dec 19 — Sundays are off)</strong>.
            This ensures zero clashing between a student's regular curriculum papers and backlog re-examinations.
          </p>
        </div>
      </div>

      {/* 3. Department Selector Tabs (Department-wise Counts) */}
      <div className="bg-white border border-slate-200 p-3 rounded-xl shadow-xs">
        <div className="flex items-center justify-between mb-2 px-1">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <Filter className="w-3 h-3 text-slate-400" />
            Academic Department Rosters
          </span>
          <span className="text-[11px] text-slate-500 font-mono">
            Active: <strong className="text-slate-800">{selectedDept === 'ALL' ? 'All Academic Departments' : selectedDept}</strong>
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {/* ALL Button */}
          <button
            onClick={() => setSelectedDept('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-2 cursor-pointer ${
              selectedDept === 'ALL'
                ? 'bg-slate-900 text-white shadow-xs font-semibold'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200/80 border border-slate-200'
            }`}
          >
            <span>All Departments</span>
            <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
              selectedDept === 'ALL' ? 'bg-slate-700 text-white' : 'bg-slate-200 text-slate-700 font-mono'
            }`}>
              {overallSummary?.total_backlogs ?? 0}
            </span>
          </button>

          {/* Department Specific Tabs */}
          {['Computer Science', 'Mathematics', 'Physics', 'Electrical Eng', 'Business'].map((dept) => {
            const isSelected = selectedDept === dept;
            const count = overallSummary?.department_counts?.[dept] ?? 0;
            return (
              <button
                key={dept}
                onClick={() => setSelectedDept(dept)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-2 cursor-pointer ${
                  isSelected
                    ? 'bg-indigo-700 text-white shadow-xs font-semibold'
                    : 'bg-slate-50 text-slate-700 hover:bg-slate-100 border border-slate-200'
                }`}
              >
                <span>{dept}</span>
                <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                  isSelected ? 'bg-indigo-900 text-indigo-100' : 'bg-slate-200 text-slate-600 font-mono'
                }`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. KPI Metrics Strip (Department Sensitive) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white border border-slate-200 p-3.5 rounded-xl shadow-xs">
          <div className="text-[11px] text-slate-500 font-medium">
            {selectedDept === 'ALL' ? 'Total Backlog Candidates' : `${selectedDept} Candidates`}
          </div>
          <div className="text-xl font-bold text-slate-900 mt-0.5">
            {summary?.total_backlogs ?? 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
            <Users className="w-3 h-3 text-indigo-600" />
            {selectedDept === 'ALL' ? 'Across All 5 Departments' : `Students in ${selectedDept}`}
          </div>
        </div>

        <div className="bg-white border border-slate-200 p-3.5 rounded-xl shadow-xs">
          <div className="text-[11px] text-slate-500 font-medium">Odd Sem Backlogs (Saturday)</div>
          <div className="text-xl font-bold text-emerald-700 mt-0.5">
            {summary?.odd_sem_backlogs_count ?? 0}
          </div>
          <div className="text-[10px] text-emerald-600 mt-1 flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            Saturday special slots (Sundays Off)
          </div>
        </div>

        <div className="bg-white border border-slate-200 p-3.5 rounded-xl shadow-xs">
          <div className="text-[11px] text-slate-500 font-medium">Saturday Exam Sessions</div>
          <div className="text-xl font-bold text-amber-700 mt-0.5">
            {summary?.weekend_sessions_count ?? 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
            <Clock className="w-3 h-3 text-amber-600" />
            Morning & Afternoon (Sundays Off)
          </div>
        </div>

        <div className="bg-white border border-slate-200 p-3.5 rounded-xl shadow-xs">
          <div className="text-[11px] text-slate-500 font-medium">Allocated Venues & Halls</div>
          <div className="text-xl font-bold text-purple-700 mt-0.5">
            {summary?.venues_allocated_count ?? 0}
          </div>
          <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
            <Building2 className="w-3 h-3 text-purple-600" />
            AUD-MAIN, HALL-101, LAB-COMP
          </div>
        </div>
      </div>

      {/* 5. Filter Toolbar */}
      <div className="bg-white border border-slate-200 p-3.5 rounded-xl shadow-xs space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Active Department Indicator */}
          <div className="text-xs text-slate-600 flex items-center gap-1.5 font-medium">
            <span>Roster Scope:</span>
            <span className="font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
              {selectedDept === 'ALL' ? 'All Academic Departments' : selectedDept}
            </span>
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-72">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search candidate name, ID, or course..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600"
            />
          </div>
        </div>

        {/* Secondary Filter Dropdowns */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2 border-t border-slate-100 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-slate-500 text-[11px] font-semibold whitespace-nowrap">Semester Cycle:</span>
            <select
              value={semTypeFilter}
              onChange={(e) => setSemTypeFilter(e.target.value)}
              className="flex-1 bg-white border border-slate-300 rounded-md py-1 px-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-600"
            >
              <option value="ALL">All Cycles</option>
              <option value="Odd Semester">Odd Semester Backlog</option>
              <option value="Even Semester">Even Semester Backlog</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-500 text-[11px] font-semibold whitespace-nowrap">Current Studying Sem:</span>
            <select
              value={currentSemFilter}
              onChange={(e) => setCurrentSemFilter(e.target.value)}
              className="flex-1 bg-white border border-slate-300 rounded-md py-1 px-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-600"
            >
              <option value="ALL">All Semesters</option>
              <option value="Semester 1">Semester 1</option>
              <option value="Semester 3">Semester 3</option>
              <option value="Semester 4">Semester 4</option>
              <option value="Semester 5">Semester 5</option>
              <option value="Semester 7">Semester 7</option>
            </select>
          </div>
        </div>
      </div>

      {/* 6. Backlog Records Roster Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Saturday Backlogs Examination Roster & Seating Ledger
            </h3>
            <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
              {backlogs.length} scheduled
            </span>
          </div>
          <span className="text-[11px] text-slate-500">
            Sessions: <strong>Saturday (Sundays Off)</strong>
          </span>
        </div>

        {isLoading ? (
          <div className="p-12 text-center text-xs text-slate-500">
            Loading backlog examination records...
          </div>
        ) : backlogs.length === 0 ? (
          <div className="p-12 text-center">
            {isPreOptimization ? (
              <>
                <Clock className="w-10 h-10 text-amber-400 mx-auto mb-2" />
                <h4 className="text-sm font-semibold text-slate-800">
                  Pre-Optimization State — Backlog Ledger Cleared (Quality: 0%)
                </h4>
                <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                  Backlog examination weekend allocations, hall seatings, and admit cards will be populated upon extracting the optimized timetable.
                </p>
                <div className="mt-4">
                  <Link
                    to="/optimizer"
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition"
                  >
                    <CalendarCheck className="w-3.5 h-3.5 text-indigo-200" />
                    Extract Optimized Timetable
                  </Link>
                </div>
              </>
            ) : (
              <>
                <History className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                <h4 className="text-sm font-semibold text-slate-800">No Backlog Examination Records Found</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                  No students match the current filters. Click "Register Backlog Candidate" to add a new student arrears exam.
                </p>
              </>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[10px] tracking-wider">
                  <th className="py-3 px-3 text-center w-10">#</th>
                  <th className="py-3 px-4">Candidate Information</th>
                  <th className="py-3 px-4">Current Sem ➔ Backlog Sem</th>
                  <th className="py-3 px-4">Backlog Subject & Course</th>
                  <th className="py-3 px-4">Weekend Schedule & Time</th>
                  <th className="py-3 px-3">Examination Venue & Desk</th>
                  <th className="py-3 px-3 text-center">Status</th>
                  <th className="py-3 px-3 text-center">Admit Card</th>
                  <th className="py-3 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {backlogs.map((item, idx) => (
                  <tr key={item.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-3 text-center font-mono text-slate-400 font-medium">
                      {idx + 1}
                    </td>

                    {/* Candidate */}
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{item.student_name}</div>
                      <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                        {item.student_code} • {item.department}
                      </div>
                    </td>

                    {/* Current Sem vs Backlog Sem */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5 text-xs">
                        <span className="font-semibold text-slate-800 bg-slate-100 px-1.5 py-0.5 rounded text-[11px]">
                          Studying: {item.current_semester}
                        </span>
                        <span className="text-slate-400 font-bold">➔</span>
                        <span className="font-semibold text-rose-800 bg-rose-50 border border-rose-200 px-1.5 py-0.5 rounded text-[11px]">
                          Backlog: {item.backlog_semester}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1 font-mono">
                        Cycle: {item.semester_type}
                      </div>
                    </td>

                    {/* Course */}
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900">{item.course_name}</div>
                      <div className="text-[11px] text-slate-500 font-mono mt-0.5 font-medium">
                        {item.course_code}
                      </div>
                    </td>

                    {/* Weekend Schedule */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-900">
                        <Calendar className="w-3.5 h-3.5 text-amber-600" />
                        <span>{item.exam_day}, {item.exam_date}</span>
                      </div>
                      <div className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span>{item.start_time.substring(0, 5)} – {item.end_time.substring(0, 5)} ({item.period})</span>
                      </div>
                    </td>

                    {/* Venue & Desk */}
                    <td className="py-3 px-3 whitespace-nowrap">
                      <div className="font-bold text-slate-900 flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-indigo-600" />
                        {item.room_code}
                      </div>
                      <div className="text-[11px] text-indigo-700 font-mono font-semibold mt-0.5">
                        Desk: {item.seat_number}
                      </div>
                    </td>

                    {/* Status */}
                    <td className="py-3 px-3 text-center whitespace-nowrap">
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        WEEKEND
                      </span>
                    </td>

                    {/* Print Admit Card (Attachment 3) */}
                    <td className="py-3 px-3 text-center whitespace-nowrap">
                      <a
                        href={api.getBacklogAdmitCardPdfUrl(item.id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 hover:text-indigo-700 rounded-lg transition-colors shadow-2xs"
                        title={`Download Official Admit Card for ${item.student_name}`}
                      >
                        <Printer className="w-3.5 h-3.5 text-slate-500" />
                        Print Admit Card
                      </a>
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => {
                          if (confirm(`Remove backlog registration for ${item.student_name}?`)) {
                            deleteMutation.mutate(item.id);
                          }
                        }}
                        disabled={deleteMutation.isPending}
                        className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition cursor-pointer"
                        title="Delete Backlog Entry"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 7. Registration Modal (With Student Status Old/New input data) */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-2xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-2">
                <span className="p-1.5 bg-indigo-50 border border-indigo-200 rounded-lg text-indigo-700">
                  <Plus className="w-4 h-4" />
                </span>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Register Backlog & Arrears Candidate</h3>
                  <p className="text-[11px] text-slate-500">Configure student status, semesters, and weekend exam session</p>
                </div>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
              {/* Select Existing Student or Type */}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Select Existing Enrolled Student (Optional Quick Fill)
                </label>
                <select
                  onChange={handleStudentSelect}
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-600"
                >
                  <option value="">-- Choose from 60 Enrolled Students --</option>
                  {registeredStudents.map(s => (
                    <option key={s.id} value={s.student_id}>
                      {s.name} ({s.student_id}) - {s.department}
                    </option>
                  ))}
                </select>
              </div>

              {/* Student Code & Name */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Student Registration ID *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. STU-2026-1002"
                    value={formData.student_code}
                    onChange={(e) => setFormData(prev => ({ ...prev, student_code: e.target.value }))}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-600"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Candidate Full Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Jordan Garcia"
                    value={formData.student_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, student_name: e.target.value }))}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-600"
                  />
                </div>
              </div>

              {/* Department & Student Status (Input data kept here) */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Academic Department</label>
                  <select
                    value={formData.department}
                    onChange={(e) => setFormData(prev => ({ ...prev, department: e.target.value }))}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-600"
                  >
                    <option value="Computer Science">Computer Science</option>
                    <option value="Mathematics">Mathematics</option>
                    <option value="Physics">Physics</option>
                    <option value="Electrical Eng">Electrical Eng</option>
                    <option value="Business">Business</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Candidate Status *</label>
                  <select
                    value={formData.student_type}
                    onChange={(e) => setFormData(prev => ({ ...prev, student_type: e.target.value }))}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-600 font-semibold"
                  >
                    <option value="Old Student">Old Student (Senior Arrear Candidate)</option>
                    <option value="New Student">New Student (Current Cohort)</option>
                  </select>
                </div>
              </div>

              {/* Current Studying Sem & Backlog Sem */}
              <div className="grid grid-cols-2 gap-3 p-3 bg-amber-50/60 border border-amber-200 rounded-xl">
                <div>
                  <label className="block font-semibold text-amber-950 mb-1">
                    Currently Studying At *
                  </label>
                  <select
                    value={formData.current_semester}
                    onChange={(e) => setFormData(prev => ({ ...prev, current_semester: e.target.value }))}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-600"
                  >
                    <option value="Semester 2">Semester 2</option>
                    <option value="Semester 3">Semester 3 (Odd Sem)</option>
                    <option value="Semester 4">Semester 4</option>
                    <option value="Semester 5">Semester 5 (Odd Sem)</option>
                    <option value="Semester 6">Semester 6</option>
                    <option value="Semester 7">Semester 7 (Odd Sem)</option>
                    <option value="Semester 8">Semester 8</option>
                  </select>
                  <p className="text-[10px] text-amber-800 mt-1">Active regular semester</p>
                </div>

                <div>
                  <label className="block font-semibold text-amber-950 mb-1">
                    Backlog In Semester *
                  </label>
                  <select
                    value={formData.backlog_semester}
                    onChange={(e) => handleBacklogSemesterChange(e.target.value)}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-600"
                  >
                    <option value="Semester 1">Semester 1 (Odd Sem)</option>
                    <option value="Semester 2">Semester 2 (Even Sem)</option>
                    <option value="Semester 3">Semester 3 (Odd Sem)</option>
                    <option value="Semester 4">Semester 4 (Even Sem)</option>
                    <option value="Semester 5">Semester 5 (Odd Sem)</option>
                    <option value="Semester 6">Semester 6 (Even Sem)</option>
                  </select>
                  <p className="text-[10px] text-amber-800 mt-1 font-semibold">
                    Cycle: {formData.semester_type}
                  </p>
                </div>
              </div>

              {/* Course Selection */}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Backlog Course / Subject *
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <div className="col-span-1">
                    <input
                      type="text"
                      required
                      placeholder="e.g. MA101"
                      value={formData.course_code}
                      onChange={(e) => setFormData(prev => ({ ...prev, course_code: e.target.value.toUpperCase() }))}
                      className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800 uppercase focus:outline-none focus:border-indigo-600"
                    />
                  </div>
                  <div className="col-span-2">
                    <input
                      type="text"
                      required
                      placeholder="e.g. Calculus I & Analytical Geometry"
                      value={formData.course_name}
                      onChange={(e) => setFormData(prev => ({ ...prev, course_name: e.target.value }))}
                      className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-600"
                    />
                  </div>
                </div>
                {registeredExams.length > 0 && (
                  <div className="mt-1">
                    <select
                      onChange={handleCourseSelect}
                      className="w-full bg-slate-50 border border-slate-200 rounded p-1 text-[11px] text-slate-600"
                    >
                      <option value="">Quick Fill from Available Course Exams...</option>
                      {registeredExams.map(ex => (
                        <option key={ex.id} value={ex.course_code}>
                          {ex.course_code} - {ex.course_name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {/* Weekend Slot Picker */}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Saturday Examination Slot (Saturday Only — Sundays Off)
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { key: 'SAT_M', label: 'Saturday Morning', date: 'Dec 19', time: '09:30 - 12:30' },
                    { key: 'SAT_A', label: 'Saturday Afternoon', date: 'Dec 19', time: '14:00 - 17:00' },
                  ].map(s => {
                    const isSelected =
                      (s.key === 'SAT_M' && formData.exam_day === 'Saturday' && formData.period === 'Morning') ||
                      (s.key === 'SAT_A' && formData.exam_day === 'Saturday' && formData.period === 'Afternoon');

                    return (
                      <button
                        key={s.key}
                        type="button"
                        onClick={() => handleWeekendSlotChange(s.key)}
                        className={`p-2.5 rounded-lg border text-left transition cursor-pointer ${
                          isSelected
                            ? 'bg-amber-50 border-amber-400 text-amber-950 font-semibold ring-1 ring-amber-400'
                            : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                        }`}
                      >
                        <div className="text-xs font-bold">{s.label}</div>
                        <div className="text-[10px] text-slate-500 mt-0.5">{s.date} • {s.time}</div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Examination Hall */}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Examination Venue & Hall
                </label>
                <select
                  value={formData.room_code}
                  onChange={(e) => {
                    const code = e.target.value;
                    const name =
                      code === 'AUD-MAIN' ? 'Grand University Auditorium' :
                      code === 'HALL-101' ? 'Science Lecture Hall A' :
                      code === 'LAB-COMP' ? 'Advanced Computing Laboratory' :
                      code === 'ROOM-202' ? 'Classroom 202' : 'Executive Seminar Room';
                    setFormData(prev => ({ ...prev, room_code: code, room_name: name }));
                  }}
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:border-indigo-600"
                >
                  <option value="AUD-MAIN">AUD-MAIN - Grand University Auditorium (150 seats)</option>
                  <option value="HALL-101">HALL-101 - Science Lecture Hall A (75 seats)</option>
                  <option value="LAB-COMP">LAB-COMP - Advanced Computing Laboratory (40 seats)</option>
                  <option value="ROOM-202">ROOM-202 - Classroom 202 (45 seats)</option>
                  <option value="SEM-A">SEM-A - Executive Seminar Room (25 seats)</option>
                </select>
                <p className="text-[10px] text-slate-500 mt-1">
                  Desk number will be auto-allocated upon saving (e.g. {formData.room_code}-BK09).
                </p>
              </div>

              {/* Modal Actions */}
              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition shadow-xs cursor-pointer disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Scheduling...' : 'Confirm & Schedule Backlog'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
