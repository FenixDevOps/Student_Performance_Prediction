import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { analyticsService, predictionService } from '../services/api';
import { DashboardAnalytics, PredictionRecord } from '../types';
import {
  Users, Award, TrendingUp, AlertTriangle,
  Plus, FileSpreadsheet, FileDown, Trash2, Eye, BookOpen, CheckCircle
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line
} from 'recharts';

const levelBadge = (level: string) => ({
  Excellent: 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400',
  Good: 'bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-950/30 dark:text-blue-400',
  Average: 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/30 dark:text-amber-400',
  'At Risk': 'bg-red-50 text-red-700 border border-red-200 dark:bg-red-950/30 dark:text-red-400',
}[level] ?? 'bg-gray-100 text-gray-700');

const riskBadge = (risk: string) => ({
  High: 'bg-red-50 text-red-700 border border-red-200 dark:bg-red-950/30 dark:text-red-400',
  Medium: 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/30 dark:text-amber-400',
  Low: 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400',
}[risk] ?? 'bg-gray-100 text-gray-700');

const PERF_COLORS = { Excellent: '#10b981', Good: '#3b82f6', Average: '#f59e0b', 'At Risk': '#ef4444' };
const RISK_COLORS = { Low: '#10b981', Medium: '#f59e0b', High: '#ef4444' };

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
}
const StatCard: React.FC<StatCardProps> = ({ label, value, icon }) => (
  <div className="card p-4 flex items-center justify-between">
    <div>
      <p className="text-xs text-muted-foreground font-medium">{label}</p>
      <p className="text-2xl font-bold text-foreground mt-0.5">{value}</p>
    </div>
    <div className="w-9 h-9 rounded-md bg-muted flex items-center justify-center text-muted-foreground">
      {icon}
    </div>
  </div>
);

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const data = await analyticsService.getAnalytics();
      setAnalytics(data);
    } catch { showToast('Failed to load dashboard.', 'error'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchDashboardData(); }, []);

  const handleDeleteRecord = async (id: number) => {
    if (!window.confirm('Delete this prediction record?')) return;
    try {
      setDeletingId(id);
      await predictionService.deleteRecord(id);
      showToast('Record deleted.', 'success');
      fetchDashboardData();
    } catch { showToast('Failed to delete record.', 'error'); }
    finally { setDeletingId(null); }
  };

  const handleExcelExport = async () => {
    try {
      showToast('Preparing Excel export...', 'info');
      await predictionService.downloadExcel();
      showToast('Excel downloaded!', 'success');
    } catch { showToast('Failed to export.', 'error'); }
  };

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="h-20 card" />)}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-72 card" />
          <div className="h-72 card" />
        </div>
      </div>
    );
  }

  if (!analytics) return <div className="text-center py-10 text-sm text-muted-foreground">No data available.</div>;

  // ── STUDENT VIEW ──────────────────────────────────────────────────────────
  if (analytics.role === 'student') {
    const sd = analytics;
    const metrics = sd.current_metrics;

    if (!metrics || sd.total === 0) {
      return (
        <div className="max-w-2xl mx-auto text-center py-16 px-4 space-y-6">
          <div className="w-16 h-16 rounded-full bg-blue-50 text-blue-500 dark:bg-blue-950/30 dark:text-blue-400 flex items-center justify-center mx-auto">
            <BookOpen className="w-8 h-8" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-foreground">Welcome to your Student Portal, {user?.full_name}!</h2>
            <p className="text-sm text-muted-foreground max-w-md mx-auto leading-relaxed">
              Your teachers have not submitted any academic evaluation reports for you yet. 
              Once a teacher performs a performance prediction for you, your grades, academic risk metrics, and custom study roadmap will appear here.
            </p>
          </div>
          <div className="pt-2">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-muted text-muted-foreground text-xs font-medium border border-border">
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              Awaiting first evaluation
            </div>
          </div>
        </div>
      );
    }

    const riskStyles: Record<string, string> = {
      High: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-950/30 dark:border-red-800 dark:text-red-300',
      Medium: 'bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-950/30 dark:border-amber-800 dark:text-amber-300',
      Low: 'bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950/30 dark:border-emerald-800 dark:text-emerald-300',
    };

    return (
      <div className="space-y-4">
        {/* Status Banner */}
        <div className={`p-4 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${riskStyles[sd.risk_level] || riskStyles.Low}`}>
          <div>
            <p className="text-sm font-semibold">Academic Status: {sd.risk_level} Risk</p>
            <p className="text-sm opacity-90 mt-0.5">
              Your latest predicted score is <strong>{sd.latest_score}%</strong> — {sd.performance_level}
            </p>
          </div>
          {sd.total > 0 && (
            <Link to="/analytics" className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white dark:bg-card text-foreground border border-border text-sm rounded-md shadow-sm hover:bg-muted transition-colors self-start sm:self-auto">
              <Eye className="w-3.5 h-3.5" /> View History
            </Link>
          )}
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="Reports Logged" value={sd.total} icon={<BookOpen className="w-4 h-4" />} />
          <StatCard label="Avg Predicted Grade" value={`${sd.avg_score}%`} icon={<Award className="w-4 h-4" />} />
          <StatCard label="Peak Score" value={`${sd.max_score}%`} icon={<TrendingUp className="w-4 h-4" />} />
          <StatCard label="Confidence" value={`${sd.confidence_score}%`} icon={<CheckCircle className="w-4 h-4" />} />
        </div>

        {/* Study Stats + History Chart */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="card p-5 space-y-4">
            <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">Study Habits</h3>
            {[
              { label: 'Attendance', value: metrics.attendance, max: 100, unit: '%' },
              { label: 'Study Hours/wk', value: metrics.study_hours, max: 40, unit: 'h' },
              { label: 'Assignment Rate', value: metrics.assignment_completion, max: 100, unit: '%' },
              { label: 'Problems Solved', value: metrics.practice_problems, max: 200, unit: '' },
            ].map(({ label, value, max, unit }) => {
              const good = value >= max * 0.6;
              return (
                <div key={label} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-muted-foreground">{label}</span>
                    <span className={good ? 'text-emerald-600' : 'text-red-500'}>{value}{unit}</span>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${good ? 'bg-emerald-500' : 'bg-red-500'}`}
                      style={{ width: `${Math.min((value / max) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="card p-5 md:col-span-2 flex flex-col">
            <h3 className="text-sm font-semibold text-foreground mb-4">Grade Prediction History</h3>
            <div className="flex-1" style={{ minHeight: 200 }}>
              {sd.history.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={sd.history}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.2} />
                    <XAxis dataKey="date" tickLine={false} tick={{ fontSize: 10 }} />
                    <YAxis domain={[0, 100]} tickLine={false} tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ fontSize: 12, borderRadius: 6, border: '1px solid #E5E7EB' }} />
                    <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                  No history yet — submit a prediction to get started.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── TEACHER / ADMIN VIEW ──────────────────────────────────────────────────
  const td = analytics;
  const perfData = Object.entries(td.performance_dist).map(([name, value]) => ({ name, value }));
  const riskData = Object.entries(td.risk_dist).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-4">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total Predictions" value={td.total} icon={<Users className="w-4 h-4" />} />
        <StatCard label="Avg Predicted Grade" value={`${td.avg_score}%`} icon={<Award className="w-4 h-4" />} />
        <StatCard label="Peak Grade" value={`${td.max_score}%`} icon={<TrendingUp className="w-4 h-4" />} />
        <StatCard label="Lowest Grade" value={`${td.min_score}%`} icon={<AlertTriangle className="w-4 h-4" />} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-5 flex flex-col" style={{ height: 280 }}>
          <h3 className="text-sm font-semibold text-foreground mb-3">Grade Category Breakdown</h3>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={perfData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.2} />
                <XAxis dataKey="name" tickLine={false} tick={{ fontSize: 11 }} />
                <YAxis tickLine={false} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 6, border: '1px solid #E5E7EB' }} />
                <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                  {perfData.map((entry, i) => (
                    <Cell key={i} fill={PERF_COLORS[entry.name as keyof typeof PERF_COLORS] || '#6b7280'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card p-5 flex flex-col" style={{ height: 280 }}>
          <h3 className="text-sm font-semibold text-foreground mb-3">Student Risk Distribution</h3>
          <div className="flex-1 flex items-center gap-4">
            <div className="flex-1 h-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={riskData} cx="50%" cy="50%" innerRadius={50} outerRadius={75} paddingAngle={3} dataKey="value">
                    {riskData.map((entry, i) => (
                      <Cell key={i} fill={RISK_COLORS[entry.name as keyof typeof RISK_COLORS] || '#6b7280'} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ fontSize: 12, borderRadius: 6, border: '1px solid #E5E7EB' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-2.5 flex-shrink-0">
              {riskData.map((entry) => (
                <div key={entry.name} className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: RISK_COLORS[entry.name as keyof typeof RISK_COLORS] }} />
                  <span className="text-muted-foreground">{entry.name}:</span>
                  <span className="font-semibold text-foreground">{entry.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Predictions Table */}
      <div className="card p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border mb-3">
          <div>
            <h3 className="text-sm font-semibold text-foreground">Recent Predictions</h3>
            <p className="text-xs text-muted-foreground mt-0.5">Student evaluations across all teachers</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={handleExcelExport}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-border bg-card hover:bg-muted text-foreground text-sm rounded-md transition-colors">
              <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
              Export Excel
            </button>
            <Link to="/predict"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md transition-colors">
              <Plus className="w-4 h-4" />
              New Student
            </Link>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="border-b border-border text-xs text-muted-foreground">
                <th className="py-2.5 px-3 font-medium">Student</th>
                <th className="py-2.5 px-3 text-center font-medium">Score</th>
                <th className="py-2.5 px-3 font-medium">Level</th>
                <th className="py-2.5 px-3 font-medium">Risk</th>
                <th className="py-2.5 px-3 font-medium">Date</th>
                <th className="py-2.5 px-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {td.recent_history.length > 0 ? td.recent_history.map((record) => (
                <tr key={record.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                  <td className="py-3 px-3 font-medium text-foreground">{record.name}</td>
                  <td className="py-3 px-3 text-center font-semibold text-blue-600">{record.score.toFixed(1)}%</td>
                  <td className="py-3 px-3">
                    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${levelBadge(record.level)}`}>
                      {record.level}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${riskBadge(record.risk)}`}>
                      {record.risk}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-xs text-muted-foreground">{record.date}</td>
                  <td className="py-3 px-3">
                    <div className="flex items-center justify-end gap-1">
                      <Link to={`/analytics?query=${encodeURIComponent(record.name)}`}
                        className="p-1.5 rounded border border-border hover:bg-muted text-muted-foreground hover:text-foreground transition-colors" title="View Analytics">
                        <Eye className="w-3.5 h-3.5" />
                      </Link>
                      <button
                        onClick={async () => {
                          try { showToast('Generating PDF...', 'info'); await predictionService.downloadPdf(record.id, record.name); showToast('PDF downloaded!', 'success'); }
                          catch { showToast('Failed to download report.', 'error'); }
                        }}
                        className="p-1.5 rounded border border-border hover:bg-muted text-muted-foreground hover:text-foreground transition-colors" title="Download PDF">
                        <FileDown className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteRecord(record.id)}
                        disabled={deletingId === record.id}
                        className="p-1.5 rounded border border-border hover:bg-red-50 text-muted-foreground hover:text-red-600 dark:hover:bg-red-950/30 transition-colors" title="Delete">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={6} className="py-10 text-center text-sm text-muted-foreground">
                    No predictions yet. <Link to="/predict" className="text-blue-600 hover:underline">Evaluate a student</Link> to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
export default Dashboard;
