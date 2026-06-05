import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { predictionService } from '../services/api';
import { useToast } from '../hooks/useToast';
import { Loader2, Upload, FileSpreadsheet, AlertCircle, CheckCircle2, RefreshCw } from 'lucide-react';

const inputClass = "w-full px-3 py-2 bg-background border border-border rounded-md text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-colors";

interface SliderFieldProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  displayValue: string;
  onChange: (v: number) => void;
}

const SliderField: React.FC<SliderFieldProps> = ({ label, value, min, max, step, displayValue, onChange }) => (
  <div className="space-y-2">
    <div className="flex items-center justify-between">
      <label className="text-sm font-medium text-foreground">{label}</label>
      <span className="text-sm font-semibold text-blue-600">{displayValue}</span>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(step % 1 !== 0 ? parseFloat(e.target.value) : parseInt(e.target.value))}
      className="w-full h-1.5 bg-muted rounded-full appearance-none cursor-pointer accent-blue-600"
    />
    <div className="flex justify-between text-[11px] text-muted-foreground">
      <span>{min}</span>
      <span>{max}</span>
    </div>
  </div>
);

export const Predict: React.FC = () => {
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<'single' | 'bulk'>('single');

  // Single Predict States
  const [studentName, setStudentName] = useState('');
  const [attendance, setAttendance] = useState<number>(85);
  const [previousGpa, setPreviousGpa] = useState<number>(7.2);
  const [studyHours, setStudyHours] = useState<number>(18);
  const [assignmentCompletion, setAssignmentCompletion] = useState<number>(80);
  const [participationScore, setParticipationScore] = useState<number>(6.5);
  const [sleepHours, setSleepHours] = useState<number>(7.5);
  const [practiceTestScore, setPracticeTestScore] = useState<number>(70);
  const [practiceProblems, setPracticeProblems] = useState<number>(90);
  const [loading, setLoading] = useState(false);

  // Bulk Predict States
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [bulkProcessing, setBulkProcessing] = useState(false);
  const [bulkResult, setBulkResult] = useState<any | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentName.trim()) {
      showToast('Please enter a student name.', 'error');
      return;
    }
    setLoading(true);
    try {
      const result = await predictionService.predict({
        student_name: studentName,
        attendance,
        previous_gpa: previousGpa,
        study_hours: studyHours,
        assignment_completion: assignmentCompletion,
        participation_score: participationScore,
        sleep_hours: sleepHours,
        practice_test_score: practiceTestScore,
        practice_problems: practiceProblems,
      });
      navigate('/results', { state: { prediction: result } });
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Failed to complete prediction.';
      showToast(detail, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (!file.name.endsWith('.csv')) {
        showToast('Please upload a valid CSV file.', 'error');
        return;
      }
      setSelectedFile(file);
      setBulkResult(null);
    }
  };

  const handleBulkSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setBulkProcessing(true);
    try {
      const res = await predictionService.uploadBulkCsv(selectedFile);
      setBulkResult(res);
      showToast(`Batch processing completed. ${res.success_count} student records evaluated!`, 'success');
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Failed to process bulk evaluations.';
      showToast(detail, 'error');
    } finally {
      setBulkProcessing(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-foreground">Evaluate Performance</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Choose to evaluate an individual student or batch upload metrics via CSV.
          </p>
        </div>

        {/* Tab Buttons */}
        <div className="inline-flex rounded-lg border border-border p-1 bg-muted/30">
          <button
            onClick={() => setActiveTab('single')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-md transition-colors ${
              activeTab === 'single'
                ? 'bg-card text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Single Student
          </button>
          <button
            onClick={() => setActiveTab('bulk')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-md transition-colors ${
              activeTab === 'bulk'
                ? 'bg-card text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Bulk CSV Upload
          </button>
        </div>
      </div>

      {activeTab === 'single' ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Student Name */}
          <div className="card p-5">
            <div className="space-y-1">
              <label className="text-sm font-medium text-foreground" htmlFor="student-name">Student name</label>
              <input
                id="student-name"
                type="text"
                value={studentName}
                onChange={(e) => setStudentName(e.target.value)}
                placeholder="e.g. Rahul Sharma"
                className={inputClass}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Academics Card */}
            <div className="card p-5 space-y-5">
              <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">Academics</h3>
              <SliderField label="Previous GPA" value={previousGpa} min={0} max={10} step={0.1}
                displayValue={`${previousGpa.toFixed(1)} / 10`} onChange={setPreviousGpa} />
              <SliderField label="Practice Mock Test Score" value={practiceTestScore} min={0} max={100} step={1}
                displayValue={`${practiceTestScore}%`} onChange={setPracticeTestScore} />
              <SliderField label="Attendance Rate" value={attendance} min={0} max={100} step={1}
                displayValue={`${attendance}%`} onChange={setAttendance} />
            </div>

            {/* Habits Card */}
            <div className="card p-5 space-y-5">
              <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">Study Habits</h3>
              <SliderField label="Weekly Study Hours" value={studyHours} min={0} max={40} step={1}
                displayValue={`${studyHours} h/wk`} onChange={setStudyHours} />
              <SliderField label="Practice Problems Completed" value={practiceProblems} min={0} max={200} step={5}
                displayValue={`${practiceProblems} solved`} onChange={setPracticeProblems} />
              <SliderField label="Daily Sleep Hours" value={sleepHours} min={0} max={12} step={0.5}
                displayValue={`${sleepHours} h/day`} onChange={setSleepHours} />
              <SliderField label="Assignment Completion" value={assignmentCompletion} min={0} max={100} step={1}
                displayValue={`${assignmentCompletion}%`} onChange={setAssignmentCompletion} />
              <SliderField label="Class Participation" value={participationScore} min={0} max={10} step={0.5}
                displayValue={`${participationScore.toFixed(1)} / 10`} onChange={setParticipationScore} />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Running prediction...</>
              ) : (
                'Predict Student Grade'
              )}
            </button>
          </div>
        </form>
      ) : (
        <div className="space-y-4">
          <div className="card p-5 space-y-4">
            <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">Batch Evaluator</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Upload a `.csv` file containing headers mapping to study characteristics. The platform will automatically map column keys like:
              <br />
              <code className="text-blue-600 bg-muted/80 px-1 py-0.5 rounded text-[10px] inline-block mt-1 font-mono">
                student_name, previous_gpa, practice_test_score, attendance, study_hours, practice_problems, sleep_hours, assignment_completion, participation_score
              </code>
            </p>

            <form onSubmit={handleBulkSubmit} className="space-y-4">
              <div className="flex flex-col items-center justify-center border-2 border-dashed border-border hover:border-blue-500 rounded-lg p-8 transition-colors bg-muted/10 cursor-pointer relative">
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  disabled={bulkProcessing}
                />
                <Upload className="w-10 h-10 text-muted-foreground mb-3" />
                <span className="text-xs font-semibold text-foreground">
                  {selectedFile ? selectedFile.name : 'Choose CSV file to upload'}
                </span>
                <span className="text-[10px] text-muted-foreground mt-1">
                  Drag and drop files or browse local explorer
                </span>
              </div>

              <div className="flex items-center justify-between pt-2">
                <a
                  href="data:text/csv;charset=utf-8,student_name,previous_gpa,practice_test_score,attendance,study_hours,practice_problems,sleep_hours,assignment_completion,participation_score%0AJohn%20Smith,7.8,75,90,15,80,7.0,85,7.0%0AJane%20Doe,5.2,50,70,8,30,5.5,50,4.5"
                  download="student_template.csv"
                  className="text-xs text-blue-600 dark:text-blue-400 font-semibold hover:underline flex items-center gap-1"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5" /> Download Template CSV
                </a>

                <button
                  type="submit"
                  disabled={bulkProcessing || !selectedFile}
                  className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {bulkProcessing ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Batch processing...</>
                  ) : (
                    'Process CSV Evaluations'
                  )}
                </button>
              </div>
            </form>
          </div>

          {bulkResult && (
            <div className="card p-5 space-y-5 animate-in fade-in duration-300">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  <h3 className="text-sm font-semibold text-foreground">Evaluations Summary</h3>
                </div>
                <button
                  onClick={() => { setSelectedFile(null); setBulkResult(null); }}
                  className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
                >
                  <RefreshCw className="w-3 h-3" /> Clear Report
                </button>
              </div>

              {/* Status Summary Stats */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-muted/30 border border-border p-3 rounded-lg text-center">
                  <p className="text-xs text-muted-foreground font-semibold">Total Rows</p>
                  <p className="text-xl font-bold text-foreground mt-0.5">{bulkResult.total_processed}</p>
                </div>
                <div className="bg-emerald-500/5 border border-emerald-500/20 p-3 rounded-lg text-center">
                  <p className="text-xs text-emerald-700 dark:text-emerald-400 font-semibold">Success</p>
                  <p className="text-xl font-bold text-emerald-600 mt-0.5">{bulkResult.success_count}</p>
                </div>
                <div className="bg-red-500/5 border border-red-500/20 p-3 rounded-lg text-center">
                  <p className="text-xs text-red-700 dark:text-red-400 font-semibold">Errors</p>
                  <p className="text-xl font-bold text-red-600 mt-0.5">{bulkResult.error_count}</p>
                </div>
              </div>

              {/* Error Warnings List */}
              {bulkResult.errors && bulkResult.errors.length > 0 && (
                <div className="bg-red-50/10 border border-red-200 dark:border-red-950 p-4 rounded-lg space-y-2">
                  <div className="flex items-center gap-2 text-red-600 dark:text-red-400 text-xs font-semibold">
                    <AlertCircle className="w-4 h-4" /> Processing Warnings
                  </div>
                  <div className="max-h-24 overflow-y-auto space-y-1 pl-6">
                    {bulkResult.errors.map((err: string, i: number) => (
                      <p key={i} className="text-[11px] text-red-600 dark:text-red-400 leading-relaxed font-mono">
                        {err}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Processed Results Table */}
              <div className="space-y-2.5">
                <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Processed Records</h4>
                <div className="overflow-x-auto border border-border rounded-lg">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-muted/50 border-b border-border text-muted-foreground font-semibold">
                        <th className="py-2 px-3">Student Name</th>
                        <th className="py-2 px-3 text-center">Predicted Grade</th>
                        <th className="py-2 px-3">Performance Category</th>
                        <th className="py-2 px-3">Risk Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bulkResult.results && bulkResult.results.map((rec: any, idx: number) => (
                        <tr key={idx} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                          <td className="py-2 px-3 font-semibold text-foreground">{rec.name}</td>
                          <td className="py-2 px-3 text-center text-blue-600 font-bold">{rec.score.toFixed(1)}%</td>
                          <td className="py-2 px-3">{rec.level}</td>
                          <td className="py-2 px-3">
                            <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              rec.risk === 'High' ? 'bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-400' :
                              rec.risk === 'Medium' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400' :
                              'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400'
                            }`}>
                              {rec.risk} Risk
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex justify-end pt-1">
                <Link
                  to="/"
                  className="inline-flex items-center gap-1.5 px-4 py-2 border border-border text-xs font-semibold rounded-md shadow-sm hover:bg-muted text-foreground transition-colors"
                >
                  View Details in Dashboard
                </Link>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
export default Predict;
