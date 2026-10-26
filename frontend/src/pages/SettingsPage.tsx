import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { TimetableVersion } from '../types';
import {
  Database, Upload, Download, RefreshCw, History,
  FileSpreadsheet, FileText, CheckCircle2, AlertOctagon,
  RotateCcw, ShieldAlert, Award, FlaskConical,
  Users, Key, Plus, Trash2, UserCheck, Lock
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const queryClient = useQueryClient();

  const [importEntity, setImportEntity] = useState<string>('exams');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<any>(null);

  // User Management State
  const [isAddUserOpen, setIsAddUserOpen] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newRole, setNewRole] = useState('editor');
  const [userError, setUserError] = useState<string | null>(null);
  const [userSuccess, setUserSuccess] = useState<string | null>(null);

  const [passwordChangeUser, setPasswordChangeUser] = useState<string | null>(null);
  const [changePasswordInput, setChangePasswordInput] = useState('');


  const { data: versions = [], isLoading: loadingVersions } = useQuery({
    queryKey: ['versions'],
    queryFn: api.getVersions,
  });

  const demoMutation = useMutation({
    mutationFn: (includeInfeasible?: boolean) => api.loadDemoData(includeInfeasible),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  const infeasibleMutation = useMutation({
    mutationFn: () => api.loadInfeasibleScenario(),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  const restoreMutation = useMutation({
    mutationFn: (versionId: number) => api.restoreVersion(versionId),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  const previewMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile) return;
      return api.previewImport(importEntity, selectedFile);
    },
    onSuccess: (data) => setPreviewData(data),
  });

  const commitMutation = useMutation({
    mutationFn: async () => {
      if (!previewData) return;
      const validItems = previewData.preview_items
        .filter((it: any) => it.status === 'VALID')
        .map((it: any) => it.data);
      return api.commitImport(importEntity, validItems, false);
    },
    onSuccess: () => {
      setPreviewData(null);
      setSelectedFile(null);
      queryClient.invalidateQueries();
    },
  });

  const { data: users = [], isLoading: loadingUsers } = useQuery({
    queryKey: ['users'],
    queryFn: api.getUsers,
  });

  const createUserMutation = useMutation({
    mutationFn: (data: any) => api.createUser(data),
    onSuccess: () => {
      setUserSuccess('User account successfully created.');
      setUserError(null);
      setIsAddUserOpen(false);
      setNewUsername('');
      setNewEmail('');
      setNewPassword('');
      setNewFullName('');
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (err: any) => {
      setUserError(err.message || 'Failed to create user');
    },
  });

  const changePasswordMutation = useMutation({
    mutationFn: (data: { username: string; new_password: string }) => api.changePassword(data),
    onSuccess: (data: any) => {
      setUserSuccess(data.message || 'Password successfully updated.');
      setUserError(null);
      setPasswordChangeUser(null);
      setChangePasswordInput('');
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (err: any) => {
      setUserError(err.message || 'Failed to update password');
    },
  });

  const deleteUserMutation = useMutation({
    mutationFn: (id: number) => api.deleteUser(id),
    onSuccess: () => {
      setUserSuccess('User account deleted.');
      setUserError(null);
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (err: any) => {
      setUserError(err.message || 'Failed to delete user');
    },
  });


  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white border border-slate-200 p-5 rounded-xl shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Database className="w-5 h-5 text-indigo-600" />
            Data Management, Ingestion & Version History
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            CSV batch ingestion, schedule snapshots, ReportLab PDF generation, and benchmark datasets
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              if (window.confirm("Are you sure want to reset all the data?\nReset timetable schedule to unallocated baseline state?")) {
                demoMutation.mutate(false);
              }
            }}
            disabled={demoMutation.isPending}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg text-xs font-semibold shadow-xs transition cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${demoMutation.isPending ? 'animate-spin' : ''}`} />
            Reset to Draft Baseline
          </button>
          <button
            onClick={() => {
              if (window.confirm("This will inject a test clash to audit conflict detection rules. Continue?")) {
                infeasibleMutation.mutate();
              }
            }}
            disabled={infeasibleMutation.isPending}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold shadow-xs transition cursor-pointer"
          >
            <FlaskConical className="w-3.5 h-3.5 text-slate-500" />
            Test Conflict Scenario
          </button>
        </div>
      </div>

      {/* Section 1: Timetable Version History & Restore */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-600" />
              Timetable Version History
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Roll back to previous schedule generations with preserved assignments and metric records
            </p>
          </div>
          <span className="text-xs text-slate-500 font-mono font-medium">{versions.length} Versions</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Ver</th>
                <th className="py-3 px-4">Schedule Title</th>
                <th className="py-3 px-4">Solver Status</th>
                <th className="py-3 px-4">Quality Score</th>
                <th className="py-3 px-4">Solve Time</th>
                <th className="py-3 px-4">Created Date</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {versions.map((ver) => (
                <tr key={ver.id} className="hover:bg-slate-50/70 transition">
                  <td className="py-3 px-4 font-mono font-bold text-slate-900">v{ver.version_number}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-900">{ver.name}</span>
                      {ver.is_active && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          ACTIVE
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-slate-700">{ver.solver_status}</td>
                  <td className="py-3 px-4 font-mono font-bold text-slate-900">
                    {ver.quality_score === 0 ? '0% (Pre-Opt)' : `${ver.quality_score.toFixed(1)}%`}
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-500">{ver.solver_runtime_ms} ms</td>
                  <td className="py-3 px-4 text-slate-500 font-mono text-[11px]">{new Date(ver.created_at).toLocaleString()}</td>
                  <td className="py-3 px-4 text-right">
                    {!ver.is_active && (
                      <button
                        onClick={() => restoreMutation.mutate(ver.id)}
                        disabled={restoreMutation.isPending}
                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-semibold text-xs shadow-xs transition cursor-pointer"
                      >
                        <RotateCcw className="w-3 h-3 text-slate-500" />
                        Restore
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 2: CSV Import Wizard */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <Upload className="w-4 h-4 text-indigo-600" />
              CSV Data Ingestion Wizard
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Batch import courses, examination records, student cohorts, enrollments, venues, and time slots
            </p>
          </div>

          <a
            href={`/api/import/template/${importEntity}`}
            download
            className="flex items-center gap-1.5 text-xs text-indigo-700 hover:text-indigo-900 font-semibold"
          >
            <Download className="w-3.5 h-3.5" />
            Download {importEntity} CSV Template
          </a>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Target Entity Type</label>
            <select
              value={importEntity}
              onChange={(e) => { setImportEntity(e.target.value); setPreviewData(null); }}
              className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-xs text-slate-900 focus:outline-none focus:border-indigo-600"
            >
              <option value="exams">Course Examinations</option>
              <option value="students">Student Records</option>
              <option value="rooms">Rooms & Venues</option>
              <option value="timeslots">Time Slots</option>
              <option value="enrollments">Student Enrollments</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-slate-700 mb-1">Upload CSV File</label>
            <div className="flex gap-2">
              <input
                type="file"
                accept=".csv"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setSelectedFile(e.target.files[0]);
                  }
                }}
                className="flex-1 bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-700 file:mr-3 file:py-1 file:px-2.5 file:rounded-md file:border file:border-slate-300 file:text-xs file:bg-slate-50 file:text-slate-700 file:font-semibold"
              />
              <button
                type="button"
                onClick={() => previewMutation.mutate()}
                disabled={!selectedFile || previewMutation.isPending}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shrink-0 shadow-xs cursor-pointer"
              >
                {previewMutation.isPending ? 'Validating...' : 'Validate & Preview'}
              </button>
            </div>
          </div>
        </div>

        {/* Import Preview Results */}
        {previewData && (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-xs text-slate-700">
                Found <strong>{previewData.total_rows}</strong> rows: <span className="text-emerald-700 font-bold">{previewData.valid_rows} Valid</span>, <span className="text-rose-700 font-bold">{previewData.invalid_rows} Invalid</span>
              </div>
              <button
                onClick={() => commitMutation.mutate()}
                disabled={!previewData.can_commit || commitMutation.isPending}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-md text-xs font-semibold shadow-xs cursor-pointer"
              >
                {commitMutation.isPending ? 'Committing...' : 'Commit Ingestion'}
              </button>
            </div>

            <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1 text-xs">
              {previewData.preview_items.map((row: any) => (
                <div key={row.row_number} className="p-2 rounded bg-white border border-slate-200 flex items-center justify-between">
                  <span className="font-mono text-slate-500">Row {row.row_number}</span>
                  <span className="font-mono text-slate-800 truncate max-w-sm">{JSON.stringify(row.data)}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${row.status === 'VALID' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}`}>
                    {row.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Section 3: Official Export Center */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
        <div className="border-b border-slate-100 pb-3">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
            <Download className="w-4 h-4 text-emerald-600" />
            Official Timetable Exports
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Generate printable, auditable administrative schedules and spreadsheets
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a
            href="/api/export/timetable/pdf"
            target="_blank"
            rel="noopener noreferrer"
            className="p-4 rounded-xl bg-slate-50 hover:bg-slate-100/80 border border-slate-200 flex items-center justify-between group transition"
          >
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-rose-500" />
              <div>
                <h4 className="font-bold text-slate-900 text-sm group-hover:text-indigo-700 transition">Complete Master Timetable PDF</h4>
                <p className="text-xs text-slate-500">ReportLab landscape format with quality headers and signatures</p>
              </div>
            </div>
            <Download className="w-4 h-4 text-slate-400 group-hover:text-slate-700" />
          </a>

          <a
            href="/api/export/timetable/csv"
            download
            className="p-4 rounded-xl bg-slate-50 hover:bg-slate-100/80 border border-slate-200 flex items-center justify-between group transition"
          >
            <div className="flex items-center gap-3">
              <FileSpreadsheet className="w-8 h-8 text-emerald-600" />
              <div>
                <h4 className="font-bold text-slate-900 text-sm group-hover:text-indigo-700 transition">Complete Timetable CSV Spreadsheet</h4>
                <p className="text-xs text-slate-500">Raw tabular export with all room, slot, and course IDs</p>
              </div>
            </div>
            <Download className="w-4 h-4 text-slate-400 group-hover:text-slate-700" />
          </a>
        </div>
      </div>

      {/* Section 4: User Accounts & Credentials Management */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-3 gap-3">
          <div>
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <Users className="w-4 h-4 text-indigo-600" />
              User Accounts & Credentials Management
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Manage system usernames, access roles, and update passwords for administrators, faculty, and viewers
            </p>
          </div>

          <button
            onClick={() => {
              setIsAddUserOpen(true);
              setUserError(null);
              setUserSuccess(null);
            }}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            Add New User Account
          </button>
        </div>

        {userSuccess && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center justify-between">
            <span>{userSuccess}</span>
            <button onClick={() => setUserSuccess(null)} className="text-emerald-600 hover:text-emerald-900 font-bold ml-2">×</button>
          </div>
        )}

        {userError && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-center justify-between">
            <span>{userError}</span>
            <button onClick={() => setUserError(null)} className="text-rose-600 hover:text-rose-900 font-bold ml-2">×</button>
          </div>
        )}

        {/* Add User Modal / Form */}
        {isAddUserOpen && (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <UserCheck className="w-4 h-4 text-indigo-600" />
              Create New Account
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">Username *</label>
                <input
                  type="text"
                  placeholder="e.g. jdoe"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-600"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  placeholder="e.g. John Doe"
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-600"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">Email *</label>
                <input
                  type="email"
                  placeholder="e.g. jdoe@university.edu"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-600"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">Password *</label>
                <input
                  type="password"
                  placeholder="Min 6 characters"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-600"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">Role</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-600"
                >
                  <option value="admin">Admin (Full Control)</option>
                  <option value="editor">Editor (Faculty)</option>
                  <option value="viewer">Viewer (Student)</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsAddUserOpen(false)}
                className="px-3.5 py-1.5 bg-white hover:bg-slate-100 text-slate-700 border border-slate-300 rounded-lg text-xs font-semibold cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!newUsername || !newEmail || !newPassword || createUserMutation.isPending}
                onClick={() => {
                  createUserMutation.mutate({
                    username: newUsername,
                    email: newEmail,
                    password: newPassword,
                    full_name: newFullName || newUsername,
                    role: newRole,
                  });
                }}
                className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs cursor-pointer"
              >
                {createUserMutation.isPending ? 'Saving...' : 'Save User Account'}
              </button>
            </div>
          </div>
        )}

        {/* Password Change Popover */}
        {passwordChangeUser && (
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-2">
            <h4 className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
              <Key className="w-4 h-4 text-amber-600" />
              Change Password for Account: <span className="font-mono underline">{passwordChangeUser}</span>
            </h4>
            <div className="flex flex-col sm:flex-row gap-2 max-w-md">
              <input
                type="password"
                placeholder="Enter new password"
                value={changePasswordInput}
                onChange={(e) => setChangePasswordInput(e.target.value)}
                className="flex-1 bg-white border border-amber-300 rounded-lg p-2 text-xs text-slate-900 focus:outline-none focus:border-amber-600"
              />
              <button
                type="button"
                disabled={!changePasswordInput || changePasswordMutation.isPending}
                onClick={() => {
                  changePasswordMutation.mutate({
                    username: passwordChangeUser,
                    new_password: changePasswordInput,
                  });
                }}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs cursor-pointer"
              >
                {changePasswordMutation.isPending ? 'Updating...' : 'Update Password'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setPasswordChangeUser(null);
                  setChangePasswordInput('');
                }}
                className="px-3 py-2 bg-white hover:bg-amber-100 text-slate-700 border border-amber-300 rounded-lg text-xs font-semibold cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Users Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-4">User ID</th>
                <th className="py-3 px-4">Username</th>
                <th className="py-3 px-4">Full Name</th>
                <th className="py-3 px-4">Email</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {loadingUsers ? (
                <tr>
                  <td colSpan={7} className="py-4 text-center text-slate-400">Loading user accounts...</td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-4 text-center text-slate-400">No user accounts found.</td>
                </tr>
              ) : (
                users.map((u: any) => (
                  <tr key={u.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3 px-4 font-mono font-bold text-slate-900">#{u.id}</td>
                    <td className="py-3 px-4 font-mono font-bold text-indigo-700">{u.username}</td>
                    <td className="py-3 px-4 text-slate-900">{u.full_name || '—'}</td>
                    <td className="py-3 px-4 font-mono text-slate-600">{u.email}</td>
                    <td className="py-3 px-4">
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold uppercase ${
                        u.role === 'admin'
                          ? 'bg-purple-50 text-purple-700 border border-purple-200'
                          : u.role === 'editor'
                          ? 'bg-blue-50 text-blue-700 border border-blue-200'
                          : 'bg-slate-100 text-slate-700 border border-slate-200'
                      }`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        ACTIVE
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right space-x-1.5">
                      <button
                        onClick={() => {
                          setPasswordChangeUser(u.username);
                          setChangePasswordInput('');
                          setUserError(null);
                          setUserSuccess(null);
                        }}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-semibold text-[11px] shadow-xs transition cursor-pointer"
                      >
                        <Key className="w-3 h-3 text-slate-500" />
                        Change Password
                      </button>

                      {u.username !== 'admin' && (
                        <button
                          onClick={() => {
                            if (window.confirm(`Delete user account "${u.username}"?`)) {
                              deleteUserMutation.mutate(u.id);
                            }
                          }}
                          disabled={deleteUserMutation.isPending}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-semibold text-[11px] transition cursor-pointer"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

