import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { StudentSeatingResponse, DepartmentSeatingSummary } from '../types';
import {
  GraduationCap, Search, FileDown, FileText, ChevronDown, ChevronUp,
  Building2, Clock, Calendar, ShieldCheck, CheckCircle2,
  Users, RefreshCw, Printer, Filter, CalendarCheck
} from 'lucide-react';

export const StudentSeatingsPage: React.FC = () => {
  const [selectedDept, setSelectedDept] = useState<string>('ALL');
  const [search, setSearch] = useState<string>('');
  const [expandedStudents, setExpandedStudents] = useState<Record<number, boolean>>({});
  const [allExpanded, setAllExpanded] = useState<boolean>(false);

  // 0. Fetch dashboard for optimization state
  const { data: dashboard } = useQuery({
    queryKey: ['dashboard'],
    queryFn: api.getDashboard,
  });

  const isPreOptimization = dashboard ? dashboard.quality_score === 0 : false;

  // 1. Fetch department summaries
  const { data: deptSummaries = [], isLoading: loadingDepts } = useQuery<DepartmentSeatingSummary[]>({
    queryKey: ['department-seatings-summary'],
    queryFn: () => api.getDepartmentSeatingSummaries(),
  });

  // 2. Fetch student seatings
  const { data: students = [], isLoading: loadingStudents, refetch, isFetching } = useQuery<StudentSeatingResponse[]>({
    queryKey: ['student-seatings', selectedDept, search],
    queryFn: () => api.getStudentSeatings({
      department: selectedDept !== 'ALL' ? selectedDept : undefined,
      search: search.trim() || undefined,
    }),
  });

  const toggleStudentExpand = (id: number) => {
    setExpandedStudents(prev => ({
      ...prev,
      [id]: prev[id] !== undefined ? !prev[id] : !allExpanded
    }));
  };

  const handleStudentNameClick = (id: number, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setExpandedStudents(prev => ({
      ...prev,
      [id]: !isStudentExpanded(id)
    }));
  };

  const toggleExpandAll = () => {
    const nextState = !allExpanded;
    setAllExpanded(nextState);
    const updated: Record<number, boolean> = {};
    students.forEach(s => {
      updated[s.id] = nextState;
    });
    setExpandedStudents(updated);
  };

  const isStudentExpanded = (id: number) => {
    if (expandedStudents[id] !== undefined) {
      return expandedStudents[id];
    }
    return allExpanded;
  };

  // Compute metrics
  const totalStudentsCount = students.length;
  const totalSittingsCount = students.reduce((acc, s) => acc + s.exams.length, 0);
  const totalVenuesCount = new Set(
    students.flatMap(s => s.exams.map(e => e.room_code))
  ).size;

  const currentDeptLabel = selectedDept === 'ALL' ? 'All Academic Departments' : selectedDept;
  const deptPdfUrl = api.getDepartmentSeatingPdfUrl(selectedDept !== 'ALL' ? selectedDept : undefined);
  const deptCsvUrl = api.getDepartmentSeatingCsvUrl(selectedDept !== 'ALL' ? selectedDept : undefined);

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
                Pre-Optimization State — Student Seating Ledger Cleared (Quality: 0%)
              </h3>
              <p className="text-xs text-slate-600 mt-0.5">
                The active schedule is in draft pre-optimization baseline state. Individual candidate examination hall allocations, desk numbers, and admit cards are generated upon extracting the optimized timetable.
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
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-indigo-50 border border-indigo-200 rounded-lg text-indigo-700">
              <GraduationCap className="w-5 h-5" />
            </span>
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                Student Seating & Examination Hall Allocations
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Official department-wise student examination rosters, hall allocations, and individual candidate admit cards
              </p>
            </div>
          </div>
        </div>

        {/* Global Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-2xs"
            title="Refresh Seating Allocations"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          {isPreOptimization ? (
            <span
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-400 bg-slate-50 border border-slate-200 rounded-lg cursor-not-allowed shadow-2xs"
              title="Seatings are cleared in pre-optimization state. Extract timetable to export."
            >
              <FileText className="w-3.5 h-3.5 text-slate-400" />
              Export CSV (Pending)
            </span>
          ) : (
            <a
              href={deptCsvUrl}
              download
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors shadow-2xs"
              title="Export CSV Seating Roster"
            >
              <FileText className="w-3.5 h-3.5 text-slate-500" />
              Export CSV
            </a>
          )}

          {isPreOptimization ? (
            <span
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-slate-400 bg-slate-100 border border-slate-200 rounded-lg cursor-not-allowed shadow-xs"
              title="Seatings are cleared in pre-optimization state. Extract timetable to export."
            >
              <FileDown className="w-4 h-4 text-slate-400" />
              Download Seating PDF (Pending)
            </span>
          ) : (
            <a
              href={deptPdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-indigo-700 hover:bg-indigo-800 rounded-lg transition-colors shadow-xs"
              title="Download Official Department Seating PDF"
            >
              <FileDown className="w-4 h-4" />
              Download Seating PDF ({selectedDept === 'ALL' ? 'All' : selectedDept})
            </a>
          )}
        </div>
      </div>

      {/* 2. Department Selector Tabs */}
      <div className="bg-white border border-slate-200 p-3 rounded-xl shadow-xs">
        <div className="flex items-center justify-between mb-2 px-1">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <Filter className="w-3 h-3 text-slate-400" />
            Academic Department Rosters
          </span>
          <span className="text-[11px] text-slate-500 font-mono">
            Active: <strong className="text-slate-800">{currentDeptLabel}</strong>
          </span>
        </div>

        <div className="flex flex-wrap gap-2">
          {/* ALL Button */}
          <button
            onClick={() => setSelectedDept('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
              selectedDept === 'ALL'
                ? 'bg-slate-900 text-white shadow-xs font-semibold'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200/80 border border-slate-200'
            }`}
          >
            <span>All Departments</span>
            <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
              selectedDept === 'ALL' ? 'bg-slate-700 text-white' : 'bg-slate-200 text-slate-700 font-mono'
            }`}>
              {deptSummaries.reduce((sum, d) => sum + d.students_count, 0) || totalStudentsCount}
            </span>
          </button>

          {/* Department Specific Tabs */}
          {deptSummaries.map((dept) => {
            const isSelected = selectedDept === dept.department;
            return (
              <button
                key={dept.department}
                onClick={() => setSelectedDept(dept.department)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
                  isSelected
                    ? 'bg-indigo-700 text-white shadow-xs font-semibold'
                    : 'bg-slate-50 text-slate-700 hover:bg-slate-100 border border-slate-200'
                }`}
              >
                <span>{dept.department}</span>
                <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                  isSelected ? 'bg-indigo-900 text-indigo-100' : 'bg-slate-200 text-slate-600 font-mono'
                }`}>
                  {dept.students_count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Metrics Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white border border-slate-200 p-3.5 rounded-xl shadow-xs">
          <div className="text-[11px] text-slate-500 font-medium">Candidates In Roster</div>
          <div className="text-xl font-bold text-slate-900 mt-0.5">{totalStudentsCount}</div>
          <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
            <Users className="w-3 h-3 text-indigo-600" />
            {selectedDept === 'ALL' ? 'University Cohort' : `${selectedDept} Dept`}
          </div>
        </div>

        <div className="bg-white border border-slate-200 p-3.5 rounded-xl shadow-xs">
          <div className="text-[11px] text-slate-500 font-medium">Total Exam Sittings</div>
          <div className="text-xl font-bold text-slate-900 mt-0.5">{totalSittingsCount}</div>
          <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
            <Clock className="w-3 h-3 text-emerald-600" />
            {(totalStudentsCount > 0 ? (totalSittingsCount / totalStudentsCount).toFixed(1) : '0')} exams/student avg
          </div>
        </div>

        <div className="bg-white border border-slate-200 p-3.5 rounded-xl shadow-xs">
          <div className="text-[11px] text-slate-500 font-medium">Distinct Exam Halls</div>
          <div className="text-xl font-bold text-slate-900 mt-0.5">{totalVenuesCount}</div>
          <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
            <Building2 className="w-3 h-3 text-blue-600" />
            Active venues allocated
          </div>
        </div>

        <div className="bg-white border border-slate-200 p-3.5 rounded-xl shadow-xs">
          <div className="text-[11px] text-slate-500 font-medium">Seating Verification</div>
          <div className={`text-xl font-bold mt-0.5 flex items-center gap-1.5 ${isPreOptimization ? 'text-amber-700' : 'text-emerald-700'}`}>
            {isPreOptimization ? (
              <>
                <Clock className="w-5 h-5 text-amber-600" />
                Pending
              </>
            ) : (
              <>
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                100% Assigned
              </>
            )}
          </div>
          <div className={`text-[10px] mt-1 ${isPreOptimization ? 'text-amber-600 font-medium' : 'text-emerald-600'}`}>
            {isPreOptimization ? 'Pre-Optimization State' : 'Deterministic desk allocations'}
          </div>
        </div>
      </div>

      {/* 4. Search and Table Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white border border-slate-200 p-3 rounded-xl shadow-xs">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search candidate name, student ID (e.g. STU-2026-1001)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 bg-white border border-slate-300 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600"
          />
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={toggleExpandAll}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
          >
            {allExpanded ? (
              <>
                <ChevronUp className="w-3.5 h-3.5 text-slate-500" />
                Collapse All
              </>
            ) : (
              <>
                <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
                Expand All
              </>
            )}
          </button>

          <span className="text-xs text-slate-500 font-mono px-2">
            Showing <strong>{students.length}</strong> candidates
          </span>
        </div>
      </div>

      {/* 5. Student Roster Listing */}
      {loadingStudents ? (
        <div className="p-12 text-center bg-white border border-slate-200 rounded-xl shadow-xs text-xs text-slate-500">
          <RefreshCw className="w-6 h-6 animate-spin text-indigo-600 mx-auto mb-2" />
          Loading candidate seating allocations...
        </div>
      ) : students.length === 0 ? (
        <div className="p-12 text-center bg-white border border-slate-200 rounded-xl shadow-xs">
          <GraduationCap className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">
            {isPreOptimization ? 'Student Seating Allocations Cleared (Pre-Optimization)' : 'No Student Seating Allocations Found'}
          </h3>
          <p className="text-xs text-slate-500 mt-1.5 max-w-md mx-auto">
            {isPreOptimization
              ? 'Student seating allocations are cleared while in baseline draft state. Click below to extract the optimized timetable to generate student schedules, examination venues, and hall admit cards.'
              : 'No students match the selected department filter or search query. Try choosing "All Departments" or clearing search.'}
          </p>
          {isPreOptimization && (
            <div className="mt-5">
              <Link
                to="/optimizer"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition"
              >
                <CalendarCheck className="w-4 h-4 text-indigo-200" />
                Extract Optimized Timetable
              </Link>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {students.map((student, idx) => {
            const isExpanded = isStudentExpanded(student.id);
            const admitCardPdfUrl = api.getStudentHallTicketPdfUrl(student.id);

            return (
              <div
                key={student.id}
                className={`bg-white border rounded-xl shadow-2xs overflow-hidden transition-all ${
                  isExpanded ? 'border-indigo-400 ring-2 ring-indigo-50 shadow-sm' : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                {/* Student Header Bar */}
                <div
                  className={`p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 cursor-pointer select-none transition-colors ${
                    isExpanded ? 'bg-indigo-50/20 border-b border-slate-200' : 'hover:bg-slate-50/50'
                  }`}
                  onClick={() => toggleStudentExpand(student.id)}
                >
                  <div className="flex items-start md:items-center gap-3">
                    <span className="w-7 h-7 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 font-bold text-xs flex items-center justify-center shrink-0">
                      {idx + 1}
                    </span>

                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <button
                          type="button"
                          onClick={(e) => handleStudentNameClick(student.id, e)}
                          className="text-sm font-bold text-slate-900 hover:text-indigo-600 hover:underline cursor-pointer flex items-center gap-1.5 transition-colors group text-left"
                          title={`Click to ${isExpanded ? 'collapse' : 'display all examination and seating details for'} ${student.name}`}
                        >
                          <span>{student.name}</span>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded transition-all inline-flex items-center gap-1 ${
                            isExpanded 
                              ? 'bg-indigo-100 text-indigo-800 border border-indigo-200' 
                              : 'bg-indigo-50 text-indigo-700 border border-indigo-200 hover:bg-indigo-100'
                          }`}>
                            {isExpanded ? (
                              <>
                                <ChevronUp className="w-3 h-3 text-indigo-600" />
                                Hide Details
                              </>
                            ) : (
                              <>
                                <ChevronDown className="w-3 h-3 text-indigo-600" />
                                Click to View Details
                              </>
                            )}
                          </span>
                        </button>
                        <span className="font-mono text-[11px] font-semibold text-slate-700 bg-white border border-slate-300 px-2 py-0.5 rounded shadow-2xs">
                          {student.student_id}
                        </span>
                        <span className="text-[11px] font-medium text-indigo-700 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded">
                          {student.department}
                        </span>
                        <span className="text-[11px] font-medium text-slate-600 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">
                          {student.semester}
                        </span>
                        {student.special_accommodations.length > 0 && (
                          <span className="text-[11px] font-medium text-amber-800 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded">
                            ♿ {student.special_accommodations.join(', ')}
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-3 mt-1.5 text-xs text-slate-500">
                        <span>
                          <strong className="text-slate-800 font-semibold">{student.subjects_count}</strong> Scheduled Subjects
                        </span>
                        <span>•</span>
                        <span>
                          <strong className="text-slate-800 font-semibold">{student.distinct_halls_count}</strong> Distinct Venues
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions & Chevron */}
                  <div className="flex items-center gap-2 self-end md:self-auto" onClick={(e) => e.stopPropagation()}>
                    <a
                      href={admitCardPdfUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 hover:text-indigo-700 rounded-lg transition-colors shadow-2xs"
                      title={`Download Official Admit Card for ${student.name}`}
                    >
                      <Printer className="w-3.5 h-3.5 text-slate-500" />
                      Print Admit Card
                    </a>

                    <button
                      onClick={() => toggleStudentExpand(student.id)}
                      className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
                      aria-label="Toggle subjects details"
                    >
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Expanded Subjects Table */}
                {isExpanded && (
                  <div className="border-t border-slate-200 bg-white">
                    <div className="px-4 py-2 bg-slate-50/80 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2 text-xs">
                      <span className="text-slate-700 font-semibold flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        Allocated Examination Sessions & Desks for {student.name}
                      </span>
                      <span className="text-[11px] text-slate-500 font-mono">
                        {student.student_id} • {student.department} • {student.exams.length} Papers
                      </span>
                    </div>

                    <div className="p-4 overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-500 font-semibold bg-slate-50/60">
                          <th className="py-2.5 px-3 w-10 text-center">#</th>
                          <th className="py-2.5 px-3">Subject & Course</th>
                          <th className="py-2.5 px-3">Exam Date & Day</th>
                          <th className="py-2.5 px-3">Time Window</th>
                          <th className="py-2.5 px-3">Examination Venue</th>
                          <th className="py-2.5 px-3">Assigned Desk / Seat</th>
                          <th className="py-2.5 px-3 text-center">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {student.exams.length === 0 ? (
                          <tr>
                            <td colSpan={7} className="py-4 text-center text-slate-400 italic">
                              No examination sessions scheduled for this candidate in the active timetable.
                            </td>
                          </tr>
                        ) : (
                          student.exams.map((exam, exIdx) => (
                            <tr key={exam.exam_id} className="hover:bg-slate-50/50 transition-colors">
                              <td className="py-2.5 px-3 text-center font-mono text-slate-400 font-medium">
                                {exIdx + 1}
                              </td>

                              <td className="py-2.5 px-3">
                                <div className="font-semibold text-slate-900">
                                  {exam.course_name}
                                </div>
                                <div className="text-[11px] font-mono text-slate-500">
                                  {exam.course_code} • {exam.exam_code}
                                </div>
                              </td>

                              <td className="py-2.5 px-3 whitespace-nowrap">
                                <div className="font-medium text-slate-800 flex items-center gap-1.5">
                                  <Calendar className="w-3.5 h-3.5 text-indigo-600" />
                                  {exam.date}
                                </div>
                                <div className="text-[11px] text-slate-500 pl-5">
                                  {exam.day_name || 'Exam Day'}
                                </div>
                              </td>

                              <td className="py-2.5 px-3 whitespace-nowrap">
                                <div className="font-medium text-slate-800 flex items-center gap-1.5">
                                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                                  {exam.start_time.substring(0, 5)} – {exam.end_time.substring(0, 5)}
                                </div>
                                {exam.period && (
                                  <div className="text-[10px] text-slate-500 pl-5 font-mono">
                                    {exam.period} Session
                                  </div>
                                )}
                              </td>

                              <td className="py-2.5 px-3">
                                <div className="font-bold text-slate-800 flex items-center gap-1">
                                  <Building2 className="w-3.5 h-3.5 text-slate-400" />
                                  {exam.room_code}
                                </div>
                                <div className="text-[11px] text-slate-500">
                                  {exam.room_name} ({exam.building})
                                </div>
                              </td>

                              <td className="py-2.5 px-3 whitespace-nowrap">
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold font-mono bg-blue-50 text-blue-700 border border-blue-200">
                                  {exam.seat_number}
                                </span>
                              </td>

                              <td className="py-2.5 px-3 text-center whitespace-nowrap">
                                {exam.is_locked ? (
                                  <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded">
                                    Locked
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                                    <CheckCircle2 className="w-3 h-3" />
                                    Allocated
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>

                    <div className="px-4 py-2.5 bg-slate-50/50 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500">
                      <span>
                        Official Seating Allocation Reference: <strong className="text-slate-700 font-mono">SEAT-{student.student_id}</strong>
                      </span>
                      <a
                        href={admitCardPdfUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-medium text-indigo-700 hover:text-indigo-900 hover:underline flex items-center gap-1"
                      >
                        <Printer className="w-3 h-3" />
                        Download Official Admit Card (PDF)
                      </a>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
