import React from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { predictionService } from '../services/api';
import { PredictionRecord } from '../types';
import { useToast } from '../hooks/useToast';
import {
  ArrowLeft,
  FileDown,
  CheckCircle,
  XCircle,
  Lightbulb,
  AlertTriangle,
} from 'lucide-react';

export const Results: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const prediction = location.state?.prediction as PredictionRecord;

  const handleDownloadPdf = async () => {
    if (!prediction) return;
    try {
      showToast('Generating PDF report...', 'info');
      await predictionService.downloadPdf(prediction.id, prediction.student_name);
      showToast('PDF downloaded!', 'success');
    } catch {
      showToast('Failed to download PDF.', 'error');
    }
  };

  if (!prediction) {
    return (
      <div className="max-w-md mx-auto text-center py-16 space-y-4">
        <div className="w-12 h-12 rounded-full bg-red-50 text-red-500 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h2 className="text-base font-semibold text-foreground">No result found</h2>
        <p className="text-sm text-muted-foreground">Please evaluate a student first.</p>
        <Link to="/predict" className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm rounded-md transition-colors">
          Go to prediction form
        </Link>
      </div>
    );
  }

  const levelBadge = (
    {
      Excellent: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
      Good: 'bg-blue-50 text-blue-700 border border-blue-200',
      Average: 'bg-amber-50 text-amber-700 border border-amber-200',
      'At Risk': 'bg-red-50 text-red-700 border border-red-200',
    } as Record<string, string>
  )[prediction.performance_level] ?? 'bg-gray-100 text-gray-700 border border-gray-200';

  const riskColor = (
    {
      High: 'text-red-600',
      Medium: 'text-amber-600',
      Low: 'text-emerald-600',
    } as Record<string, string>
  )[prediction.risk_level] ?? 'text-gray-600';

  const riskBarColor = (
    {
      High: 'bg-red-500',
      Medium: 'bg-amber-500',
      Low: 'bg-emerald-500',
    } as Record<string, string>
  )[prediction.risk_level] ?? 'bg-gray-400';

  const riskBarWidth = (
    { High: '100%', Medium: '60%', Low: '20%' } as Record<string, string>
  )[prediction.risk_level] ?? '50%';

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      {/* Nav */}
      <div className="flex items-center justify-between pb-2">
        <button
          onClick={() => navigate('/predict')}
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to form
        </button>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDownloadPdf}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-border bg-card hover:bg-muted text-foreground text-sm rounded-md transition-colors"
          >
            <FileDown className="w-4 h-4" />
            Download PDF
          </button>
          <Link to="/" className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md transition-colors">
            Dashboard
          </Link>
        </div>
      </div>

      {/* Score summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Score */}
        <div className="card p-5 flex flex-col items-center justify-center text-center space-y-3">
          <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium">Predicted Score</span>
          <div className="text-4xl font-bold text-foreground">{prediction.predicted_score.toFixed(1)}%</div>
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-md ${levelBadge}`}>
            {prediction.performance_level}
          </span>
        </div>

        {/* Classification */}
        <div className="card p-5 space-y-3">
          <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium">Score Range</span>
          <p className="text-sm text-foreground leading-relaxed">
            Students in the <strong>{prediction.performance_level}</strong> category typically score{' '}
            {prediction.performance_level === 'Excellent' ? '85–100%'
              : prediction.performance_level === 'Good' ? '70–85%'
              : prediction.performance_level === 'Average' ? '50–70%'
              : '0–50%'}.
          </p>
        </div>

        {/* Confidence & Risk */}
        <div className="card p-5 space-y-4">
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-medium">
              <span className="text-muted-foreground">Confidence</span>
              <span className="text-foreground font-semibold">{prediction.confidence_score.toFixed(1)}%</span>
            </div>
            <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
              <div className="h-full rounded-full bg-blue-500" style={{ width: `${prediction.confidence_score}%` }} />
            </div>
          </div>
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-medium">
              <span className="text-muted-foreground">Academic Risk</span>
              <span className={`font-semibold ${riskColor}`}>{prediction.risk_level}</span>
            </div>
            <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
              <div className={`h-full rounded-full ${riskBarColor}`} style={{ width: riskBarWidth }} />
            </div>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Confidence reflects input deviation from historical averages.
          </p>
        </div>
      </div>

      {/* Assessment Profile */}
      <div className="card p-5 space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Performance Assessment</h3>
          <p className="text-xs text-muted-foreground mt-0.5">Breakdown based on study habits and academic input</p>
        </div>

        {prediction.summary && (
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-md flex gap-2.5 items-start dark:bg-amber-950/20 dark:border-amber-800">
            <Lightbulb className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-foreground leading-relaxed">{prediction.summary}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Strengths */}
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-md space-y-2 dark:bg-emerald-950/20 dark:border-emerald-800">
            <div className="flex items-center gap-1.5 text-emerald-700 dark:text-emerald-400 text-sm font-semibold">
              <CheckCircle className="w-4 h-4" />
              Strengths
            </div>
            <ul className="space-y-1.5">
              {prediction.strengths.length > 0 ? prediction.strengths.map((s: string, i: number) => (
                <li key={i} className="flex items-start gap-1.5 text-sm text-foreground">
                  <span className="text-emerald-500 mt-0.5">•</span>
                  <span>{s}</span>
                </li>
              )) : (
                <li className="text-sm text-muted-foreground italic">No major strengths identified.</li>
              )}
            </ul>
          </div>

          {/* Weaknesses */}
          <div className="p-4 bg-red-50 border border-red-200 rounded-md space-y-2 dark:bg-red-950/20 dark:border-red-800">
            <div className="flex items-center gap-1.5 text-red-700 dark:text-red-400 text-sm font-semibold">
              <XCircle className="w-4 h-4" />
              Areas for Improvement
            </div>
            <ul className="space-y-1.5">
              {prediction.weaknesses.length > 0 ? prediction.weaknesses.map((w: string, i: number) => (
                <li key={i} className="flex items-start gap-1.5 text-sm text-foreground">
                  <span className="text-red-500 mt-0.5">•</span>
                  <span>{w}</span>
                </li>
              )) : (
                <li className="text-sm text-emerald-600 font-medium">All parameters meet baseline — great work!</li>
              )}
            </ul>
          </div>
        </div>
      </div>

      {/* 4-Week Roadmap */}
      <div className="card p-5 space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-foreground">4-Week Study Roadmap</h3>
          <p className="text-xs text-muted-foreground mt-0.5">Personalized milestones based on weak areas</p>
        </div>

        <div className="space-y-5 border-l-2 border-gray-200 dark:border-gray-700 pl-5 ml-2">
          {prediction.learning_roadmap.map((weekData: any, idx: number) => (
            <div key={idx} className="relative space-y-2">
              <div className="absolute -left-[25px] top-0.5 w-3.5 h-3.5 rounded-full bg-white dark:bg-card border-2 border-blue-500" />
              <div className="space-y-1">
                <span className="text-xs font-semibold text-blue-600 uppercase tracking-wide">
                  Week {weekData.week}: {weekData.title}
                </span>
                <p className="text-sm font-medium text-foreground">{weekData.focus}</p>
              </div>
              <ul className="space-y-1.5 bg-muted/40 border border-border rounded-md p-3">
                {weekData.tasks.map((task: string, ti: number) => (
                  <li key={ti} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <span className="text-blue-500 font-bold mt-0.5">·</span>
                    <span>{task}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
export default Results;
