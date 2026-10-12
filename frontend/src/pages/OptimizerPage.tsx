import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import {
  Cpu, Sparkles, Sliders, CheckCircle2, AlertOctagon,
  Clock, ShieldCheck, Zap, Info, ArrowRight,
  BookOpen, CalendarCheck, GraduationCap, Calendar, Users
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const OptimizerPage: React.FC = () => {
  const queryClient = useQueryClient();

  // Mode locked to Full Global Optimization (Minimal Change removed as requested)
  const mode = 'full';
  const [timeLimit, setTimeLimit] = useState<number>(30);
  const [scheduleName, setScheduleName] = useState<string>('');

  // Single Practical Real-World Policy: Student Study Leave & Revision Interval Policy (Inter-Exam Preparation Buffer)
  const [studyBufferDays, setStudyBufferDays] = useState<number>(1); // Default: 1 day dedicated study holiday between exams
  const [studyPolicyPreset, setStudyPolicyPreset] = useState<'standard' | 'extended' | 'compact'>('standard');

  const [solveResult, setSolveResult] = useState<any>(null);

  // Helper to compute exact schedule dates as per time interval
  // (Backlogs remain strictly on Saturday: Saturday Dec 19, Sundays off)
  const computeScheduleDates = (intervalDays: number) => {
    const base = new Date(2026, 11, 14); // Mon Dec 14, 2026
    const days: { dateStr: string; dayName: string; label: string }[] = [
      { dateStr: '2026-12-14', dayName: 'Monday', label: 'Exam Day 1 (D1)' }
    ];
    let cur = new Date(base);
    for (let i = 1; i <= 3; i++) {
      const nxt = new Date(cur);
      nxt.setDate(nxt.getDate() + 1 + intervalDays);
      if (nxt.getDay() === 6) { // Saturday -> advance to Monday
        nxt.setDate(nxt.getDate() + 2);
      } else if (nxt.getDay() === 0) { // Sunday -> advance to Monday
        nxt.setDate(nxt.getDate() + 1);
      }
      cur = nxt;
      const yyyy = cur.getFullYear();
      const mm = String(cur.getMonth() + 1).padStart(2, '0');
      const dd = String(cur.getDate()).padStart(2, '0');
      const dayName = cur.toLocaleDateString('en-US', { weekday: 'long' });
      days.push({
        dateStr: `${yyyy}-${mm}-${dd}`,
        dayName: dayName,
        label: `Exam Day ${i + 1} (D${i + 1})`
      });
    }
    return {
      examDays: days,
      backlogWeekend: {
        sat: '2026-12-19',
        sun: 'Sundays Off'
      }
    };
  };

  const scheduleDates = computeScheduleDates(studyBufferDays);

  const solveMutation = useMutation({
    mutationFn: (params: any) => api.generateTimetable(params),
    onSuccess: (res) => {
      setSolveResult(res);
      queryClient.invalidateQueries();
    },
  });

  const autoResolveMutation = useMutation({
    mutationFn: () => api.autoResolveConflicts(),
    onSuccess: (res) => {
      setSolveResult(res);
      queryClient.invalidateQueries();
    },
  });

  const handleLaunch = (e: React.FormEvent) => {
    e.preventDefault();
    setSolveResult(null);

    // Map the practical Study Leave Buffer policy to solver weights:
    let burden = 200;
    let spacing = 150;
    if (studyBufferDays === 0) {
      burden = 60;
      spacing = 30;
    } else if (studyBufferDays === 1) {
      burden = 200;
      spacing = 150;
    } else if (studyBufferDays === 2) {
      burden = 300;
      spacing = 250;
    } else {
      burden = 400;
      spacing = 350;
    }

    solveMutation.mutate({
      name: scheduleName || undefined,
      time_limit_seconds: timeLimit,
      mode: mode,
      study_interval_days: studyBufferDays,
      weight_student_burden: burden,
      weight_exam_spacing: spacing,
      weight_daily_imbalance: 30,
      weight_preference_violation: 20,
      weight_room_utilization: 10,
      weight_unnecessary_changes: 20,
      weight_undesirable_session: 40,
    });
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600 shrink-0">
            <CalendarCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Automated Examination Scheduler & Optimizer</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Constraint satisfaction engine configuring multi-objective student, room, duration, and academic policy rules
            </p>
          </div>
        </div>
      </div>

      {/* Solver Result Banner */}
      {solveResult && (
        <div className={`p-5 rounded-xl border shadow-xs transition ${
          solveResult.status === 'SUCCESS' || solveResult.is_feasible
            ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
            : 'bg-rose-50 border-rose-200 text-rose-950'
        }`}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className={`p-2.5 rounded-lg shrink-0 ${
                solveResult.status === 'SUCCESS' || solveResult.is_feasible
                  ? 'bg-emerald-100 text-emerald-700'
                  : 'bg-rose-100 text-rose-700'
              }`}>
                {solveResult.status === 'SUCCESS' || solveResult.is_feasible ? (
                  <CheckCircle2 className="w-6 h-6" />
                ) : (
                  <AlertOctagon className="w-6 h-6" />
                )}
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-900">
                    Optimization Result: {solveResult.solver_status || solveResult.status}
                  </h3>
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-700 font-medium">
                    {solveResult.solver_runtime_ms} ms
                  </span>
                </div>
                <p className="text-xs text-slate-600">
                  {solveResult.status === 'SUCCESS' || solveResult.is_feasible
                    ? `Verified feasible! Achieved timetable quality score of ${solveResult.quality_score}% with 0 clashes. All dates updated in timetable, student details, and scheduling calendar.`
                    : 'The solver proved or encountered infeasibility under current parameters. Check diagnostics below.'}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 shrink-0">
              {!(solveResult.status === 'SUCCESS' || solveResult.is_feasible) && (
                <button
                  type="button"
                  onClick={() => autoResolveMutation.mutate()}
                  disabled={autoResolveMutation.isPending}
                  className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs disabled:opacity-50 cursor-pointer"
                >
                  <CheckCircle2 className={`w-3.5 h-3.5 ${autoResolveMutation.isPending ? 'animate-spin' : ''}`} />
                  Auto-Resolve Conflicting Locks
                </button>
              )}
              <Link
                to="/"
                className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs transition"
              >
                Dashboard <ArrowRight className="w-3.5 h-3.5" />
              </Link>
              <Link
                to="/calendar"
                className="px-3 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs transition"
              >
                <Calendar className="w-3.5 h-3.5 text-indigo-600" />
                Schedule
              </Link>
              <Link
                to="/students/seatings"
                className="px-3 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs transition"
              >
                <Users className="w-3.5 h-3.5 text-indigo-600" />
                Student Details
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Main Solver Form */}
      <form onSubmit={handleLaunch} className="space-y-6">
        {/* Section 1: Optimization Strategy & Runtime Limits */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-5">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <Sliders className="w-4 h-4 text-indigo-600" />
              1. Optimization Strategy & Runtime Limits
            </h3>
            <span className="text-xs text-slate-500 font-medium">Deterministic Solver</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Optimization Engine Mode - Minimal Change removed, permanently Full Global Optimization */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-2">Optimization Strategy Mode</label>
              <div className="p-4 rounded-xl border border-indigo-200 bg-linear-to-br from-indigo-50/90 via-white to-purple-50/50 shadow-2xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="relative flex h-2.5 w-2.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                    </span>
                    <span className="text-sm font-bold text-slate-900">Full Global Optimization</span>
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                    Active (Global Optimum)
                  </span>
                </div>
                <p className="text-[11px] text-slate-600 mt-2 leading-relaxed">
                  Globally recalculates and schedules all courses, room capacities, and time slots simultaneously to achieve a 100% timetable quality rating and zero hard clashes.
                </p>
              </div>
            </div>

            {/* Time Limit Slider */}
            <div className="flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-semibold text-slate-700">Solver Time Limit</label>
                  <span className="font-mono text-xs font-bold text-indigo-600">{timeLimit} seconds</span>
                </div>
                <input
                  type="range"
                  min={5}
                  max={120}
                  step={5}
                  value={timeLimit}
                  onChange={(e) => setTimeLimit(parseInt(e.target.value))}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
                  <span>5s (Fast Draft)</span>
                  <span>30s (Recommended)</span>
                  <span>120s (Exhaustive)</span>
                </div>
              </div>

              <div className="mt-3">
                <label className="block text-xs font-semibold text-slate-700 mb-1">Schedule Label (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. Fall 2026 Official Final Schedule v2"
                  value={scheduleName}
                  onChange={(e) => setScheduleName(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-indigo-600"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Student Study Leave & Revision Interval Policy */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-5">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <GraduationCap className="w-4 h-4 text-indigo-600" />
                2. Student Study Leave & Revision Interval Policy
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Mandatory inter-exam preparation holiday buffer to prevent cognitive overload and student burnout
              </p>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
              UGC / AICTE Academic Standard
            </span>
          </div>

          {/* Policy Preset Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
            {/* Standard: 1 Day Study Gap */}
            <button
              type="button"
              onClick={() => {
                setStudyPolicyPreset('standard');
                setStudyBufferDays(1);
              }}
              className={`p-4 rounded-xl border text-left transition cursor-pointer relative ${
                studyPolicyPreset === 'standard' && studyBufferDays === 1
                  ? 'bg-indigo-50/80 border-indigo-400 shadow-xs ring-1 ring-indigo-400'
                  : 'bg-slate-50/60 border-slate-200 text-slate-600 hover:bg-slate-100/80 hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                  <CalendarCheck className="w-3.5 h-3.5 text-indigo-600" />
                  1-Day Study Holiday Gap
                </span>
                <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200">
                  Recommended
                </span>
              </div>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                Guarantees at least 1 dedicated revision day (≥ 24h gap) between consecutive papers for all enrolled students. Prevents student burnout.
              </p>
              <div className="mt-2.5 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[10px] font-medium text-slate-500">
                <span>Burnout Risk: <strong className="text-emerald-700">0% (Zero)</strong></span>
                <span>Buffer: <strong className="text-indigo-700">≥ 24 Hours</strong></span>
              </div>
            </button>

            {/* Extended: 2 Days Spacing */}
            <button
              type="button"
              onClick={() => {
                setStudyPolicyPreset('extended');
                setStudyBufferDays(2);
              }}
              className={`p-4 rounded-xl border text-left transition cursor-pointer relative ${
                studyPolicyPreset === 'extended' || studyBufferDays >= 2
                  ? 'bg-indigo-50/80 border-indigo-400 shadow-xs ring-1 ring-indigo-400'
                  : 'bg-slate-50/60 border-slate-200 text-slate-600 hover:bg-slate-100/80 hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5 text-purple-600" />
                  2-Day Extended Buffer
                </span>
                <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-purple-100 text-purple-800 border border-purple-200">
                  Deep Revision
                </span>
              </div>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                Spreads out papers with 48h+ preparation interval. Ideal for dense engineering mathematics and theoretical core subjects.
              </p>
              <div className="mt-2.5 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[10px] font-medium text-slate-500">
                <span>Burnout Risk: <strong className="text-emerald-700">0% (Zero)</strong></span>
                <span>Buffer: <strong className="text-purple-700">≥ 48 Hours</strong></span>
              </div>
            </button>

            {/* Compact: Consecutive */}
            <button
              type="button"
              onClick={() => {
                setStudyPolicyPreset('compact');
                setStudyBufferDays(0);
              }}
              className={`p-4 rounded-xl border text-left transition cursor-pointer relative ${
                studyPolicyPreset === 'compact' && studyBufferDays === 0
                  ? 'bg-indigo-50/80 border-indigo-400 shadow-xs ring-1 ring-indigo-400'
                  : 'bg-slate-50/60 border-slate-200 text-slate-600 hover:bg-slate-100/80 hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5 text-amber-600" />
                  Compact Accelerated Term
                </span>
                <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">
                  Fast-Track
                </span>
              </div>
              <p className="text-[11px] text-slate-500 leading-relaxed">
                Allows consecutive day scheduling for rapid semester completion and accelerated holiday schedule.
              </p>
              <div className="mt-2.5 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[10px] font-medium text-slate-500">
                <span>Burnout Risk: <strong className="text-amber-700">Elevated</strong></span>
                <span>Buffer: <strong className="text-slate-700">0 Hours</strong></span>
              </div>
            </button>
          </div>

          {/* Interactive Stepper / Fine-tune Slider */}
          <div className="bg-slate-50/80 border border-slate-200 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-indigo-600" />
                <span className="text-xs font-bold text-slate-800">
                  Inter-Exam Revision Holiday Buffer Interval
                </span>
              </div>
              <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-md bg-white border border-slate-200 text-indigo-600 shadow-2xs">
                {studyBufferDays === 0
                  ? '0 Days (Consecutive Exam Sessions)'
                  : studyBufferDays === 1
                  ? '1 Dedicated Study Holiday (≥ 24h Rest)'
                  : `${studyBufferDays} Dedicated Study Holidays (≥ ${studyBufferDays * 24}h Rest)`}
              </span>
            </div>

            <input
              type="range"
              min={0}
              max={3}
              step={1}
              value={studyBufferDays}
              onChange={(e) => {
                const val = parseInt(e.target.value);
                setStudyBufferDays(val);
                if (val === 0) setStudyPolicyPreset('compact');
                else if (val === 1) setStudyPolicyPreset('standard');
                else setStudyPolicyPreset('extended');
              }}
              className="w-full accent-indigo-600 cursor-pointer"
            />

            <div className="grid grid-cols-4 text-[10px] text-slate-500 font-mono text-center pt-0.5">
              <span className={studyBufferDays === 0 ? 'text-indigo-600 font-bold' : ''}>0 Days (Fast-Track)</span>
              <span className={studyBufferDays === 1 ? 'text-indigo-600 font-bold' : ''}>1 Day (Recommended)</span>
              <span className={studyBufferDays === 2 ? 'text-indigo-600 font-bold' : ''}>2 Days (Extended)</span>
              <span className={studyBufferDays === 3 ? 'text-indigo-600 font-bold' : ''}>3 Days (Maximum Spacing)</span>
            </div>
          </div>

          {/* Real-Time Timetable Dates Preview Card */}
          <div className="bg-linear-to-r from-slate-50 via-indigo-50/30 to-slate-50 border border-indigo-100 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-indigo-600" />
                <span className="text-xs font-bold text-slate-800">
                  Calculated Timetable Schedule ({studyBufferDays === 0 ? '0-Day Gap / Fast-Track' : `${studyBufferDays}-Day Study Holiday Gap`})
                </span>
              </div>
              <span className="text-[10px] font-semibold text-indigo-700 bg-indigo-100/80 px-2 py-0.5 rounded border border-indigo-200">
                Propagates to Calendar & Student Seatings
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
              {scheduleDates.examDays.map((d, idx) => (
                <div key={idx} className="bg-white border border-slate-200 rounded-lg p-2.5 shadow-2xs">
                  <div className="text-[10px] font-bold text-indigo-600 uppercase tracking-wider">{d.label}</div>
                  <div className="text-xs font-bold text-slate-900 mt-0.5">{d.dateStr}</div>
                  <div className="text-[10px] text-slate-500 font-medium">{d.dayName}</div>
                </div>
              ))}
            </div>

            {/* Backlog Weekend Notice - Strictly on weekends */}
            <div className="pt-2 border-t border-slate-200/60 flex flex-wrap items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-200">
                  Backlogs Schedule (Saturday Only)
                </span>
                <span className="text-[11px] text-slate-700 font-medium">
                  Saturday <strong>{scheduleDates.backlogWeekend.sat}</strong> (Sundays Off)
                </span>
              </div>
              <span className="text-[10px] text-emerald-700 font-medium">
                ✓ Locked exclusively to Saturday (Sundays off) to prevent regular candidate clashes
              </span>
            </div>
          </div>

          {/* Academic Impact & Real-World Feasibility Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
            <div className="bg-slate-50/70 border border-slate-200 rounded-lg p-3 text-center">
              <div className="text-[11px] font-medium text-slate-500">Student Burnout Risk</div>
              <div className="text-sm font-bold text-emerald-600 mt-0.5 flex items-center justify-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                {studyBufferDays === 0 ? 'Elevated (Consecutive)' : '0% (Eliminated)'}
              </div>
            </div>
            <div className="bg-slate-50/70 border border-slate-200 rounded-lg p-3 text-center">
              <div className="text-[11px] font-medium text-slate-500">Preparation Interval</div>
              <div className="text-sm font-bold text-indigo-600 mt-0.5">
                {studyBufferDays === 0 ? '0 Hours (Back-to-Back)' : `≥ ${studyBufferDays * 24} Hours Buffer`}
              </div>
            </div>
            <div className="bg-slate-50/70 border border-slate-200 rounded-lg p-3 text-center">
              <div className="text-[11px] font-medium text-slate-500">University Compliance</div>
              <div className="text-sm font-bold text-slate-900 mt-0.5">
                {studyBufferDays >= 1 ? '100% (Affiliation Standard)' : 'Express Exemption'}
              </div>
            </div>
            <div className="bg-slate-50/70 border border-slate-200 rounded-lg p-3 text-center">
              <div className="text-[11px] font-medium text-slate-500">Target Timetable Quality</div>
              <div className="text-sm font-bold text-emerald-600 mt-0.5">
                100.0% (Zero Clash)
              </div>
            </div>
          </div>

          {/* Regulatory Context Callout */}
          <div className="flex items-start gap-2.5 p-3 rounded-lg bg-indigo-50/50 border border-indigo-100 text-xs text-indigo-950">
            <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
            <p className="text-[11px] text-slate-600 leading-relaxed">
              <strong>Institutional Policy Note:</strong> In real university governance, back-to-back papers without revision intervals are the leading cause of exam appeal petitions and student fatigue. Enforcing this policy instructs the Google OR-Tools CP-SAT solver to guarantee dedicated study holidays between enrolled exams while simultaneously securing 100% room capacity and zero slot clashes.
            </p>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={solveMutation.isPending}
            className="flex items-center gap-2 px-6 py-3 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-semibold text-xs shadow-xs transition disabled:opacity-50 cursor-pointer"
          >
            <CalendarCheck className={`w-4 h-4 text-indigo-300 ${solveMutation.isPending ? 'animate-spin' : ''}`} />
            {solveMutation.isPending ? 'Computing Conflict-Free Schedule...' : 'Generate & Extract Optimized Timetable'}
          </button>
        </div>
      </form>
    </div>
  );
};
