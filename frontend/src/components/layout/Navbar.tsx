import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../api/client';
import { GraduationCap, CheckCircle2, AlertOctagon, RefreshCw, Cpu, Download, Calendar } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Navbar: React.FC = () => {
  const queryClient = useQueryClient();
  const { data: dashboard } = useQuery({
    queryKey: ['dashboard'],
    queryFn: api.getDashboard,
    refetchInterval: 5000,
  });

  const demoMutation = useMutation({
    mutationFn: () => api.loadDemoData(),
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
  });

  return (
    <header className="h-16 border-b border-slate-200 bg-white sticky top-0 z-40 px-6 flex items-center justify-between shadow-xs">
      <div className="flex items-center gap-3.5">
        <div className="w-9 h-9 rounded-lg bg-slate-900 text-white flex items-center justify-center shadow-xs shrink-0">
          <GraduationCap className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
              University Examination Scheduling System
            </h1>
          </div>
          <p className="text-[11px] text-slate-500 font-medium">
            Office of the University Registrar • Fall 2026 Academic Term
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {dashboard && (
          <div className="hidden lg:flex items-center gap-3 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-xs">
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500">Active Schedule:</span>
              <span className="font-semibold text-slate-800 truncate max-w-[150px]">
                {dashboard.quality_score === 0 ? 'Draft Baseline (Unallocated)' : (dashboard.active_version_name || 'Official Term Schedule')}
              </span>
            </div>
            <div className="h-3.5 w-[1px] bg-slate-200" />
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500">Validation:</span>
              {dashboard.quality_score === 0 ? (
                <span className="inline-flex items-center gap-1 text-slate-600 font-medium bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                  Pending Generation
                </span>
              ) : dashboard.student_clash_count + dashboard.room_clash_count === 0 ? (
                <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5" /> 0 Clashes (Valid)
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-rose-700 font-semibold bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                  <AlertOctagon className="w-3.5 h-3.5" /> Clashes ({dashboard.student_clash_count + dashboard.room_clash_count})
                </span>
              )}
            </div>
            <div className="h-3.5 w-[1px] bg-slate-200" />
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500">Status:</span>
              {dashboard.quality_score === 0 ? (
                <span className="inline-flex items-center gap-1 font-bold text-slate-600 bg-slate-100 border border-slate-300 px-2 py-0.5 rounded text-[11px]">
                  Unscheduled
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded text-[11px]">
                  {dashboard.quality_score.toFixed(1)}% Score
                </span>
              )}
            </div>
          </div>
        )}

        <div className="flex items-center gap-2">
          <Link
            to="/optimizer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition"
          >
            <Calendar className="w-3.5 h-3.5" />
            <span>Run Optimizer</span>
          </Link>
          <button
            onClick={() => {
              if (window.confirm("Are you sure want to reset all the data?\nReset timetable schedule to unallocated baseline state?")) {
                demoMutation.mutate();
              }
            }}
            disabled={demoMutation.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 shadow-xs transition cursor-pointer"
            title="Reset timetable to unallocated baseline"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${demoMutation.isPending ? 'animate-spin' : ''}`} />
            <span>Reset</span>
          </button>
          <a
            href="/api/export/timetable/pdf"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 shadow-xs transition"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export PDF</span>
          </a>
        </div>
      </div>
    </header>
  );
};
