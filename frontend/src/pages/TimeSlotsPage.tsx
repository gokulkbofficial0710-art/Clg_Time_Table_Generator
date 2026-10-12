import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { TimeSlot } from '../types';
import {
  Clock, Plus, Edit2, Trash2, AlertOctagon, CheckCircle2,
  Calendar, X, ShieldAlert
} from 'lucide-react';

export const TimeSlotsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingSlot, setEditingSlot] = useState<TimeSlot | null>(null);

  const { data: slots = [], isLoading } = useQuery({
    queryKey: ['timeslots'],
    queryFn: api.getTimeSlots,
  });

  const saveMutation = useMutation({
    mutationFn: ({ id, data }: { id?: number; data: any }) =>
      id ? api.updateTimeSlot(id, data) : api.createTimeSlot(data),
    onSuccess: () => {
      setIsAddModalOpen(false);
      setEditingSlot(null);
      queryClient.invalidateQueries({ queryKey: ['timeslots'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteTimeSlot(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['timeslots'] }),
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white border border-slate-200 p-5 rounded-xl shadow-xs">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-600" />
            Time Slots & Examination Periods
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Permitted scheduling windows, session durations, and institutional blackout dates
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-xs transition self-start md:self-auto cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          Add Time Slot
        </button>
      </div>

      {/* Slots Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {slots.map((slot) => (
          <div
            key={slot.id}
            className={`p-5 rounded-xl border flex flex-col justify-between space-y-4 shadow-xs transition ${
              slot.is_blackout
                ? 'bg-rose-50/70 border-rose-200 text-rose-950'
                : 'bg-white border-slate-200 hover:border-slate-300'
            }`}
          >
            <div>
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-sm text-slate-900">{slot.slot_code}</span>
                    {slot.is_blackout ? (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200">
                        BLACKOUT
                      </span>
                    ) : (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700">
                        {slot.period}
                      </span>
                    )}
                  </div>
                  <div className="text-sm font-semibold text-slate-800 mt-1 flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-indigo-600" />
                    <span>{slot.date}</span>
                  </div>
                </div>

                <div className="text-right">
                  <span className="font-mono text-xl font-bold text-slate-900">{slot.duration_minutes}m</span>
                  <span className="block text-[10px] text-slate-500 uppercase font-semibold">Max Duration</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 space-y-1 text-xs">
                <div className="text-slate-700 font-mono">
                  Time: <strong className="text-slate-900">{slot.start_time.slice(0, 5)} — {slot.end_time.slice(0, 5)}</strong>
                </div>
                {slot.blackout_reason && (
                  <div className="text-rose-700 font-medium text-[11px] mt-1">
                    Reason: {slot.blackout_reason}
                  </div>
                )}
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] text-slate-500 font-mono">
                {slot.is_available && !slot.is_blackout ? 'Available for booking' : 'Excluded from solver'}
              </span>

              <div className="flex items-center gap-1">
                <button
                  onClick={() => setEditingSlot(slot)}
                  className="p-1.5 text-slate-400 hover:text-slate-700 rounded hover:bg-slate-100 cursor-pointer"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => {
                    if (confirm(`Delete slot ${slot.slot_code}?`)) {
                      deleteMutation.mutate(slot.id);
                    }
                  }}
                  className="p-1.5 text-slate-400 hover:text-rose-600 rounded hover:bg-rose-50 cursor-pointer"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add / Edit Time Slot Modal */}
      {(isAddModalOpen || editingSlot) && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl w-full max-w-md p-6 space-y-4 shadow-xl text-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">
                {editingSlot ? 'Edit Time Slot' : 'Add New Time Slot'}
              </h3>
              <button
                onClick={() => { setIsAddModalOpen(false); setEditingSlot(null); }}
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
                  slot_code: form.slot_code.value,
                  date: form.date.value,
                  start_time: form.start_time.value,
                  end_time: form.end_time.value,
                  duration_minutes: parseInt(form.duration_minutes.value),
                  period: form.period.value,
                  is_available: form.is_available.checked,
                  is_blackout: form.is_blackout.checked,
                  blackout_reason: form.blackout_reason.value || null,
                };
                saveMutation.mutate({ id: editingSlot?.id, data });
              }}
              className="space-y-3 text-xs"
            >
              <div>
                <label className="block text-slate-700 font-medium mb-1">Slot Code</label>
                <input
                  name="slot_code"
                  defaultValue={editingSlot?.slot_code || ''}
                  placeholder="SLOT-D1-M"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Date</label>
                <input
                  name="date"
                  type="date"
                  defaultValue={editingSlot?.date || '2026-12-14'}
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Start Time</label>
                  <input
                    name="start_time"
                    type="time"
                    defaultValue={editingSlot?.start_time ? editingSlot.start_time.slice(0, 5) : '09:00'}
                    required
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">End Time</label>
                  <input
                    name="end_time"
                    type="time"
                    defaultValue={editingSlot?.end_time ? editingSlot.end_time.slice(0, 5) : '12:00'}
                    required
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Duration (minutes)</label>
                  <input
                    name="duration_minutes"
                    type="number"
                    defaultValue={editingSlot?.duration_minutes || 180}
                    required
                    min={15}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Period</label>
                  <select
                    name="period"
                    defaultValue={editingSlot?.period || 'Morning'}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                  >
                    <option value="Morning">Morning</option>
                    <option value="Afternoon">Afternoon</option>
                    <option value="Evening">Evening</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="is_available"
                  name="is_available"
                  defaultChecked={editingSlot ? editingSlot.is_available : true}
                  className="rounded border-slate-300 text-indigo-600"
                />
                <label htmlFor="is_available" className="text-slate-700">
                  Available for scheduling
                </label>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="is_blackout"
                  name="is_blackout"
                  defaultChecked={editingSlot ? editingSlot.is_blackout : false}
                  className="rounded border-slate-300 text-rose-600"
                />
                <label htmlFor="is_blackout" className="text-rose-700 font-medium">
                  Mark as Institutional Blackout / Holiday
                </label>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Blackout Reason (if applicable)</label>
                <input
                  name="blackout_reason"
                  defaultValue={editingSlot?.blackout_reason || ''}
                  placeholder="e.g. University Convocation Day"
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => { setIsAddModalOpen(false); setEditingSlot(null); }}
                  className="px-4 py-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saveMutation.isPending}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-semibold shadow-xs cursor-pointer"
                >
                  {saveMutation.isPending ? 'Saving...' : 'Save Time Slot'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
