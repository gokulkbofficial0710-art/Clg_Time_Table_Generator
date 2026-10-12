import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { Exam, Student } from '../types';
import {
  BookOpen, Plus, Search, Lock, Unlock, Edit2, Trash2,
  Users, CheckCircle2, X, Clock, Award, Filter
} from 'lucide-react';

export const ExamsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState('ALL');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingExam, setEditingExam] = useState<Exam | null>(null);
  const [enrolledExam, setEnrolledExam] = useState<Exam | null>(null);

  const { data: exams = [], isLoading } = useQuery({
    queryKey: ['exams', selectedDept, search],
    queryFn: () => api.getExams({
      department: selectedDept !== 'ALL' ? selectedDept : undefined,
      search: search || undefined
    }),
  });

  const { data: enrolledStudents = [] } = useQuery({
    queryKey: ['exam-students', enrolledExam?.id],
    queryFn: () => enrolledExam ? api.getExamStudents(enrolledExam.id) : Promise.resolve([]),
    enabled: !!enrolledExam,
  });

  const lockMutation = useMutation({
    mutationFn: ({ id, lock }: { id: number; lock: boolean }) => api.toggleExamLock(id, lock),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['exams'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteExam(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['exams'] }),
  });

  const saveMutation = useMutation({
    mutationFn: ({ id, data }: { id?: number; data: any }) =>
      id ? api.updateExam(id, data) : api.createExam(data),
    onSuccess: () => {
      setIsAddModalOpen(false);
      setEditingExam(null);
      queryClient.invalidateQueries({ queryKey: ['exams'] });
    },
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white border border-slate-200 p-5 rounded-xl shadow-xs">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-indigo-600" />
            Course Examinations Registry
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Configure examination sessions, durations, venue requirements, and administrative locks
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-xs transition self-start md:self-auto cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          Add Examination
        </button>
      </div>

      {/* Filter and Search */}
      <div className="flex flex-wrap items-center gap-3 bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search code, course name..."
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
            <option value="Humanities">Humanities</option>
          </select>
        </div>
      </div>

      {/* Examinations Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Exam Code</th>
                <th className="py-3 px-4">Course Name</th>
                <th className="py-3 px-4">Department</th>
                <th className="py-3 px-4">Duration</th>
                <th className="py-3 px-4">Enrolled</th>
                <th className="py-3 px-4">Features</th>
                <th className="py-3 px-4">Lock</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {exams.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    No examinations found matching filters
                  </td>
                </tr>
              ) : (
                exams.map((exam) => (
                  <tr key={exam.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3 px-4 font-mono font-bold text-slate-900">
                      {exam.exam_code}
                    </td>
                    <td className="py-3 px-4">
                      <div>
                        <span className="font-semibold text-slate-900">{exam.course_name}</span>
                        <span className="block text-[11px] text-slate-500">{exam.course_code}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-600">{exam.department}</td>
                    <td className="py-3 px-4 font-mono font-semibold text-slate-700">
                      {exam.duration_minutes}m
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => setEnrolledExam(exam)}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-50 hover:bg-slate-100 text-indigo-700 border border-slate-200 font-mono transition cursor-pointer"
                      >
                        <Users className="w-3 h-3" />
                        {exam.enrollment_count}
                      </button>
                    </td>
                    <td className="py-3 px-4">
                      {exam.required_features.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {exam.required_features.map((f, i) => (
                            <span key={i} className="px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-[10px] text-slate-700">
                              {f}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => lockMutation.mutate({ id: exam.id, lock: !exam.is_locked })}
                        className={`p-1.5 rounded-lg border transition cursor-pointer ${
                          exam.is_locked
                            ? 'bg-indigo-50 border-indigo-200 text-indigo-700 hover:bg-indigo-100'
                            : 'bg-slate-50 border-slate-200 text-slate-400 hover:text-slate-600'
                        }`}
                        title={exam.is_locked ? 'Click to Unlock' : 'Click to Lock'}
                      >
                        {exam.is_locked ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                      </button>
                    </td>
                    <td className="py-3 px-4 text-right space-x-1">
                      <button
                        onClick={() => setEditingExam(exam)}
                        className="p-1.5 text-slate-400 hover:text-slate-700 rounded hover:bg-slate-100 transition cursor-pointer"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => {
                          if (confirm(`Delete exam ${exam.exam_code}?`)) {
                            deleteMutation.mutate(exam.id);
                          }
                        }}
                        className="p-1.5 text-slate-400 hover:text-rose-600 rounded hover:bg-rose-50 transition cursor-pointer"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Enrolled Students Drawer/Modal */}
      {enrolledExam && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl w-full max-w-lg p-6 space-y-4 shadow-xl max-h-[85vh] flex flex-col text-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Enrolled Students</h3>
                <p className="text-xs text-slate-500">{enrolledExam.exam_code} — {enrolledExam.course_name}</p>
              </div>
              <button onClick={() => setEnrolledExam(null)} className="p-1 text-slate-400 hover:text-slate-700 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="overflow-y-auto space-y-2 flex-1 pr-1">
              {enrolledStudents.length === 0 ? (
                <p className="text-xs text-slate-400 py-6 text-center">No students currently enrolled</p>
              ) : (
                enrolledStudents.map((s) => (
                  <div key={s.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between text-xs">
                    <div>
                      <div className="font-semibold text-slate-900">{s.name}</div>
                      <div className="text-[11px] text-slate-500 font-mono">{s.student_id} • {s.department}</div>
                    </div>
                    {s.special_accommodations.length > 0 && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-mono">
                        {s.special_accommodations.join(', ')}
                      </span>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Add / Edit Exam Modal */}
      {(isAddModalOpen || editingExam) && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl w-full max-w-lg p-6 space-y-4 shadow-xl text-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">
                {editingExam ? 'Edit Examination' : 'Add New Examination'}
              </h3>
              <button
                onClick={() => { setIsAddModalOpen(false); setEditingExam(null); }}
                className="p-1 text-slate-400 hover:text-slate-700 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                const form = e.currentTarget as any;
                const data = {
                  exam_code: form.exam_code.value,
                  course_code: form.course_code.value,
                  course_name: form.course_name.value,
                  department: form.department.value,
                  duration_minutes: parseInt(form.duration_minutes.value),
                  exam_type: form.exam_type.value,
                  priority: parseInt(form.priority.value),
                  required_features: form.features.value ? form.features.value.split(',').map((s: string) => s.trim()) : [],
                  notes: form.notes.value,
                };
                saveMutation.mutate({ id: editingExam?.id, data });
              }}
              className="space-y-3 text-xs"
            >
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Exam Code</label>
                  <input
                    name="exam_code"
                    defaultValue={editingExam?.exam_code || ''}
                    placeholder="EXAM-CS101"
                    required
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Course Code</label>
                  <input
                    name="course_code"
                    defaultValue={editingExam?.course_code || ''}
                    placeholder="CS101"
                    required
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Course Title</label>
                <input
                  name="course_name"
                  defaultValue={editingExam?.course_name || ''}
                  placeholder="Data Structures"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Department</label>
                  <input
                    name="department"
                    defaultValue={editingExam?.department || 'Computer Science'}
                    required
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Duration (minutes)</label>
                  <input
                    name="duration_minutes"
                    type="number"
                    defaultValue={editingExam?.duration_minutes || 120}
                    required
                    min={15}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Type</label>
                  <select
                    name="exam_type"
                    defaultValue={editingExam?.exam_type || 'Written'}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                  >
                    <option value="Written">Written</option>
                    <option value="Practical">Practical</option>
                    <option value="Oral">Oral</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Priority (1-10)</label>
                  <input
                    name="priority"
                    type="number"
                    min={1}
                    max={10}
                    defaultValue={editingExam?.priority || 5}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Required Features (comma-separated)</label>
                <input
                  name="features"
                  defaultValue={editingExam?.required_features.join(', ') || ''}
                  placeholder="Computers, Wheelchair Access"
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Notes</label>
                <textarea
                  name="notes"
                  defaultValue={editingExam?.notes || ''}
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 h-16 focus:outline-none focus:border-indigo-600"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => { setIsAddModalOpen(false); setEditingExam(null); }}
                  className="px-4 py-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saveMutation.isPending}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-semibold shadow-xs cursor-pointer"
                >
                  {saveMutation.isPending ? 'Saving...' : 'Save Examination'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
