import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { predictionService } from '../services/api';
import { useToast } from '../hooks/useToast';
import { Loader2 } from 'lucide-react';

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

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h2 className="text-base font-semibold text-foreground">Evaluate Student Performance</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Enter the student's academic details to generate a predicted grade.
        </p>
      </div>

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
    </div>
  );
};
export default Predict;
