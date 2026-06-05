import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { predictionService, analyticsService } from '../services/api';
import { useToast } from '../hooks/useToast';
import { PredictionRecord } from '../types';
import {
  Search,
  FileDown,
  Trash2,
  X,
  CheckCircle,
  XCircle,
  Lightbulb,
  Compass,
  Eye,
} from 'lucide-react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const levelBadge = (level: string) => ({
  Excellent: 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-800',
  Good: 'bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-950/30 dark:text-blue-400 dark:border-blue-800',
  Average: 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-800',
  'At Risk': 'bg-red-50 text-red-700 border border-red-200 dark:bg-red-950/30 dark:text-red-400 dark:border-red-800',
}[level] ?? 'bg-gray-100 text-gray-700 border border-gray-200');

const riskBadge = (risk: string) => ({
  High: 'bg-red-50 text-red-700 border border-red-200 dark:bg-red-950/30 dark:text-red-400 dark:border-red-800',
  Medium: 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-800',
  Low: 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-800',
}[risk] ?? 'bg-gray-100 text-gray-700');

export const Analytics: React.FC = () => {
  const { showToast } = useToast();
  const [searchParams] = useSearchParams();

  const [query, setQuery] = useState(searchParams.get('query') || '');
  const [level, setLevel] = useState('All');
  const [sort, setSort] = useState('latest');
  const [records, setRecords] = useState<PredictionRecord[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [scatterData, setScatterData] = useState<any[]>([]);
  const [loadingAnalytics, setLoadingAnalytics] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState<PredictionRecord | null>(null);

  const fetchAnalyticsData = async () => {
    try {
      setLoadingAnalytics(true);
      const data = await analyticsService.getAnalytics();
      if (data.scatter_data) setScatterData(data.scatter_data);
    } catch { showToast('Failed to load chart metrics.', 'error'); }
    finally { setLoadingAnalytics(false); }
  };

  const fetchHistoryRecords = async () => {
    try {
      setLoadingHistory(true);
      const data = await predictionService.getHistory({ query: query || undefined, level: level !== 'All' ? level : undefined, sort });
      setRecords(data);
    } catch { showToast('Failed to load records.', 'error'); }
    finally { setLoadingHistory(false); }
  };

  useEffect(() => { fetchAnalyticsData(); }, []);
  useEffect(() => { fetchHistoryRecords(); }, [query, level, sort]);

  const handleDeleteRecord = async (id: number) => {
    if (!window.confirm('Delete this record?')) return;
    try {
      await predictionService.deleteRecord(id);
      showToast('Record deleted.', 'success');
      fetchHistoryRecords();
      fetchAnalyticsData();
    } catch { showToast('Deletion failed.', 'error'); }
  };

  const handleDownloadPdf = async (rec: PredictionRecord) => {
    try {
      showToast('Preparing PDF...', 'info');
      await predictionService.downloadPdf(rec.id, rec.student_name);
      showToast('PDF downloaded!', 'success');
    } catch { showToast('PDF generation failed.', 'error'); }
  };

  const inputClass = "px-3 py-1.5 bg-background border border-border rounded-md text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-colors";

  return (
    <div className="space-y-4">
      {/* Scatter Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[
          { title: 'Attendance vs. Predicted Score', xKey: 'attendance', xName: 'Attendance', xUnit: '%' },
          { title: 'Study Hours vs. Predicted Score', xKey: 'study_hours', xName: 'Study Hours', xUnit: ' h' },
        ].map(({ title, xKey, xName, xUnit }) => (
          <div key={xKey} className="card p-4 flex flex-col" style={{ height: 280 }}>
            <h3 className="text-sm font-semibold text-foreground mb-1">{title}</h3>
            <p className="text-xs text-muted-foreground mb-3">Correlation across all student evaluations</p>
            <div className="flex-1">
              {loadingAnalytics
                ? <div className="h-full bg-muted animate-pulse rounded-md" />
                : (
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart margin={{ top: 5, right: 10, bottom: 5, left: -10 }}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                      <XAxis type="number" dataKey={xKey} name={xName} unit={xUnit} tick={{ fontSize: 10 }} tickLine={false} />
                      <YAxis type="number" dataKey="score" name="Exam Grade" unit="%" tick={{ fontSize: 10 }} tickLine={false} />
                      <Tooltip contentStyle={{ fontSize: 12, borderRadius: 6, border: '1px solid #E5E7EB' }} />
                      <Scatter data={scatterData} fill="#3b82f6" />
                    </ScatterChart>
                  </ResponsiveContainer>
                )}
            </div>
          </div>
        ))}
      </div>

      {/* Records Table */}
      <div className="card p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border">
          <div>
            <h3 className="text-sm font-semibold text-foreground">Evaluation Logs</h3>
            <p className="text-xs text-muted-foreground mt-0.5">Filter and search all prediction records</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by name..."
                className={inputClass + " pl-8 w-44"}
              />
            </div>
            <select value={level} onChange={(e) => setLevel(e.target.value)} className={inputClass + " cursor-pointer"}>
              <option value="All">All levels</option>
              <option value="Excellent">Excellent (≥85%)</option>
              <option value="Good">Good (70–85%)</option>
              <option value="Average">Average (50–70%)</option>
              <option value="At Risk">At Risk (&lt;50%)</option>
            </select>
            <select value={sort} onChange={(e) => setSort(e.target.value)} className={inputClass + " cursor-pointer"}>
              <option value="latest">Latest first</option>
              <option value="score">Highest score</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          {loadingHistory ? (
            <div className="space-y-2 py-4 animate-pulse">
              {[...Array(4)].map((_, i) => <div key={i} className="h-10 bg-muted rounded-md" />)}
            </div>
          ) : (
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-border text-xs text-muted-foreground">
                  <th className="py-2.5 px-3 font-medium">Student</th>
                  <th className="py-2.5 px-3 text-center font-medium">Score</th>
                  <th className="py-2.5 px-3 font-medium">Level</th>
                  <th className="py-2.5 px-3 font-medium">Risk</th>
                  <th className="py-2.5 px-3 text-center font-medium">Confidence</th>
                  <th className="py-2.5 px-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {records.length > 0 ? records.map((record) => (
                  <tr key={record.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                    <td className="py-3 px-3 font-medium text-foreground">{record.student_name}</td>
                    <td className="py-3 px-3 text-center font-semibold text-blue-600">{record.predicted_score.toFixed(1)}%</td>
                    <td className="py-3 px-3">
                      <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${levelBadge(record.performance_level)}`}>
                        {record.performance_level}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${riskBadge(record.risk_level)}`}>
                        {record.risk_level}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-center text-xs text-muted-foreground">{record.confidence_score.toFixed(1)}%</td>
                    <td className="py-3 px-3">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => setSelectedRecord(record)} title="View report"
                          className="p-1.5 rounded border border-border hover:bg-muted text-muted-foreground hover:text-foreground transition-colors">
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button onClick={() => handleDownloadPdf(record)} title="Download PDF"
                          className="p-1.5 rounded border border-border hover:bg-muted text-muted-foreground hover:text-foreground transition-colors">
                          <FileDown className="w-3.5 h-3.5" />
                        </button>
                        <button onClick={() => handleDeleteRecord(record.id)} title="Delete"
                          className="p-1.5 rounded border border-border hover:bg-red-50 text-muted-foreground hover:text-red-600 dark:hover:bg-red-950/30 transition-colors">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={6} className="py-10 text-center text-sm text-muted-foreground">
                      No records matched your filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Side Drawer */}
      {selectedRecord && (
        <>
          <div className="fixed inset-0 bg-black/40 z-40" onClick={() => setSelectedRecord(null)} />
          <div className="fixed top-0 bottom-0 right-0 w-full max-w-lg bg-card border-l border-border z-50 flex flex-col overflow-y-auto shadow-xl">
            {/* Drawer Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-border flex-shrink-0">
              <div>
                <h3 className="text-sm font-semibold text-foreground">{selectedRecord.student_name}'s Report</h3>
                <span className="text-xs text-muted-foreground">Evaluated on {selectedRecord.created_at.slice(0, 10)}</span>
              </div>
              <button onClick={() => setSelectedRecord(null)} className="p-1.5 rounded hover:bg-muted text-muted-foreground">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 p-5 space-y-5">
              {/* Score block */}
              <div className="p-4 bg-muted/30 border border-border rounded-md flex items-center justify-between">
                <div>
                  <span className="text-xs text-muted-foreground block mb-1">Predicted Score</span>
                  <span className="text-3xl font-bold text-blue-600">{selectedRecord.predicted_score.toFixed(1)}%</span>
                </div>
                <div className="text-right space-y-1">
                  <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded ${levelBadge(selectedRecord.performance_level)}`}>
                    {selectedRecord.performance_level}
                  </span>
                  <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded ml-1 ${riskBadge(selectedRecord.risk_level)}`}>
                    {selectedRecord.risk_level} Risk
                  </span>
                </div>
              </div>

              {/* Parameters */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Parameters</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {[
                    ['Attendance', `${selectedRecord.attendance}%`],
                    ['Previous GPA', `${selectedRecord.previous_gpa}/10`],
                    ['Study Hours', `${selectedRecord.study_hours} h/wk`],
                    ['Mock Exam', `${selectedRecord.practice_test_score}%`],
                  ].map(([label, value]) => (
                    <div key={label} className="p-3 bg-muted/30 border border-border rounded-md flex justify-between">
                      <span className="text-muted-foreground">{label}</span>
                      <strong className="font-semibold text-foreground">{value}</strong>
                    </div>
                  ))}
                </div>
              </div>

              {/* Summary */}
              {selectedRecord.summary && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-md flex gap-2 dark:bg-amber-950/20 dark:border-amber-800">
                  <Lightbulb className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-foreground">{selectedRecord.summary}</p>
                </div>
              )}

              {/* Strengths & Weaknesses */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wide block">Strengths</span>
                  <ul className="space-y-1">
                    {selectedRecord.strengths.map((s, i) => (
                      <li key={i} className="flex gap-1.5 text-xs text-muted-foreground">
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-red-600 uppercase tracking-wide block">Weaknesses</span>
                  <ul className="space-y-1">
                    {selectedRecord.weaknesses.map((w, i) => (
                      <li key={i} className="flex gap-1.5 text-xs text-muted-foreground">
                        <XCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0 mt-0.5" />
                        <span>{w}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Roadmap */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5 text-blue-600" /> Study Roadmap
                </h4>
                <div className="space-y-3 border-l-2 border-gray-200 dark:border-gray-700 pl-4 ml-1.5">
                  {selectedRecord.learning_roadmap.map((week, idx) => (
                    <div key={idx} className="relative space-y-0.5">
                      <div className="absolute -left-[21px] top-1 w-3 h-3 rounded-full bg-card border-2 border-blue-500" />
                      <span className="text-[10px] font-bold text-blue-600 uppercase">Week {week.week}: {week.title}</span>
                      <p className="text-xs text-muted-foreground">{week.focus}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-border">
              <button
                onClick={() => handleDownloadPdf(selectedRecord)}
                className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md flex items-center justify-center gap-1.5 transition-colors"
              >
                <FileDown className="w-4 h-4" />
                Download PDF Report
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
export default Analytics;
