import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { Room } from '../types';
import {
  Building2, Plus, Edit2, Trash2, CheckCircle2,
  AlertTriangle, Calendar, X, Eye, ShieldCheck
} from 'lucide-react';

export const RoomsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingRoom, setEditingRoom] = useState<Room | null>(null);
  const [selectedOccupancyRoom, setSelectedOccupancyRoom] = useState<Room | null>(null);

  const { data: rooms = [], isLoading } = useQuery({
    queryKey: ['rooms'],
    queryFn: api.getRooms,
  });

  const { data: occupancyData } = useQuery({
    queryKey: ['room-occupancy', selectedOccupancyRoom?.id],
    queryFn: () => selectedOccupancyRoom ? api.getRoomOccupancy(selectedOccupancyRoom.id) : Promise.resolve(null),
    enabled: !!selectedOccupancyRoom,
  });

  const saveMutation = useMutation({
    mutationFn: ({ id, data }: { id?: number; data: any }) =>
      id ? api.updateRoom(id, data) : api.createRoom(data),
    onSuccess: () => {
      setIsAddModalOpen(false);
      setEditingRoom(null);
      queryClient.invalidateQueries({ queryKey: ['rooms'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteRoom(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['rooms'] }),
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white border border-slate-200 p-5 rounded-xl shadow-xs">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-indigo-600" />
            Rooms, Venues & Examination Facilities
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Seating capacities, equipment specifications, maintenance blackouts, and venue occupancy schedules
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-xs transition self-start md:self-auto cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          Add Venue / Room
        </button>
      </div>

      {/* Room Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {rooms.map((room) => (
          <div key={room.id} className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col justify-between space-y-4 hover:border-slate-300 shadow-xs transition">
            <div>
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-base text-slate-900">{room.room_code}</span>
                    {room.is_available ? (
                      <span className="w-2 h-2 rounded-full bg-emerald-500" title="Active & Available" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-rose-500" title="Unavailable" />
                    )}
                  </div>
                  <h4 className="text-xs font-semibold text-slate-700 mt-0.5">{room.name}</h4>
                  <p className="text-[11px] text-slate-500">{room.building}</p>
                </div>

                <div className="text-right">
                  <div className="text-2xl font-bold font-mono text-slate-900 tracking-tight">{room.capacity}</div>
                  <span className="text-[10px] uppercase font-semibold text-slate-500">Seats</span>
                </div>
              </div>

              {/* Features Tags */}
              <div className="mt-4 pt-3 border-t border-slate-100 space-y-2">
                <div className="text-[11px] text-slate-500 font-medium">Equipped Features:</div>
                <div className="flex flex-wrap gap-1.5">
                  {room.features.length > 0 ? (
                    room.features.map((f, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-md bg-slate-100 border border-slate-200 text-[10px] text-slate-700 font-medium">
                        {f}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-400">Standard Desks Only</span>
                  )}
                </div>

                {room.blackout_intervals.length > 0 && (
                  <div className="mt-2 p-2 rounded-lg bg-amber-50 border border-amber-200 text-[11px] text-amber-900 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-amber-600" />
                    <span>Maintenance: {room.blackout_intervals[0].reason || 'Blackout'} ({room.blackout_intervals[0].date})</span>
                  </div>
                )}
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
              <button
                onClick={() => setSelectedOccupancyRoom(room)}
                className="flex items-center gap-1.5 text-xs text-indigo-700 hover:text-indigo-900 font-semibold cursor-pointer"
              >
                <Eye className="w-3.5 h-3.5" />
                View Occupancy
              </button>

              <div className="flex items-center gap-1">
                <button
                  onClick={() => setEditingRoom(room)}
                  className="p-1.5 text-slate-400 hover:text-slate-700 rounded hover:bg-slate-100 cursor-pointer"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => {
                    if (confirm(`Delete room ${room.room_code}?`)) {
                      deleteMutation.mutate(room.id);
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

      {/* Room Occupancy Modal */}
      {selectedOccupancyRoom && occupancyData && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl w-full max-w-xl p-6 space-y-4 shadow-xl max-h-[85vh] flex flex-col text-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">Occupancy Schedule</h3>
                <p className="text-xs text-slate-500">{selectedOccupancyRoom.room_code} — {selectedOccupancyRoom.name} (Capacity: {selectedOccupancyRoom.capacity})</p>
              </div>
              <button onClick={() => setSelectedOccupancyRoom(null)} className="p-1 text-slate-400 hover:text-slate-700 cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="overflow-y-auto space-y-2.5 flex-1 pr-1">
              {occupancyData.bookings.length === 0 ? (
                <p className="text-xs text-slate-400 py-8 text-center">No examinations scheduled in this room.</p>
              ) : (
                occupancyData.bookings.map((b: any, idx: number) => (
                  <div key={idx} className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900">{b.exam_code} — {b.course_name}</span>
                      <span className="font-mono text-indigo-700 font-semibold">{b.occupancy_rate}% Full</span>
                    </div>
                    <div className="flex items-center justify-between text-slate-500 text-[11px]">
                      <span>{b.date} • {b.start_time.slice(0, 5)} - {b.end_time.slice(0, 5)} ({b.period})</span>
                      <span>{b.assigned_students} / {b.capacity} Seats Allocated</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Add / Edit Room Modal */}
      {(isAddModalOpen || editingRoom) && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl w-full max-w-md p-6 space-y-4 shadow-xl text-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">
                {editingRoom ? 'Edit Room / Venue' : 'Add New Venue'}
              </h3>
              <button
                onClick={() => { setIsAddModalOpen(false); setEditingRoom(null); }}
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
                  room_code: form.room_code.value,
                  name: form.name.value,
                  building: form.building.value,
                  capacity: parseInt(form.capacity.value),
                  is_available: form.is_available.checked,
                  features: form.features.value ? form.features.value.split(',').map((s: string) => s.trim()) : [],
                };
                saveMutation.mutate({ id: editingRoom?.id, data });
              }}
              className="space-y-3 text-xs"
            >
              <div>
                <label className="block text-slate-700 font-medium mb-1">Room Code</label>
                <input
                  name="room_code"
                  defaultValue={editingRoom?.room_code || ''}
                  placeholder="HALL-101"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Venue Name</label>
                <input
                  name="name"
                  defaultValue={editingRoom?.name || ''}
                  placeholder="Lecture Hall 101"
                  required
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Building</label>
                  <input
                    name="building"
                    defaultValue={editingRoom?.building || 'Main Campus'}
                    required
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Capacity</label>
                  <input
                    name="capacity"
                    type="number"
                    min={1}
                    defaultValue={editingRoom?.capacity || 50}
                    required
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">Features (comma-separated)</label>
                <input
                  name="features"
                  defaultValue={editingRoom?.features.join(', ') || ''}
                  placeholder="Computers, Projector, Wheelchair Access"
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
                />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="is_available"
                  name="is_available"
                  defaultChecked={editingRoom ? editingRoom.is_available : true}
                  className="rounded border-slate-300 text-indigo-600"
                />
                <label htmlFor="is_available" className="text-slate-700">
                  Room is currently active and available for booking
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => { setIsAddModalOpen(false); setEditingRoom(null); }}
                  className="px-4 py-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saveMutation.isPending}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-semibold shadow-xs cursor-pointer"
                >
                  {saveMutation.isPending ? 'Saving...' : 'Save Venue'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
