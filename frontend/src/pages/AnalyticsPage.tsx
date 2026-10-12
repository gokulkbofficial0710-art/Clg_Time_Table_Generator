import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend, Cell, PieChart, Pie
} from 'recharts';
import {
  BarChart3, Award, TrendingUp, TrendingDown, ShieldCheck,
  CheckCircle2, ArrowRight, ArrowUpRight, ArrowDownRight, Minus
} from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const { data: dashboard } = useQuery({
    queryKey: ['dashboard'],
    queryFn: api.getDashboard,
  });

  const { data: distributions } = useQuery({
    queryKey: ['distributions'],
    queryFn: api.getDistributions,
  });

  const { data: comparison } = useQuery({
    queryKey: ['comparison'],
    queryFn: () => api.compareVersions(),
  });

  const dateData = distributions?.dates || [];
  const roomData = distributions?.rooms || [];
  const loadData = distributions?.student_loads || [];

  const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ec4899'];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white border border-slate-200 p-5 rounded-xl shadow-xs">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            Timetable Quality Metrics & Comparative Analytics
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Quantitative measurement of soft-constraint fulfillment and baseline schedule benchmarking
          </p>
        </div>

        {dashboard && (
          <div className="flex items-center gap-2 bg-slate-50 px-4 py-2 rounded-lg border border-slate-200 font-mono text-xs">
            <span className="text-slate-500 font-medium">Quality Score:</span>
            {dashboard.quality_score === 0 ? (
              <span className="text-amber-700 font-bold text-sm">0% (Pre-Optimization)</span>
            ) : (
              <span className="text-emerald-700 font-bold text-sm">{dashboard.quality_score.toFixed(1)}%</span>
            )}
          </div>
        )}
      </div>

      {/* Baseline Comparison Table */}
      {comparison && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Baseline vs Optimized Timetable Benchmarking
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Comparing <strong>{comparison.baseline_version_name}</strong> vs <strong>{comparison.current_version_name}</strong>
              </p>
            </div>
            <span className="text-xs font-mono text-indigo-700 bg-indigo-50 border border-indigo-200 px-2.5 py-1 rounded-md font-semibold">
              Verified Delta
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-3 px-4">Quality Indicator</th>
                  <th className="py-3 px-4">Baseline Schedule</th>
                  <th className="py-3 px-4">Optimized Schedule</th>
                  <th className="py-3 px-4">Absolute Change</th>
                  <th className="py-3 px-4">% Change</th>
                  <th className="py-3 px-4 text-right">Verdict</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {comparison.comparisons.map((c, i) => (
                  <tr key={i} className="hover:bg-slate-50/70 transition">
                    <td className="py-3 px-4 font-semibold text-slate-900">{c.metric_label}</td>
                    <td className="py-3 px-4 font-mono text-slate-500">{c.baseline_value}</td>
                    <td className="py-3 px-4 font-mono font-bold text-slate-900">{c.current_value}</td>
                    <td className="py-3 px-4 font-mono text-slate-700">
                      {c.absolute_diff > 0 ? `+${c.absolute_diff}` : c.absolute_diff}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-700">
                      {c.percentage_change !== null && c.percentage_change !== undefined
                        ? `${c.percentage_change > 0 ? '+' : ''}${c.percentage_change}%`
                        : '—'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {c.is_improvement ? (
                        <span className="inline-flex items-center gap-1 font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 text-[11px]">
                          <ArrowUpRight className="w-3.5 h-3.5" /> Improved
                        </span>
                      ) : c.absolute_diff === 0 ? (
                        <span className="inline-flex items-center gap-1 text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 text-[11px]">
                          <Minus className="w-3.5 h-3.5" /> Maintained
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200 text-[11px]">
                          <ArrowDownRight className="w-3.5 h-3.5" /> Trade-off
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Examination Distribution per Date */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Daily Examination Load Distribution</h4>
            <span className="text-xs text-slate-500 font-mono font-medium">Exams / Day</span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dateData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1', borderRadius: '8px', fontSize: '12px', color: '#0f172a', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Bar dataKey="exam_count" name="Exams" fill="#4f46e5" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Room Utilization Percentage */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Venue Seating Utilization Rate</h4>
            <span className="text-xs text-slate-500 font-mono font-medium">% Usable Seats Filled</span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={roomData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="room_code" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} unit="%" domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1', borderRadius: '8px', fontSize: '12px', color: '#0f172a', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Bar dataKey="utilization_rate" name="Utilization Rate" fill="#0284c7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Student Daily Burden Load */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Student Daily Examination Burden Distribution</h4>
            <span className="text-xs text-slate-500 font-mono font-medium">Cohorts Load Exposure</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {loadData.map((load: any, i: number) => (
              <div key={i} className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-500 uppercase">{load.burden_category}</span>
                  <div className="text-2xl font-bold text-slate-900 mt-1">{load.count} <span className="text-xs font-normal text-slate-500">instances</span></div>
                </div>
                <div className="text-xl font-mono font-bold text-indigo-600">
                  {load.percentage}%
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
