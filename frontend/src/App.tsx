import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { CalendarPage } from './pages/CalendarPage';
import { ExamsPage } from './pages/ExamsPage';
import { StudentsPage } from './pages/StudentsPage';
import { StudentSeatingsPage } from './pages/StudentSeatingsPage';
import { BacklogsPage } from './pages/BacklogsPage';
import { RoomsPage } from './pages/RoomsPage';
import { TimeSlotsPage } from './pages/TimeSlotsPage';
import { ConflictsPage } from './pages/ConflictsPage';
import { OptimizerPage } from './pages/OptimizerPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="calendar" element={<CalendarPage />} />
            <Route path="exams" element={<ExamsPage />} />
            <Route path="students" element={<StudentsPage />} />
            <Route path="seatings" element={<StudentSeatingsPage />} />
            <Route path="backlogs" element={<BacklogsPage />} />
            <Route path="rooms" element={<RoomsPage />} />
            <Route path="timeslots" element={<TimeSlotsPage />} />
            <Route path="conflicts" element={<ConflictsPage />} />
            <Route path="optimizer" element={<OptimizerPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
