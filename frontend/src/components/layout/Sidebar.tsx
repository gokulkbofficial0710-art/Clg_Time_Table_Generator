import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Calendar,
  BookOpen,
  Users,
  GraduationCap,
  Building2,
  Clock,
  AlertTriangle,
  Cpu,
  CheckCircle2,
  History
} from 'lucide-react';

interface NavSection {
  title: string;
  items: {
    to: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
  }[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: 'Schedule & Overview',
    items: [
      { to: '/', label: 'Dashboard', icon: LayoutDashboard },
      { to: '/calendar', label: 'Timetable Grid', icon: Calendar },
    ],
  },
  {
    title: 'Academic Registry',
    items: [
      { to: '/exams', label: 'Examinations', icon: BookOpen },
      { to: '/students', label: 'Students', icon: Users },
      { to: '/seatings', label: 'Student Seatings', icon: GraduationCap },
      { to: '/backlogs', label: 'Backlogs', icon: History },
      { to: '/rooms', label: 'Rooms & Venues', icon: Building2 },
      { to: '/timeslots', label: 'Time Slots', icon: Clock },
    ],
  },
  {
    title: 'Schedule Operations & Audit',
    items: [
      { to: '/conflicts', label: 'Conflict Resolution', icon: AlertTriangle },
      { to: '/optimizer', label: 'Schedule Optimizer', icon: Cpu },
    ],
  },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 border-r border-slate-200 bg-white flex flex-col shrink-0">
      <nav className="p-3 space-y-4 flex-1 overflow-y-auto">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title} className="space-y-1">
            <div className="px-3 py-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              {section.title}
            </div>
            {section.items.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-slate-100 text-slate-900 font-semibold border-l-3 border-indigo-600 rounded-l-none'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0 text-slate-500" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="p-3.5 border-t border-slate-200 bg-slate-50/70 text-xs text-slate-600">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-slate-700">Registrar Portal</span>
          <span className="inline-flex items-center gap-1 text-[11px] text-emerald-700 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            Operational
          </span>
        </div>
        <p className="mt-1 text-[11px] text-slate-500 leading-tight">
          Academic Term: Fall 2026
        </p>
      </div>
    </aside>
  );
};
