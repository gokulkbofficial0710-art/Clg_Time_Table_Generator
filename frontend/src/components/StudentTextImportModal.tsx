import React, { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { ParsedStudentItem, StudentTextPreviewResponse, StudentTextCommitResponse } from '../types';
import {
  FileText, Upload, CheckCircle2, AlertTriangle, X,
  Download, Copy, Check, Users, ArrowRight, RefreshCw, Sparkles, Building2
} from 'lucide-react';

interface StudentTextImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (response: StudentTextCommitResponse) => void;
}

const SAMPLE_DELIMITED = `# Student Cohort Registry - Comma Delimited (.txt)
# Format: student_id, name, department, semester, courses, accommodations
STU-2026-1101, Alex Williams, Computer Science, Semester 5, CS101, Extra Time
STU-2026-1102, Brittany Brown, Business, Semester 5, BUS101, None
STU-2026-1103, Charlie Clark, Mathematics, Semester 5, MA101, None
STU-2026-1104, Daniel Davis, Electrical Eng, Semester 5, CS101, Wheelchair Access
STU-2026-1105, Evelyn Evans, Physics, Semester 5, MA101, None`;

const SAMPLE_PIPE = `# Student Cohort Registry - Pipe Delimited (.txt)
STU-2026-1201 | Fiona Fisher | Computer Science | Semester 5 | CS101,CS201 | Extra Time
STU-2026-1202 | George Garcia | Business | Semester 5 | BUS101 | None
STU-2026-1203 | Hannah Harris | Mathematics | Semester 5 | MA101,MA310 | None
STU-2026-1204 | Ian Isaac | Electrical Eng | Semester 5 | CS499 | None`;

const SAMPLE_BLOCK = `# Student Cohort Registry - Key-Value Block (.txt)
Student ID: STU-2026-1301
Name: Julia Jones
Department: Computer Science
Semester: Semester 5
Courses: CS101, CS201
Accommodations: Extra Time
---
Student ID: STU-2026-1302
Name: Kevin King
Department: Business
Semester: Semester 5
Courses: BUS101
Accommodations: None`;

export const StudentTextImportModal: React.FC<StudentTextImportModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [inputMode, setInputMode] = useState<'upload' | 'paste'>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [rawText, setRawText] = useState<string>('');
  const [overwriteExisting, setOverwriteExisting] = useState<boolean>(true);
  const [autoEnrollCourses, setAutoEnrollCourses] = useState<boolean>(true);

  const [previewData, setPreviewData] = useState<StudentTextPreviewResponse | null>(null);
  const [commitResult, setCommitResult] = useState<StudentTextCommitResponse | null>(null);
  const [copiedTemplate, setCopiedTemplate] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Preview mutation
  const previewMutation = useMutation({
    mutationFn: async () => {
      setErrorMessage(null);
      if (inputMode === 'upload') {
        if (!selectedFile) throw new Error('Please select a .txt file to upload.');
        return api.previewStudentText({ file: selectedFile });
      } else {
        if (!rawText.trim()) throw new Error('Please enter student text records to preview.');
        return api.previewStudentText({ raw_text: rawText });
      }
    },
    onSuccess: (data) => {
      setPreviewData(data);
      setCommitResult(null);
    },
    onError: (err: any) => {
      setErrorMessage(err.message || 'Failed to parse student text file.');
    },
  });

  // Commit mutation
  const commitMutation = useMutation({
    mutationFn: async () => {
      if (!previewData || previewData.students.length === 0) {
        throw new Error('No student records available to import.');
      }
      return api.commitStudentText({
        students: previewData.students.filter((s) => s.status === 'VALID'),
        overwrite_existing: overwriteExisting,
        auto_enroll_courses: autoEnrollCourses,
      });
    },
    onSuccess: (data) => {
      setCommitResult(data);
      // Invalidate queries so dashboard, students list, and seatings refresh immediately
      queryClient.invalidateQueries({ queryKey: ['students'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['student-seatings'] });
      queryClient.invalidateQueries({ queryKey: ['department-seatings-summary'] });
      queryClient.invalidateQueries({ queryKey: ['hall-seating-charts'] });
      if (onSuccess) {
        onSuccess(data);
      }
    },
    onError: (err: any) => {
      setErrorMessage(err.message || 'Failed to commit student records.');
    },
  });

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewData(null);
      setCommitResult(null);
      setErrorMessage(null);
    }
  };

  const handleCopySample = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedTemplate(label);
    setTimeout(() => setCopiedTemplate(null), 2000);
  };

  const handleDownloadTemplate = (format: string) => {
    window.open(api.getStudentTextTemplateUrl(format), '_blank');
  };

  const resetAll = () => {
    setSelectedFile(null);
    setRawText('');
    setPreviewData(null);
    setCommitResult(null);
    setErrorMessage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full border border-slate-200 overflow-hidden flex flex-col max-h-[92vh] animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/80">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-100 text-indigo-700">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                Attach Student Text File (.txt / .csv)
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                  Student Registry
                </span>
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Import student cohort attributes, department affiliations, enrolled courses, and exam accommodations
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/50 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
          {/* Error Banner */}
          {errorMessage && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{errorMessage}</span>
              </div>
              <button
                onClick={() => setErrorMessage(null)}
                className="text-rose-500 hover:text-rose-700 p-1"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Success Banner */}
          {commitResult && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-950 space-y-2">
              <div className="flex items-center gap-2 font-bold text-sm text-emerald-900">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <span>Import Succeeded!</span>
              </div>
              <p className="text-emerald-800">{commitResult.message}</p>
              <div className="flex flex-wrap gap-2 pt-1">
                {Object.entries(commitResult.departments).map(([dept, count]) => (
                  <span
                    key={dept}
                    className="px-2.5 py-1 rounded-md bg-white border border-emerald-300 font-semibold text-[11px] text-emerald-800"
                  >
                    {dept}: {count}
                  </span>
                ))}
              </div>
            </div>
          )}

          {!commitResult && (
            <>
              {/* Input Tabs */}
              <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => { setInputMode('upload'); setErrorMessage(null); }}
                    className={`px-3 py-1.5 rounded-lg font-semibold transition cursor-pointer ${
                      inputMode === 'upload'
                        ? 'bg-indigo-600 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    Attach .TXT File
                  </button>
                  <button
                    onClick={() => { setInputMode('paste'); setErrorMessage(null); }}
                    className={`px-3 py-1.5 rounded-lg font-semibold transition cursor-pointer ${
                      inputMode === 'paste'
                        ? 'bg-indigo-600 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    Paste Text Content
                  </button>
                </div>

                {/* Templates Quick Actions */}
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-slate-400 font-medium hidden sm:inline">Templates:</span>
                  <button
                    onClick={() => handleDownloadTemplate('delimited')}
                    className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-medium transition cursor-pointer"
                    title="Download Comma-Delimited Template"
                  >
                    <Download className="w-3 h-3" />
                    CSV/TXT
                  </button>
                  <button
                    onClick={() => handleDownloadTemplate('block')}
                    className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-medium transition cursor-pointer"
                    title="Download Block Template"
                  >
                    <Download className="w-3 h-3" />
                    Key-Value
                  </button>
                </div>
              </div>

              {/* Mode 1: File Upload */}
              {inputMode === 'upload' && (
                <div className="space-y-3">
                  {/* Download Sample Files Quick Banner */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-indigo-50/70 border border-indigo-200/80 px-3.5 py-2.5 rounded-xl text-xs text-indigo-900">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-indigo-600 shrink-0" />
                      <span className="font-medium">Need sample test files? Download & attach directly:</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-1.5">
                      <a
                        href="/sample_students.txt"
                        download="sample_students.txt"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-[11px] transition shadow-xs"
                      >
                        <Download className="w-3 h-3" />
                        sample_students.txt
                      </a>
                      <a
                        href="/sample_students_pipe.txt"
                        download="sample_students_pipe.txt"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-indigo-300 hover:bg-indigo-100 text-indigo-800 font-semibold text-[11px] transition"
                      >
                        <Download className="w-3 h-3" />
                        Pipe .txt
                      </a>
                      <a
                        href="/sample_students_blocks.txt"
                        download="sample_students_blocks.txt"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-indigo-300 hover:bg-indigo-100 text-indigo-800 font-semibold text-[11px] transition"
                      >
                        <Download className="w-3 h-3" />
                        Block .txt
                      </a>
                    </div>
                  </div>

                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition flex flex-col items-center justify-center gap-3 ${
                      selectedFile
                        ? 'border-indigo-400 bg-indigo-50/40 text-indigo-950'
                        : 'border-slate-300 hover:border-indigo-400 bg-slate-50/50 hover:bg-indigo-50/20 text-slate-600'
                    }`}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".txt,.csv,.tsv"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                    <div className="p-3 rounded-xl bg-white shadow-xs border border-slate-200 text-indigo-600">
                      <Upload className="w-6 h-6" />
                    </div>
                    {selectedFile ? (
                      <div>
                        <div className="font-bold text-sm text-slate-900">{selectedFile.name}</div>
                        <div className="text-[11px] text-slate-500 mt-0.5">
                          {(selectedFile.size / 1024).toFixed(1)} KB — Ready to parse
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div className="font-semibold text-sm text-slate-800">
                          Click to browse or drop your student <code className="bg-slate-200 px-1.5 py-0.5 rounded text-indigo-700">.txt</code> or <code className="bg-slate-200 px-1.5 py-0.5 rounded text-indigo-700">.csv</code> file
                        </div>
                        <div className="text-[11px] text-slate-400 mt-1">
                          Supports comma, pipe (|), tab, or key-value format
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Mode 2: Paste Raw Text */}
              {inputMode === 'paste' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="font-semibold text-slate-700">
                      Enter or Paste Student Records:
                    </label>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] text-slate-400">Insert Sample:</span>
                      <button
                        onClick={() => setRawText(SAMPLE_DELIMITED)}
                        className="px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 text-[10px] font-mono cursor-pointer"
                      >
                        Comma
                      </button>
                      <button
                        onClick={() => setRawText(SAMPLE_PIPE)}
                        className="px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 text-[10px] font-mono cursor-pointer"
                      >
                        Pipe
                      </button>
                      <button
                        onClick={() => setRawText(SAMPLE_BLOCK)}
                        className="px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 text-[10px] font-mono cursor-pointer"
                      >
                        Key-Value
                      </button>
                    </div>
                  </div>

                  <textarea
                    rows={7}
                    value={rawText}
                    onChange={(e) => {
                      setRawText(e.target.value);
                      setPreviewData(null);
                    }}
                    placeholder={`STU-1001, John Doe, Computer Science, Semester 5, CS101, None\nSTU-1002, Jane Smith, Mathematics, Semester 5, MA101, Extra Time`}
                    className="w-full p-3 font-mono text-[11px] border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-slate-50/50 text-slate-900"
                  />
                </div>
              )}

              {/* Options */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={overwriteExisting}
                    onChange={(e) => setOverwriteExisting(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                  />
                  <div>
                    <span className="font-semibold text-slate-800">Update Existing Students</span>
                    <p className="text-[10px] text-slate-500">Overwrite details if Student ID already exists</p>
                  </div>
                </label>

                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={autoEnrollCourses}
                    onChange={(e) => setAutoEnrollCourses(e.target.checked)}
                    className="rounded text-indigo-600 focus:ring-indigo-500 w-4 h-4"
                  />
                  <div>
                    <span className="font-semibold text-slate-800">Auto-Enroll Departmental Exams</span>
                    <p className="text-[10px] text-slate-500">Assign departmental exams if courses column is empty</p>
                  </div>
                </label>
              </div>

              {/* Parse & Preview Button */}
              <div className="flex items-center justify-between pt-1">
                <button
                  onClick={() => previewMutation.mutate()}
                  disabled={previewMutation.isPending || (inputMode === 'upload' && !selectedFile) || (inputMode === 'paste' && !rawText.trim())}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition disabled:opacity-50 cursor-pointer"
                >
                  <Sparkles className={`w-3.5 h-3.5 ${previewMutation.isPending ? 'animate-spin' : ''}`} />
                  {previewMutation.isPending ? 'Parsing Text File...' : 'Parse & Preview Student Data'}
                </button>

                {(selectedFile || rawText) && (
                  <button
                    onClick={resetAll}
                    className="text-xs text-slate-400 hover:text-slate-600 font-medium cursor-pointer"
                  >
                    Reset Input
                  </button>
                )}
              </div>

              {/* Preview Table & Breakdown */}
              {previewData && (
                <div className="space-y-4 pt-3 border-t border-slate-200">
                  {/* Summary Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                    <div className="flex items-center gap-3">
                      <div className="text-xs text-slate-600">
                        Total Found: <strong className="text-slate-900 font-bold">{previewData.total_found}</strong>
                      </div>
                      <div className="text-xs text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
                        {previewData.valid_count} Valid
                      </div>
                      {previewData.invalid_count > 0 && (
                        <div className="text-xs text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200 font-semibold">
                          {previewData.invalid_count} Errors
                        </div>
                      )}
                    </div>

                    {/* Department Badges */}
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-[11px] text-slate-400 font-medium">Departments:</span>
                      {Object.entries(previewData.departments_detected).map(([dept, count]) => (
                        <span
                          key={dept}
                          className="px-2 py-0.5 rounded-md bg-white border border-slate-300 text-slate-700 font-medium text-[11px] shadow-2xs"
                        >
                          {dept} <strong className="text-indigo-600 font-bold">({count})</strong>
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Student Table */}
                  <div className="border border-slate-200 rounded-xl overflow-hidden max-h-60 overflow-y-auto">
                    <table className="w-full text-left text-[11px]">
                      <thead className="bg-slate-100 text-slate-700 font-bold sticky top-0 border-b border-slate-200">
                        <tr>
                          <th className="py-2 px-3">#</th>
                          <th className="py-2 px-3">Status</th>
                          <th className="py-2 px-3">Student ID</th>
                          <th className="py-2 px-3">Full Name</th>
                          <th className="py-2 px-3">Department</th>
                          <th className="py-2 px-3">Semester</th>
                          <th className="py-2 px-3">Courses</th>
                          <th className="py-2 px-3">Accommodations</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                        {previewData.students.map((st, i) => (
                          <tr key={i} className={st.status === 'INVALID' ? 'bg-rose-50/50' : 'hover:bg-slate-50'}>
                            <td className="py-2 px-3 text-slate-400">{st.row_number}</td>
                            <td className="py-2 px-3">
                              {st.status === 'VALID' ? (
                                <span className="inline-flex items-center gap-1 text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200 font-semibold">
                                  <CheckCircle2 className="w-2.5 h-2.5" /> OK
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 text-[10px] text-rose-700 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200 font-semibold" title={st.errors.join(', ')}>
                                  <AlertTriangle className="w-2.5 h-2.5" /> Error
                                </span>
                              )}
                            </td>
                            <td className="py-2 px-3 font-mono font-semibold text-slate-900">{st.student_id || '—'}</td>
                            <td className="py-2 px-3">{st.name || '—'}</td>
                            <td className="py-2 px-3">
                              <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-semibold">
                                {st.department}
                              </span>
                            </td>
                            <td className="py-2 px-3 text-slate-500">{st.semester}</td>
                            <td className="py-2 px-3">
                              {st.enrolled_courses.length > 0 ? (
                                <span className="font-mono text-slate-800">{st.enrolled_courses.join(', ')}</span>
                              ) : (
                                <span className="text-slate-400 italic">Auto-assign</span>
                              )}
                            </td>
                            <td className="py-2 px-3 text-slate-500">
                              {st.special_accommodations.length > 0 ? st.special_accommodations.join(', ') : '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Commit Button */}
                  <div className="flex items-center justify-between pt-2">
                    <div className="text-xs text-slate-500">
                      Ready to import <strong className="text-slate-900 font-bold">{previewData.valid_count}</strong> students across {Object.keys(previewData.departments_detected).length} departments into the academic registry.
                    </div>
                    <button
                      onClick={() => commitMutation.mutate()}
                      disabled={commitMutation.isPending || previewData.valid_count === 0}
                      className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition disabled:opacity-50 cursor-pointer"
                    >
                      <CheckCircle2 className={`w-4 h-4 ${commitMutation.isPending ? 'animate-spin' : ''}`} />
                      {commitMutation.isPending ? 'Importing Records...' : `Commit & Import ${previewData.valid_count} Students`}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs">
          <div className="text-slate-500">
            {commitResult ? 'Students updated in database registry.' : 'Attached files are securely parsed on the local server.'}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg font-semibold bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 transition cursor-pointer"
          >
            {commitResult ? 'Close & Refresh View' : 'Cancel'}
          </button>
        </div>
      </div>
    </div>
  );
};
