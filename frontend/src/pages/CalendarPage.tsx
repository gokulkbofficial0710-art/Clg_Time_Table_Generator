import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { Assignment, Room, TimeSlot } from '../types';
import {
  Calendar as CalendarIcon, Clock, Building2, Lock, Unlock,
  Search, Filter, Edit3, ShieldAlert, CheckCircle2, User,
  AlertTriangle, X, Save, CalendarCheck
} from 'lucide-react';

export const CalendarPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [viewMode, setViewMode] = useState<'grid' | 'room' | 'dept'>('grid');
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState<string>('ALL');
  const [selectedRoom, setSelectedRoom] = useState<string>('ALL');
  const [editingAssignment, setEditingAssignment] = useState<Assignment | null>(null);

  // Queries
  const { data: dashboard } = useQuery({
    queryKey: ['dashboard'],
    queryFn: api.getDashboard,
  });

  const { data: assignments = [], isLoading: loadingAssignments } = useQuery({
    queryKey: ['timetable', selectedDept, search],
    queryFn: () => api.getTimetable({
      department: selectedDept !== 'ALL' ? selectedDept : undefined,
      search: search || undefined
    }),
  });

  const { data: rooms = [] } = useQuery({
    queryKey: ['rooms'],
    queryFn: api.getRooms,
  });

  const { data: slots = [] } = useQuery({
    queryKey: ['timeslots'],
    queryFn: api.getTimeSlots,
  });

  // Lock Toggle Mutation
  const lockMutation = useMutation({
    mutationFn: ({ id, lock }: { id: number; lock: boolean }) => api.toggleAssignmentLock(id, lock),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timetable'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });

  // Manual Edit Mutation
  const editMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => api.updateAssignment(id, data),
    onSuccess: () => {
      setEditingAssignment(null);
      queryClient.invalidateQueries({ queryKey: ['timetable'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });

  // Filtered Assignments
  const filteredAssignments = useMemo(() => {
    return assignments.filter((a) => {
      if (selectedRoom !== 'ALL' && a.room_code !== selectedRoom) return false;
      return true;
    });
  }, [assignments, selectedRoom]);

  // Unique departments for filter
  const departments = useMemo(() => {
    const set = new Set<string>();
    assignments.forEach((a) => {
      if (a.department) set.add(a.department);
    });
    return Array.from(set).sort();
  }, [assignments]);

  // Group by Date & Slot for the Grid View
  const gridData = useMemo(() => {
    const dates = Array.from(new Set(slots.map((s) => s.date))).sort();
    return dates.map((d) => {
      const dateSlots = slots.filter((s) => s.date === d).sort((a, b) => a.start_time.localeCompare(b.start_time));
      return {
        date: d,
        slots: dateSlots.map((s) => {
          const slotAssignments = filteredAssignments.filter((a) => a.timeslot_id === s.id);
          return {
            slot: s,
            assignments: slotAssignments,
          };
        }),
      };
    });
  }, [slots, filteredAssignments]);

  const isPreOptimization = dashboard ? dashboard.quality_score === 0 : false;
  const isTimetableEmpty = (isPreOptimization || assignments.length === 0) && selectedDept === 'ALL' && !search && selectedRoom === 'ALL';

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Draft Baseline Banner */}
      {isPreOptimization && (
        <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/90 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-amber-100 text-amber-700 shrink-0">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Draft Baseline State — Timetable Grid is Unallocated (Quality: 0%)
              </h3>
              <p className="text-xs text-slate-600 mt-0.5">
                The active schedule is in draft pre-optimization baseline state. All examination slots, rooms, and seatings are unallocated until the timetable optimizer is executed.
              </p>
            </div>
          </div>
          <Link
            to="/optimizer"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-xs transition shrink-0"
          >
            <CalendarCheck className="w-3.5 h-3.5 text-indigo-300" />
            Extract Optimized Timetable
          </Link>
        </div>
      )}

      {/* Header and Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white border border-slate-200 p-5 rounded-xl shadow-xs">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <CalendarIcon className="w-5 h-5 text-indigo-600" />
            Timetable Calendar & Examination Schedule
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Interactive examination schedule across examination sessions, rooms, and academic departments
          </p>
        </div>

        {/* View Mode Switcher */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
          <button
            onClick={() => setViewMode('grid')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition cursor-pointer ${
              viewMode === 'grid' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Session Grid
          </button>
          <button
            onClick={() => setViewMode('room')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition cursor-pointer ${
              viewMode === 'room' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Room View
          </button>
          <button
            onClick={() => setViewMode('dept')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition cursor-pointer ${
              viewMode === 'dept' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Department View
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-white border border-slate-200 p-4 rounded-xl shadow-xs">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search course code, exam title, room..."
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
            {departments.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500 font-medium">Room:</span>
          <select
            value={selectedRoom}
            onChange={(e) => setSelectedRoom(e.target.value)}
            className="bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:border-indigo-600"
          >
            <option value="ALL">All Rooms</option>
            {rooms.map((r) => (
              <option key={r.id} value={r.room_code}>{r.room_code} ({r.capacity} seats)</option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Content: Empty State or Scheduled Timetable Views */}
      {isTimetableEmpty ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-xs space-y-4">
          <div className="w-16 h-16 mx-auto rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-400">
            <CalendarIcon className="w-8 h-8 text-slate-400" />
          </div>
          <div className="max-w-md mx-auto space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
              Draft Baseline — Unallocated
            </div>
            <h3 className="text-lg font-bold text-slate-900">Examination Timetable Grid is Empty</h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              No examinations are currently scheduled. The timetable has been reset to an unallocated baseline state. To assign examinations to time slots and venues, extract the optimized timetable.
            </p>
          </div>
          <div className="pt-2">
            <Link
              to="/optimizer"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-white shadow-xs transition"
            >
              <CalendarCheck className="w-4 h-4 text-indigo-300" />
              Extract Optimized Timetable
            </Link>
          </div>
        </div>
      ) : filteredAssignments.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-xs space-y-3">
          <Search className="w-8 h-8 text-slate-300 mx-auto" />
          <h3 className="text-sm font-bold text-slate-800">No Matching Examinations Found</h3>
          <p className="text-xs text-slate-500">
            No examinations match your current search or filter criteria.
          </p>
          <button
            onClick={() => { setSearch(''); setSelectedDept('ALL'); setSelectedRoom('ALL'); }}
            className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium cursor-pointer"
          >
            Clear Filters
          </button>
        </div>
      ) : (
        <>
          {/* VIEW MODE 1: Session Grid */}
          {viewMode === 'grid' && (
            <div className="space-y-6">
          {gridData.map(({ date, slots: dateSlots }) => (
            <div key={date} className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-indigo-600" />
                  <h3 className="text-base font-bold text-slate-900 tracking-tight">
                    {new Date(date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                  </h3>
                </div>
                <span className="text-xs text-slate-500 font-mono font-medium">
                  {dateSlots.reduce((acc, s) => acc + s.assignments.length, 0)} exams scheduled
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {dateSlots.map(({ slot, assignments: slotAssignments }) => (
                  <div
                    key={slot.id}
                    className={`p-4 rounded-xl border flex flex-col justify-between ${
                      slot.is_blackout
                        ? 'bg-rose-50/60 border-rose-200'
                        : 'bg-slate-50/80 border-slate-200'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
                          <Clock className="w-3.5 h-3.5 text-indigo-600" />
                          <span>{slot.start_time.slice(0, 5)} - {slot.end_time.slice(0, 5)}</span>
                        </div>
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
                          {slot.period} ({slot.duration_minutes}m)
                        </span>
                      </div>

                      {slotAssignments.length === 0 ? (
                        <div className="py-6 text-center text-xs text-slate-400">
                          No examinations in this session
                        </div>
                      ) : (
                        <div className="space-y-2.5">
                          {slotAssignments.map((a) => (
                            <div
                              key={a.id}
                              className={`p-3 rounded-lg border transition ${
                                a.is_locked
                                  ? 'bg-indigo-50/60 border-indigo-200 hover:border-indigo-300 shadow-xs'
                                  : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
                              }`}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div>
                                  <div className="flex items-center gap-1.5">
                                    <span className="font-bold text-xs text-slate-900">{a.exam_code}</span>
                                    {a.is_locked && (
                                      <span title="Locked Assignment">
                                        <Lock className="w-3 h-3 text-indigo-600" />
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-[11px] text-slate-600 line-clamp-1 mt-0.5">{a.course_name}</p>
                                </div>

                                <button
                                  onClick={() => setEditingAssignment(a)}
                                  className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition cursor-pointer"
                                  title="Edit Assignment"
                                >
                                  <Edit3 className="w-3.5 h-3.5" />
                                </button>
                              </div>

                              <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                                <span className="flex items-center gap-1 font-semibold text-indigo-700">
                                  <Building2 className="w-3 h-3" /> {a.room_code || 'TBA'}
                                </span>
                                <span className="font-medium text-slate-600">{a.assigned_student_count} Students</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* VIEW MODE 2: Room View */}
      {viewMode === 'room' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {rooms.map((room) => {
            const roomAssignments = filteredAssignments.filter((a) => a.room_id === room.id);
            return (
              <div key={room.id} className="bg-white border border-slate-200 rounded-xl p-5 space-y-3 shadow-xs">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">{room.room_code}</h4>
                    <p className="text-xs text-slate-500">{room.name} ({room.building})</p>
                  </div>
                  <span className="text-xs font-mono font-semibold px-2 py-0.5 bg-slate-100 border border-slate-200 rounded text-slate-700">
                    {room.capacity} seats
                  </span>
                </div>

                <div className="space-y-2">
                  {roomAssignments.length === 0 ? (
                    <p className="text-xs text-slate-400 py-4 text-center">No examinations assigned to this room</p>
                  ) : (
                    roomAssignments.map((a) => (
                      <div key={a.id} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs flex justify-between items-center">
                        <div>
                          <div className="font-bold text-slate-900">{a.exam_code}</div>
                          <div className="text-[11px] text-slate-500">{a.date} ({a.start_time?.slice(0, 5)})</div>
                        </div>
                        <span className="text-slate-700 font-medium font-mono">{a.assigned_student_count} std</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* VIEW MODE 3: Department View */}
      {viewMode === 'dept' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {departments.map((dept) => {
            const deptAssignments = filteredAssignments.filter((a) => a.department === dept);
            return (
              <div key={dept} className="bg-white border border-slate-200 rounded-xl p-5 space-y-3 shadow-xs">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <h4 className="font-bold text-sm text-slate-900">{dept}</h4>
                  <span className="text-xs text-slate-500 font-mono font-medium">{deptAssignments.length} examinations</span>
                </div>

                <div className="space-y-2">
                  {deptAssignments.map((a) => (
                    <div key={a.id} className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs flex justify-between items-center">
                      <div>
                        <div className="font-bold text-slate-900">{a.exam_code} - {a.course_name}</div>
                        <div className="text-[11px] text-slate-500 mt-0.5">
                          {a.date} at {a.start_time?.slice(0, 5)} | Room: <strong className="text-indigo-700">{a.room_code}</strong>
                        </div>
                      </div>
                      <span className="text-xs font-mono font-semibold text-slate-700">{a.assigned_student_count} std</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
      </>
      )}

      {/* EDIT ASSIGNMENT MODAL */}
      {editingAssignment && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl w-full max-w-lg p-6 space-y-5 shadow-xl text-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Edit Schedule Assignment</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {editingAssignment.exam_code} — {editingAssignment.course_name}
                </p>
              </div>
              <button
                onClick={() => setEditingAssignment(null)}
                className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                const form = e.currentTarget as any;
                const slotId = form.timeslot_id.value ? parseInt(form.timeslot_id.value) : null;
                const roomId = form.room_id.value ? parseInt(form.room_id.value) : null;
                const isLocked = form.is_locked.checked;

                editMutation.mutate({
                  id: editingAssignment.id,
                  data: {
                    timeslot_id: slotId,
                    room_id: roomId,
                    is_locked: isLocked,
                    force_apply: false,
                  },
                });
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Time Slot</label>
                <select
                  name="timeslot_id"
                  defaultValue={editingAssignment.timeslot_id || ''}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-600"
                >
                  <option value="">Unscheduled</option>
                  {slots.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.date} {s.start_time.slice(0, 5)} ({s.period}, {s.duration_minutes}m) {s.is_blackout ? '[BLACKOUT]' : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Room / Venue</label>
                <select
                  name="room_id"
                  defaultValue={editingAssignment.room_id || ''}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-600"
                >
                  <option value="">Unassigned</option>
                  {rooms.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.room_code} — {r.name} (Cap: {r.capacity})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="is_locked"
                  name="is_locked"
                  defaultChecked={editingAssignment.is_locked}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-0"
                />
                <label htmlFor="is_locked" className="text-xs font-medium text-slate-700">
                  Lock this examination assignment (Preserves slot and room during re-optimization)
                </label>
              </div>

              {editMutation.isError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800">
                  {(editMutation.error as Error).message}
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditingAssignment(null)}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editMutation.isPending}
                  className="px-4 py-2 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-white flex items-center gap-1.5 cursor-pointer shadow-xs"
                >
                  <Save className="w-3.5 h-3.5" />
                  {editMutation.isPending ? 'Verifying...' : 'Save & Validate'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
