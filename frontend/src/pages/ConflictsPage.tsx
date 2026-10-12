import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import {
  AlertTriangle, ShieldAlert, CheckCircle2, RefreshCw,
  Filter, ArrowRight, Lightbulb, ExternalLink, Clock, CalendarCheck
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const ConflictsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');
  const [selectedRule, setSelectedRule] = useState('ALL');

  const { data: dashboard } = useQuery({
    queryKey: ['dashboard'],
    queryFn: api.getDashboard,
  });

  const isPreOptimization = dashboard ? dashboard.quality_score === 0 : false;

  const { data: conflictData, isLoading, refetch } = useQuery({
    queryKey: ['conflicts-page', selectedSeverity, selectedRule],
    queryFn: () => api.getConflicts({
      severity: selectedSeverity !== 'ALL' ? selectedSeverity : undefined,
      rule: selectedRule !== 'ALL' ? selectedRule : undefined,
    }),
  });

  const validateMutation = useMutation({
    mutationFn: () => api.validateTimetable(),
    onSuccess: () => {
      refetch();
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });

  const autoResolveMutation = useMutation({
    mutationFn: () => api.autoResolveConflicts(),
    onSuccess: () => {
      refetch();
      queryClient.invalidateQueries();
    },
  });

  const conflicts = conflictData?.conflicts || [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white border border-slate-200 p-5 rounded-xl shadow-xs">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-600" />
            Conflict Diagnostics & Feasibility Center
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Independent constraint violation detector, resource bottleneck analysis, and actionable remediation steps
          </p>
        </div>

        <button
          onClick={() => validateMutation.mutate()}
          disabled={validateMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg text-xs font-semibold shadow-xs transition self-start md:self-auto cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${validateMutation.isPending ? 'animate-spin' : ''}`} />
          Run Independent Verification
        </button>
      </div>

      {/* Status Bar */}
      <div className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs ${
        isPreOptimization
          ? 'bg-amber-50 border-amber-200 text-amber-950'
          : conflictData?.is_feasible
          ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
          : 'bg-rose-50 border-rose-200 text-rose-950'
      }`}>
        <div className="flex items-center gap-3">
          {isPreOptimization ? (
            <Clock className="w-5 h-5 text-amber-600 shrink-0" />
          ) : conflictData?.is_feasible ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
          )}
          <div>
            <span className="font-bold text-sm text-slate-900">
              {isPreOptimization
                ? 'Draft Baseline Loaded — Schedule Unallocated'
                : conflictData?.is_feasible
                ? 'All Hard Constraints Satisfied (Feasible)'
                : `${conflictData?.hard_violations_count || conflicts.length} Active Hard Constraint Violations Detected`}
            </span>
            <p className="text-xs text-slate-600 mt-0.5">
              {isPreOptimization
                ? 'Zero clashes or collisions detected. Examinations are unallocated pending optimization.'
                : conflictData?.is_feasible
                ? 'No student clashes, room overlaps, or venue capacity breaches found.'
                : 'The timetable cannot be deployed until all critical hard constraints are resolved.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {!isPreOptimization && !conflictData?.is_feasible && (
            <button
              onClick={() => autoResolveMutation.mutate()}
              disabled={autoResolveMutation.isPending}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs transition disabled:opacity-50 cursor-pointer"
            >
              <CheckCircle2 className={`w-3.5 h-3.5 ${autoResolveMutation.isPending ? 'animate-spin' : ''}`} />
              {autoResolveMutation.isPending ? 'Resolving Violations...' : 'Auto-Resolve Violations'}
            </button>
          )}

          <Link
            to="/optimizer"
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-white shadow-xs shrink-0"
          >
            <CalendarCheck className="w-3.5 h-3.5 text-indigo-300" />
            {isPreOptimization ? 'Extract Optimized Timetable' : 'Launch Optimizer'}
          </Link>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="flex flex-wrap items-center gap-3 bg-white border border-slate-200 p-4 rounded-xl shadow-xs text-xs">
        <div className="flex items-center gap-2">
          <span className="text-slate-500 font-medium">Severity:</span>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-slate-900 focus:outline-none focus:border-indigo-600"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="FATAL">Fatal Infeasibility</option>
            <option value="WARNING">Warning</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-500 font-medium">Constraint Rule:</span>
          <select
            value={selectedRule}
            onChange={(e) => setSelectedRule(e.target.value)}
            className="bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-slate-900 focus:outline-none focus:border-indigo-600"
          >
            <option value="ALL">All Rules (H1-H9)</option>
            <option value="H1">H1: Student Clashes</option>
            <option value="H2">H2: Room Capacity</option>
            <option value="H3">H3: Room Availability</option>
            <option value="H4">H4: Duration Exceeded</option>
            <option value="H5">H5: Blackout Dates</option>
            <option value="H6">H6: Locked Preserved</option>
            <option value="H7">H7: Room Suitability</option>
            <option value="H9">H9: Assignment Completeness</option>
          </select>
        </div>
      </div>

      {/* Conflict List */}
      <div className="space-y-4">
        {isPreOptimization ? (
          <div className="bg-white border border-slate-200 rounded-xl p-12 text-center flex flex-col items-center justify-center space-y-3 shadow-xs">
            <Clock className="w-12 h-12 text-amber-500" />
            <h3 className="text-base font-bold text-slate-900">Draft Baseline State — No Constraint Clashes</h3>
            <p className="text-xs text-slate-500 max-w-md">
              The schedule is in unallocated draft baseline state. Constraint rules (H1–H9) are active and will audit for conflicts once the examination schedule is extracted.
            </p>
            <Link
              to="/optimizer"
              className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-white shadow-xs transition"
            >
              <CalendarCheck className="w-3.5 h-3.5 text-indigo-300" />
              Extract Optimized Timetable
            </Link>
          </div>
        ) : conflicts.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-xl p-12 text-center flex flex-col items-center justify-center space-y-3 shadow-xs">
            <CheckCircle2 className="w-12 h-12 text-emerald-600" />
            <h3 className="text-base font-bold text-slate-900">Zero Conflict Infeasibilities</h3>
            <p className="text-xs text-slate-500 max-w-md">
              Every scheduled examination strictly obeys student cohort non-overlap, room seating capacities, room equipment suitability, and duration limits.
            </p>
          </div>
        ) : (
          conflicts.map((c, i) => (
            <div
              key={i}
              className="bg-white border border-slate-200 rounded-xl p-5 space-y-3 hover:border-slate-300 shadow-xs transition"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                    c.severity === 'CRITICAL' || c.severity === 'FATAL'
                      ? 'bg-rose-100 text-rose-800 border-rose-200'
                      : 'bg-amber-100 text-amber-800 border-amber-200'
                  }`}>
                    {c.severity} • {c.rule}
                  </span>
                  <h4 className="text-sm font-bold text-slate-900">{c.title}</h4>
                </div>

                {c.date && (
                  <span className="text-xs text-slate-500 font-mono">Date: {c.date}</span>
                )}
              </div>

              <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-200">
                {c.description}
              </p>

              <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-2 text-slate-800">
                  <Lightbulb className="w-4 h-4 shrink-0 text-amber-500" />
                  <span><strong>Recommended Resolution:</strong> {c.suggested_action}</span>
                </div>

                {c.exam_code && (
                  <Link
                    to={`/calendar?search=${encodeURIComponent(c.exam_code)}`}
                    className="flex items-center gap-1 font-semibold text-indigo-600 hover:text-indigo-800 shrink-0"
                  >
                    Locate on Calendar <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
