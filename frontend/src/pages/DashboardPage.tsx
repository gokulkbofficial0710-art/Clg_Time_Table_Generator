import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { Link } from 'react-router-dom';
import {
  BookOpen, Users, Building2, Clock, CheckCircle2,
  AlertOctagon, Lock, RefreshCw, Download,
  ExternalLink, TrendingUp, ShieldAlert, Award, FlaskConical, CalendarCheck
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: api.getDashboard,
    refetchInterval: 5000,
  });

  const { data: conflicts } = useQuery({
    queryKey: ['conflicts'],
    queryFn: () => api.getConflicts(),
  });

  const demoMutation = useMutation({
    mutationFn: () => api.loadDemoData(),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  const infeasibleMutation = useMutation({
    mutationFn: () => api.loadInfeasibleScenario(),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  const autoResolveMutation = useMutation({
    mutationFn: () => api.autoResolveConflicts(),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  const resetInfeasibleMutation = useMutation({
    mutationFn: () => api.resetInfeasibleScenario(),
    onSuccess: () => queryClient.invalidateQueries(),
  });


  if (isLoading || !dashboard) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3 text-slate-400">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm">Loading examination management system...</p>
        </div>
      </div>
    );
  }

  const totalClashes = dashboard.student_clash_count + dashboard.room_clash_count + dashboard.capacity_violation_count;
  const isPreOptimization = dashboard.quality_score === 0;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Banner / Feasibility Status */}
      <div className={`p-5 rounded-xl border shadow-xs transition ${
        isPreOptimization
          ? 'bg-amber-50/90 border-amber-200 text-amber-950'
          : dashboard.is_valid_timetable
          ? 'bg-emerald-50/90 border-emerald-200 text-emerald-950'
          : 'bg-rose-50/90 border-rose-200 text-rose-950'
      }`}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className={`p-2.5 rounded-lg shrink-0 ${
              isPreOptimization
                ? 'bg-amber-100 text-amber-700'
                : dashboard.is_valid_timetable
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-rose-100 text-rose-700'
            }`}>
              {isPreOptimization ? (
                <Clock className="w-6 h-6" />
              ) : dashboard.is_valid_timetable ? (
                <CheckCircle2 className="w-6 h-6" />
              ) : (
                <AlertOctagon className="w-6 h-6" />
              )}
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-base font-bold text-slate-900">
                  {isPreOptimization
                    ? 'Draft Baseline Loaded — Pre-Optimization State (Quality: 0%)'
                    : dashboard.is_valid_timetable
                    ? `Timetable Optimized & Fully Verified — Quality: ${dashboard.quality_score === 100 ? '100' : dashboard.quality_score.toFixed(1)}%`
                    : 'Attention: Timetable Contains Constraint Violations'}
                </h2>
                <span className={`text-[11px] px-2.5 py-0.5 rounded-full font-semibold uppercase tracking-wider ${
                  isPreOptimization
                    ? 'bg-amber-100 text-amber-800 border border-amber-300'
                    : dashboard.is_valid_timetable
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                    : 'bg-rose-100 text-rose-800 border border-rose-300'
                }`}>
                  {isPreOptimization ? 'Quality: 0% (Pending)' : dashboard.is_valid_timetable ? 'Valid & Optimized' : `${totalClashes} Clashes Detected`}
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                {isPreOptimization
                  ? `Active schedule '${dashboard.active_version_name || 'Baseline'}' is currently in pre-optimization draft state. Click 'Extract Optimized Timetable' to run the scheduler and compute conflict-free exam allocations.`
                  : dashboard.is_valid_timetable
                  ? `Active schedule '${dashboard.active_version_name || 'Active Schedule'}' satisfies student clashing, venue capacity, duration, and room suitability constraints.`
                  : 'Independent validator flagged hard-constraint collisions. Run the schedule optimizer or resolve locks in the Conflict Center.'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {isPreOptimization ? (
              <Link
                to="/optimizer"
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition cursor-pointer"
              >
                <CalendarCheck className="w-3.5 h-3.5 text-indigo-200" />
                <span>Extract Optimized Timetable</span>
              </Link>
            ) : (
              <Link
                to="/optimizer"
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-white shadow-xs transition"
              >
                <CalendarCheck className="w-3.5 h-3.5 text-indigo-300" />
                Re-Optimize Schedule
              </Link>
            )}
            {!isPreOptimization && !dashboard.is_valid_timetable && (
              <Link
                to="/conflicts"
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-rose-100 hover:bg-rose-200 text-rose-900 border border-rose-300 transition"
              >
                <ShieldAlert className="w-3.5 h-3.5" />
                View Diagnostics
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Examinations */}
        <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Examinations</span>
            <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
              <BookOpen className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div className="text-3xl font-bold text-slate-900 tracking-tight">{dashboard.total_exams}</div>
            <span className="text-xs text-slate-600">
              <span className="text-emerald-700 font-semibold">{dashboard.scheduled_exams}</span> scheduled
            </span>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex justify-between text-xs text-slate-500">
            <span>Unscheduled: <strong className="text-slate-800">{dashboard.unscheduled_exams}</strong></span>
            <span>Locked: <strong className="text-indigo-600 font-semibold">{dashboard.locked_exam_count}</strong></span>
          </div>
        </div>

        {/* Card 2: Students */}
        <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Students Enrolled</span>
            <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div className="text-3xl font-bold text-slate-900 tracking-tight">{dashboard.total_students}</div>
            <span className="text-xs text-slate-500">Across 5 Depts</span>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex justify-between text-xs text-slate-500">
            <span>Student Clashes:</span>
            <strong className={dashboard.student_clash_count === 0 ? 'text-emerald-700 font-semibold' : 'text-rose-700 font-semibold'}>
              {dashboard.student_clash_count}
            </strong>
          </div>
        </div>

        {/* Card 3: Rooms & Capacity */}
        <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Rooms Available</span>
            <div className="p-1.5 rounded-lg bg-purple-50 text-purple-600">
              <Building2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div className="text-3xl font-bold text-slate-900 tracking-tight">{dashboard.available_rooms}</div>
            <span className="text-xs text-slate-500">
              <span className="text-slate-700 font-semibold">{dashboard.available_timeslots}</span> Slots
            </span>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex justify-between text-xs text-slate-500">
            <span>Room Overlaps:</span>
            <strong className={dashboard.room_clash_count === 0 ? 'text-emerald-700 font-semibold' : 'text-rose-700 font-semibold'}>
              {dashboard.room_clash_count}
            </strong>
          </div>
        </div>

        {/* Card 4: Quality Score */}
        <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Quality Score</span>
            <div className={`p-1.5 rounded-lg ${dashboard.quality_score === 0 ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'}`}>
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div className="text-3xl font-bold text-slate-900 tracking-tight">
              {dashboard.quality_score === 0 ? (
                <>
                  0<span className="text-lg font-semibold text-slate-500 ml-0.5">%</span>
                </>
              ) : (
                <>
                  {dashboard.quality_score === 100 ? '100' : dashboard.quality_score.toFixed(1)}
                  <span className="text-lg font-semibold text-emerald-600 ml-0.5">%</span>
                </>
              )}
            </div>
            <span className={`text-[11px] font-mono font-semibold px-2 py-0.5 rounded border uppercase ${
              dashboard.quality_score === 0
                ? 'text-amber-800 bg-amber-50 border-amber-200'
                : 'text-emerald-700 bg-emerald-50 border-emerald-200'
            }`}>
              {dashboard.quality_score === 0 ? 'PRE-OPTIMIZATION' : dashboard.solver_status}
            </span>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex justify-between text-xs text-slate-500">
            <span>{dashboard.quality_score === 0 ? 'Solver not yet executed' : 'Soft Penalty Model'}</span>
            <Link to="/analytics" className="text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1">
              Details <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>

      {/* Main Grid: Quick Action Hub & Active Conflict Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Actions Panel */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Optimization Actions</h3>
            <span className="text-[11px] text-slate-500 font-medium">Quick Controls</span>
          </div>

          <div className="space-y-2.5">
            <Link
              to="/optimizer"
              className="w-full flex items-center justify-between p-3 rounded-lg bg-indigo-50/70 hover:bg-indigo-100/70 border border-indigo-200 text-indigo-950 font-medium text-xs transition"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-md bg-indigo-100 text-indigo-700">
                  <CalendarCheck className="w-4 h-4" />
                </div>
                <div className="text-left">
                  <div className="font-semibold text-slate-900">Schedule Optimizer</div>
                  <div className="text-[11px] text-slate-500">Generate conflict-free examination schedule</div>
                </div>
              </div>
              <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
            </Link>

            <Link
              to="/calendar"
              className="w-full flex items-center justify-between p-3 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-800 font-medium text-xs transition"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-md bg-slate-200/70 text-slate-700">
                  <Clock className="w-4 h-4" />
                </div>
                <div className="text-left">
                  <div className="font-semibold text-slate-900">Inspect Calendar Grid</div>
                  <div className="text-[11px] text-slate-500">Filter by room, date, or student</div>
                </div>
              </div>
              <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
            </Link>

            {totalClashes > 0 ? (
              <button
                onClick={() => autoResolveMutation.mutate()}
                disabled={autoResolveMutation.isPending}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-950 font-medium text-xs transition cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-md bg-emerald-100 text-emerald-700">
                    <CheckCircle2 className={`w-4 h-4 ${autoResolveMutation.isPending ? 'animate-spin' : ''}`} />
                  </div>
                  <div className="text-left">
                    <div className="font-semibold text-emerald-950">
                      {autoResolveMutation.isPending ? 'Resolving Violations...' : 'Auto-Resolve All Clashes'}
                    </div>
                    <div className="text-[11px] text-slate-600">Eliminate all {totalClashes} hard violations</div>
                  </div>
                </div>
                <span className="text-[10px] bg-emerald-200/80 px-2 py-0.5 rounded text-emerald-900 font-mono font-semibold">FIX</span>
              </button>
            ) : null}

            {dashboard.locked_exam_count > 1 ? (
              <button
                onClick={() => resetInfeasibleMutation.mutate()}
                disabled={resetInfeasibleMutation.isPending}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-950 font-medium text-xs transition cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-md bg-amber-100 text-amber-700">
                    <RefreshCw className={`w-4 h-4 ${resetInfeasibleMutation.isPending ? 'animate-spin' : ''}`} />
                  </div>
                  <div className="text-left">
                    <div className="font-semibold text-amber-950">Clear Injected Scenario</div>
                    <div className="text-[11px] text-slate-600">Revert conflicting locks to default</div>
                  </div>
                </div>
                <span className="text-[10px] bg-amber-200/80 px-2 py-0.5 rounded text-amber-900 font-mono font-semibold">RESET</span>
              </button>
            ) : (
              <button
                onClick={() => {
                  if (window.confirm("This will inject a test clash to audit conflict detection rules. Continue?")) {
                    infeasibleMutation.mutate();
                  }
                }}
                disabled={infeasibleMutation.isPending}
                className="w-full flex items-center justify-between p-3 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 font-medium text-xs transition cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-md bg-slate-200/70 text-slate-700">
                    <FlaskConical className="w-4 h-4" />
                  </div>
                  <div className="text-left">
                    <div className="font-semibold text-slate-900">Simulate Conflict Test</div>
                    <div className="text-[11px] text-slate-500">Test diagnostics on deliberate clash</div>
                  </div>
                </div>
                <span className="text-[10px] bg-slate-200 px-2 py-0.5 rounded text-slate-700 font-mono font-semibold">TEST</span>
              </button>
            )}
          </div>
        </div>

        {/* Live Diagnostics Summary */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Independent Validation Feed</h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Real-time status of constraints H1 – H9</p>
            </div>
            <div className="flex items-center gap-3">
              {totalClashes > 0 && (
                <button
                  onClick={() => autoResolveMutation.mutate()}
                  disabled={autoResolveMutation.isPending}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition disabled:opacity-50 cursor-pointer"
                >
                  <CheckCircle2 className={`w-3 h-3 ${autoResolveMutation.isPending ? 'animate-spin' : ''}`} />
                  Auto-Resolve
                </button>
              )}
              <Link to="/conflicts" className="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1">
                Full Diagnostics Center <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          <div className="mt-4 space-y-3">
            {isPreOptimization ? (
              <div className="p-8 text-center text-slate-500 flex flex-col items-center justify-center space-y-2 bg-slate-50/50 rounded-lg border border-slate-100">
                <Clock className="w-8 h-8 text-amber-500" />
                <p className="text-sm font-semibold text-slate-800">Draft Baseline — Schedule Unallocated</p>
                <p className="text-xs text-slate-500 max-w-md">
                  The active timetable is in draft pre-optimization baseline state. Hard-constraint conflict audit will monitor examinations once the schedule is extracted.
                </p>
                <Link
                  to="/optimizer"
                  className="mt-2 inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-white shadow-xs transition"
                >
                  <CalendarCheck className="w-3.5 h-3.5 text-indigo-300" />
                  Extract Optimized Timetable
                </Link>
              </div>
            ) : conflicts?.conflicts && conflicts.conflicts.length > 0 ? (
              conflicts.conflicts.slice(0, 3).map((c, i) => (
                <div key={i} className="p-3.5 rounded-lg bg-rose-50/70 border border-rose-200 flex items-start gap-3">
                  <AlertOctagon className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <div className="text-xs space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-rose-900">{c.title}</span>
                      <span className="font-mono text-[10px] px-1.5 py-0.5 bg-rose-200/80 rounded text-rose-800 font-semibold">{c.rule}</span>
                    </div>
                    <p className="text-slate-700">{c.description}</p>
                    <p className="text-slate-900 font-medium text-[11px]">Action: {c.suggested_action}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-slate-500 flex flex-col items-center justify-center space-y-2 bg-slate-50/50 rounded-lg border border-slate-100">
                <CheckCircle2 className="w-8 h-8 text-emerald-600" />
                <p className="text-sm font-semibold text-slate-800">Zero Infeasibilities Detected</p>
                <p className="text-xs text-slate-500 max-w-md">
                  All 9 hard constraints (student non-overlap, room capacity, room non-overlap, duration, locked preservation, features) are mathematically satisfied.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
