import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { Student, StudentTimetableItem } from '../types';
import {
  Users, Search, Calendar, BookOpen, Clock, Building2,
  CheckCircle2, X, AlertTriangle, FileDown
} from 'lucide-react';

export const StudentsPage: React.FC = () => {
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState('ALL');
  const [viewingStudent, setViewingStudent] = useState<Student | null>(null);

  const { data: students = [], isLoading } = useQuery({
    queryKey: ['students', selectedDept, search],
    queryFn: () => api.getStudents({
      department: selectedDept !== 'ALL' ? selectedDept : undefined,
      search: search || undefined
    }),
  });

  const { data: studentSchedule = [], isLoading: loadingSchedule } = useQuery({
    queryKey: ['student-timetable', viewingStudent?.id],
    queryFn: () => viewingStudent ? api.getStudentTimetable(viewingStudent.id) : Promise.resolve([]),
    enabled: !!viewingStudent,
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white border border-slate-200 p-5 rounded-xl shadow-xs">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Users className="w-5 h-5 text-indigo-600" />
            Student Cohort Registry & Individual Schedules
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Student enrollments, accommodation requirements, and student-wise examination timetables
          </p>
        </div>
        <div className="text-xs text-slate-500 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 font-mono">
          Total Students: <strong className="text-slate-900 font-bold">{students.length}</strong>
        </div>
      </div>

      {/* Filter and Search */}
      <div className="flex flex-wrap items-center gap-3 bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by student name or ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-white border border-slate-300 rounded-lg text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600"
          />
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500 font-medium">Department:</span>
          <select
            value={selectedDept}
            onChange={(e) => setSelectedDept(e.target.value)}
            className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:border-indigo-600"
          >
            <option value="ALL">All Departments</option>
            <option value="Computer Science">Computer Science</option>
            <option value="Mathematics">Mathematics</option>
            <option value="Physics">Physics</option>
            <option value="Electrical Eng">Electrical Eng</option>
            <option value="Business">Business</option>
          </select>
        </div>
      </div>

      {/* Students Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Student ID</th>
                <th className="py-3 px-4">Full Name</th>
                <th className="py-3 px-4">Department</th>
                <th className="py-3 px-4">Semester</th>
                <th className="py-3 px-4">Enrolled Exams</th>
                <th className="py-3 px-4">Accommodations</th>
                <th className="py-3 px-4 text-right">Personal Timetable</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {students.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No students found matching filters
                  </td>
                </tr>
              ) : (
                students.map((student) => (
                  <tr key={student.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3 px-4 font-mono font-bold text-slate-900">{student.student_id}</td>
                    <td className="py-3 px-4">
                      <button
                        type="button"
                        onClick={() => setViewingStudent(student)}
                        className="text-slate-900 font-semibold hover:text-indigo-600 hover:underline cursor-pointer text-left flex items-center gap-1.5 transition-colors group"
                        title={`Click to view examination timetable and details for ${student.name}`}
                      >
                        <span>{student.name}</span>
                        <span className="text-[10px] text-indigo-600 bg-indigo-50 border border-indigo-200 px-1.5 py-0.2 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                          View
                        </span>
                      </button>
                    </td>
                    <td className="py-3 px-4 text-slate-600">{student.department}</td>
                    <td className="py-3 px-4 text-slate-500">{student.semester}</td>
                    <td className="py-3 px-4 font-mono font-semibold text-slate-700">{student.enrolled_exam_ids.length} Courses</td>
                    <td className="py-3 px-4">
                      {student.special_accommodations.length > 0 ? (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-medium">
                          {student.special_accommodations.join(', ')}
                        </span>
                      ) : (
                        <span className="text-slate-400">Standard</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="inline-flex items-center gap-1.5 justify-end">
                        <a
                          href={api.getStudentHallTicketPdfUrl(student.id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-300 font-medium text-xs transition"
                          title="Download Admit Card PDF"
                        >
                          <FileDown className="w-3.5 h-3.5 text-slate-500" />
                          Admit Card
                        </a>
                        <button
                          onClick={() => setViewingStudent(student)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 font-semibold text-xs transition cursor-pointer"
                        >
                          <Calendar className="w-3.5 h-3.5" />
                          View Schedule
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Individual Student Timetable Modal */}
      {viewingStudent && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl w-full max-w-2xl p-6 space-y-4 shadow-xl max-h-[85vh] flex flex-col text-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-indigo-600" />
                  Personalized Examination Timetable & Seating
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {viewingStudent.name} ({viewingStudent.student_id}) • {viewingStudent.department}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={api.getStudentHallTicketPdfUrl(viewingStudent.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-indigo-700 hover:bg-indigo-800 rounded-lg transition-colors shadow-2xs"
                  title="Download Official Admit Card PDF"
                >
                  <FileDown className="w-3.5 h-3.5" />
                  Download Admit Card (PDF)
                </a>
                <button onClick={() => setViewingStudent(null)} className="p-1 text-slate-400 hover:text-slate-700 cursor-pointer">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="overflow-y-auto space-y-3 flex-1 pr-1">
              {loadingSchedule ? (
                <div className="py-12 text-center text-xs text-slate-400 animate-pulse">Loading timetable...</div>
              ) : studentSchedule.length === 0 ? (
                <div className="py-12 text-center text-xs text-slate-400">
                  No active timetable assignments for this student's courses yet.
                </div>
              ) : (
                studentSchedule.map((item, idx) => (
                  <div key={idx} className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="font-bold text-slate-900 text-sm">{item.exam_code} — {item.course_name}</div>
                        <div className="text-xs text-slate-500">{item.course_code}</div>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">
                        Confirmed
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200 text-xs text-slate-600">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-indigo-600" />
                        <span>{item.date} at {item.start_time.slice(0, 5)} - {item.end_time.slice(0, 5)}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-indigo-600" />
                        <span>{item.room_name} ({item.room_code}, {item.building})</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
