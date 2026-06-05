import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { analyticsService, predictionService, alertsService } from '../services/api';
import { DashboardAnalytics, PredictionRecord } from '../types';
import {
  Users, Award, TrendingUp, AlertTriangle,
  Plus, FileSpreadsheet, FileDown, Trash2, Eye, BookOpen, CheckCircle,
  Bell, Mail, Check, Send, Flame, Sparkles, X
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
  const { user, updateUser } = useAuth();
  const { showToast } = useToast();

  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Gamification & Alerts state
  const [alerts, setAlerts] = useState<any[]>([]);
  const [parentEmailModalOpen, setParentEmailModalOpen] = useState(false);
  const [selectedRecordId, setSelectedRecordId] = useState<number | null>(null);
  const [parentEmail, setParentEmail] = useState('');
  const [sendingEmail, setSendingEmail] = useState(false);

  // Student specific states
  const [roadmapTasks, setRoadmapTasks] = useState<any[]>([]);
  const [predictionId, setPredictionId] = useState<number | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<{ sender: 'user' | 'bot'; text: string }[]>([]);
  const [chatLoading, setChatLoading] = useState(false);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const data = await analyticsService.getAnalytics();
      setAnalytics(data);

      if (user && (user.role === 'teacher' || user.role === 'admin')) {
        const activeAlerts = await alertsService.getAlerts();
        setAlerts(activeAlerts);
      } else if (user && user.role === 'student') {
        const rdata = await predictionService.getRoadmapTasks();
        setPredictionId(rdata.prediction_id || null);
        setRoadmapTasks(rdata.tasks || []);
      }
    } catch {
      showToast('Failed to load dashboard.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [user?.role]);

  // Load initial greeting message for the chatbot
  useEffect(() => {
    if (analytics && analytics.role === 'student' && user) {
      setChatMessages([
        {
          sender: 'bot',
          text: `Hi ${user.full_name}! 🎒 I am your AI Study Companion. Ask me questions about your 4-week study roadmap, study methods like Pomodoro, or strategies to improve in your weaker areas!`
        }
      ]);
    }
  }, [analytics, user]);

  const handleDeleteRecord = async (id: number) => {
    if (!window.confirm('Delete this prediction record?')) return;
    try {
      setDeletingId(id);
      await predictionService.deleteRecord(id);
      showToast('Record deleted.', 'success');
      fetchDashboardData();
    } catch {
      showToast('Failed to delete record.', 'error');
    } finally {
      setDeletingId(null);
    }
  };

  const handleExcelExport = async () => {
    try {
      showToast('Preparing Excel export...', 'info');
      await predictionService.downloadExcel();
      showToast('Excel downloaded!', 'success');
    } catch {
      showToast('Failed to export.', 'error');
    }
  };

  const handleToggleTask = async (task: any) => {
    if (!predictionId) return;
    try {
      const newCompletedState = !task.completed;
      // Optimistic update
      setRoadmapTasks(prev =>
        prev.map(t =>
          t.week === task.week && t.task_index === task.task_index
            ? { ...t, completed: newCompletedState }
            : t
        )
      );

      const res = await predictionService.toggleRoadmapTask({
        prediction_id: predictionId,
        week: task.week,
        task_index: task.task_index,
        completed: newCompletedState
      });

      if (res.success) {
        if (newCompletedState) {
          showToast(`Task completed! +${res.xp_gained} XP!`, 'success');
        } else {
          showToast('Task status updated.', 'info');
        }

        if (user) {
          updateUser({
            ...user,
            xp_points: res.total_xp,
            current_streak: res.streak
          });
        }
      }
    } catch (err) {
      showToast('Failed to update task state.', 'error');
      // Revert optimistic update
      setRoadmapTasks(prev =>
        prev.map(t =>
          t.week === task.week && t.task_index === task.task_index
            ? { ...t, completed: task.completed }
            : t
        )
      );
    }
  };

  const handleResolveAlert = async (id: number) => {
    try {
      await alertsService.resolveAlert(id);
      showToast('Alert resolved.', 'success');
      const activeAlerts = await alertsService.getAlerts();
      setAlerts(activeAlerts);
    } catch {
      showToast('Failed to resolve alert.', 'error');
    }
  };

  const handleOpenEmailModal = (recordId: number) => {
    setSelectedRecordId(recordId);
    setParentEmail('');
    setParentEmailModalOpen(true);
  };

  const handleSendParentEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRecordId || !parentEmail.trim()) return;
    try {
      setSendingEmail(true);
      const res = await alertsService.sendParentEmail({
        record_id: selectedRecordId,
        parent_email: parentEmail.trim()
      });
      if (res.success) {
        showToast(res.message, 'success');
        setParentEmailModalOpen(false);
        // If there is an alert for this student, resolve it dynamically
        const matchingAlert = alerts.find(a => {
          const matchingRec = (analytics as any)?.recent_history?.find((r: any) => r.id === selectedRecordId);
          return matchingRec && a.student_name === matchingRec.name;
        });
        if (matchingAlert) {
          await handleResolveAlert(matchingAlert.id);
        }
      }
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to send notification.', 'error');
    } finally {
      setSendingEmail(false);
    }
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

    const xp = user?.xp_points || 0;
    const currentLevel = Math.floor(xp / 100) + 1;
    const levelProgress = xp % 100;
    const streak = user?.current_streak || 0;

    return (
      <div className="space-y-4">
        {/* Status Banner */}
        <div className={`p-4 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${riskStyles[sd.risk_level] || riskStyles.Low}`}>
          <div>
            <p className="text-sm font-semibold flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4" /> Academic Status: {sd.risk_level} Risk
            </p>
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

        {/* Gamification, Habits & History Chart */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Level Progress Gamification Card */}
          <div className="card p-5 space-y-4 flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2 flex items-center justify-between">
                <span className="flex items-center gap-1.5"><Sparkles className="w-4 h-4 text-blue-500" /> Gamification Stats</span>
                <span className="text-[10px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-400 px-2 py-0.5 rounded-full">LVL {currentLevel}</span>
              </h3>
              <div className="mt-4 flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">Total XP Points</p>
                  <p className="text-2xl font-black text-foreground mt-0.5">{xp} XP</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground">Daily Streak</p>
                  <p className="text-xl font-bold mt-0.5 flex items-center gap-1 justify-end text-orange-500 animate-bounce">
                    <Flame className="w-5 h-5 fill-orange-500 text-orange-500" /> {streak} Day{streak !== 1 && 's'}
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-1 mt-4">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Progress to Level {currentLevel + 1}</span>
                <span>{levelProgress} / 100 XP</span>
              </div>
              <div className="h-2.5 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-500"
                  style={{ width: `${levelProgress}%` }}
                />
              </div>
            </div>
            <p className="text-[10px] text-muted-foreground mt-2 italic">
              ⭐ Check off tasks on your study roadmap below to earn 10 XP each. Complete a full week for a bonus +50 XP!
            </p>
          </div>

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

          <div className="card p-5 flex flex-col">
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
                  No history yet.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Study Planner / Kanban Board */}
        <div className="card p-5 space-y-4">
          <div>
            <h3 className="text-base font-bold text-foreground">Interactive Study Planner (4-Week Roadmap)</h3>
            <p className="text-xs text-muted-foreground mt-0.5">Track your study milestones, tick off completed tasks, and level up!</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(wNum => {
              const weekTasks = roadmapTasks.filter(t => t.week === wNum);
              const weekTitle = weekTasks[0]?.title || `Week ${wNum}`;
              const weekFocus = weekTasks[0]?.focus || 'Goal';

              const total = weekTasks.length;
              const completedCount = weekTasks.filter(t => t.completed).length;
              const percent = total > 0 ? Math.round((completedCount / total) * 100) : 0;

              return (
                <div key={wNum} className="flex flex-col bg-muted/20 dark:bg-muted/5 rounded-lg border border-border p-4 space-y-3">
                  <div className="border-b border-border/60 pb-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Week {wNum}</span>
                      <span className="text-[10px] font-bold bg-blue-50 text-blue-800 dark:bg-blue-950/40 dark:text-blue-300 px-1.5 py-0.5 rounded-full">
                        {completedCount}/{total} Done
                      </span>
                    </div>
                    <h4 className="text-sm font-bold text-foreground truncate mt-1">{weekTitle}</h4>
                    <p className="text-[11px] text-muted-foreground truncate mt-0.5" title={weekFocus}>
                      Focus: {weekFocus}
                    </p>
                    <div className="h-1 bg-muted rounded-full mt-2 overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 transition-all duration-300"
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  </div>

                  <div className="space-y-2 flex-1 overflow-y-auto max-h-[220px] pr-0.5">
                    {weekTasks.map((t, idx) => (
                      <div
                        key={idx}
                        onClick={() => handleToggleTask(t)}
                        className={`p-3 rounded-md border text-xs cursor-pointer select-none transition-all flex items-start gap-2.5 
                          ${t.completed
                            ? 'bg-emerald-500/5 dark:bg-emerald-500/10 border-emerald-500/30 text-emerald-800 dark:text-emerald-400'
                            : 'bg-card border-border hover:border-blue-500/40 text-foreground'
                          }`}
                      >
                        <input
                          type="checkbox"
                          checked={t.completed}
                          onChange={() => {}}
                          className="mt-0.5 h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                        />
                        <span className={t.completed ? 'line-through text-muted-foreground' : ''}>
                          {t.task}
                        </span>
                      </div>
                    ))}
                    {weekTasks.length === 0 && (
                      <div className="text-center py-6 text-xs text-muted-foreground">
                        No tasks found for this week.
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Floating Chatbot Assistant */}
        {predictionId && (
          <div className="fixed bottom-6 right-6 z-50">
            <button
              onClick={() => setIsChatOpen(!isChatOpen)}
              className="w-14 h-14 bg-gradient-to-tr from-blue-600 to-indigo-600 text-white rounded-full flex items-center justify-center shadow-lg hover:shadow-blue-500/20 hover:scale-105 active:scale-95 transition-all"
            >
              <Sparkles className="w-6 h-6 animate-pulse" />
            </button>

            {isChatOpen && (
              <div className="absolute bottom-16 right-0 w-[350px] sm:w-[400px] h-[480px] bg-card border border-border rounded-xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-5">
                <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-2.5 w-2.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                    </span>
                    <div className="text-left">
                      <h4 className="text-sm font-bold">AI Study Companion</h4>
                      <p className="text-[10px] opacity-80">Ask about your roadmap tasks</p>
                    </div>
                  </div>
                  <button onClick={() => setIsChatOpen(false)} className="text-white hover:opacity-80">
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-muted/10">
                  {chatMessages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[80%] rounded-lg p-3 text-xs leading-relaxed ${
                        msg.sender === 'user'
                          ? 'bg-blue-600 text-white rounded-br-none font-medium'
                          : 'bg-muted border border-border text-foreground rounded-bl-none'
                      }`}>
                        {msg.text}
                      </div>
                    </div>
                  ))}
                  {chatLoading && (
                    <div className="flex justify-start">
                      <div className="bg-muted border border-border rounded-lg p-3 text-xs rounded-bl-none text-muted-foreground flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" />
                        <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce [animation-delay:0.2s]" />
                        <span className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce [animation-delay:0.4s]" />
                      </div>
                    </div>
                  )}
                </div>

                <form
                  onSubmit={async (e) => {
                    e.preventDefault();
                    if (!chatInput.trim() || chatLoading) return;

                    const userMsg = chatInput.trim();
                    setChatInput('');
                    setChatMessages(prev => [...prev, { sender: 'user', text: userMsg }]);

                    setChatLoading(true);
                    try {
                      const res = await predictionService.chat({
                        prediction_id: predictionId,
                        message: userMsg
                      });
                      setChatMessages(prev => [...prev, { sender: 'bot', text: res.response }]);
                    } catch (err) {
                      setChatMessages(prev => [...prev, { sender: 'bot', text: "Sorry, the study assistant is currently offline. Focus on completing your study plan tasks!" }]);
                    } finally {
                      setChatLoading(false);
                    }
                  }}
                  className="border-t border-border p-3 flex gap-2 bg-card"
                >
                  <input
                    type="text"
                    placeholder="Ask about your study tasks..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    disabled={chatLoading}
                    className="flex-1 bg-muted border border-border rounded-md px-3 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 text-foreground"
                  />
                  <button
                    type="submit"
                    disabled={chatLoading || !chatInput.trim()}
                    className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-md px-3 py-1.5 text-xs font-semibold flex items-center gap-1 transition-colors"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>
            )}
          </div>
        )}
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

      {/* Active Alerts Panel */}
      {alerts.length > 0 && (
        <div className="card border-red-200 dark:border-red-900 bg-red-50/10 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-red-100 dark:border-red-950 pb-2">
            <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
              <AlertTriangle className="w-5 h-5 animate-pulse" />
              <h3 className="text-sm font-semibold">Active Academic Risk Alerts ({alerts.length})</h3>
            </div>
            <span className="text-[10px] uppercase font-bold text-red-600 bg-red-100 dark:bg-red-950/60 dark:text-red-400 px-2 py-0.5 rounded-full">Action Needed</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {alerts.map((alert) => {
              const matchingRec = td.recent_history.find(r => r.name === alert.student_name);
              return (
                <div key={alert.id} className="bg-card border border-border p-4 rounded-lg flex items-center justify-between shadow-sm">
                  <div className="space-y-1">
                    <p className="text-sm font-bold text-foreground">{alert.student_name}</p>
                    <p className="text-xs text-muted-foreground">
                      Predicted Score: <span className="font-semibold text-red-600">{alert.predicted_score.toFixed(1)}%</span> | Attendance: <span className="font-semibold text-foreground">{alert.attendance}%</span>
                    </p>
                    <p className="text-[10px] text-muted-foreground/85">
                      Alert Triggered: {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        if (matchingRec) {
                          handleOpenEmailModal(matchingRec.id);
                        } else {
                          showToast(`No prediction record found for ${alert.student_name} to send alert.`, 'error');
                        }
                      }}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded shadow-sm transition-colors"
                      title="Dispatch Report to Parent"
                    >
                      <Mail className="w-3.5 h-3.5" /> Parent Alert
                    </button>
                    <button
                      onClick={() => handleResolveAlert(alert.id)}
                      className="p-1.5 border border-border hover:bg-muted text-muted-foreground hover:text-foreground rounded transition-colors"
                      title="Mark as Resolved"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

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
                      {record.risk === 'High' && (
                        <button
                          onClick={() => handleOpenEmailModal(record.id)}
                          className="p-1.5 rounded border border-red-200 hover:bg-red-50 text-red-600 dark:border-red-950 dark:hover:bg-red-950/20 transition-colors"
                          title="Dispatch Parent Report"
                        >
                          <Mail className="w-3.5 h-3.5" />
                        </button>
                      )}
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

      {/* Parent Email Modal Dialog */}
      {parentEmailModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in">
          <div className="bg-card border border-border p-6 rounded-xl shadow-2xl w-full max-w-md space-y-4 relative animate-in zoom-in-95">
            <button
              onClick={() => setParentEmailModalOpen(false)}
              className="absolute top-4 right-4 text-muted-foreground hover:text-foreground"
            >
              <X className="w-4 h-4" />
            </button>
            <div>
              <h3 className="text-base font-bold text-foreground">Academic Status Parent Alert</h3>
              <p className="text-xs text-muted-foreground mt-1">
                Enter the parent or advisor's email address to dispatch the comprehensive student evaluation report PDF.
              </p>
            </div>

            <form onSubmit={handleSendParentEmail} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-muted-foreground">Parent/Advisor Email</label>
                <input
                  type="email"
                  required
                  placeholder="parent@example.com"
                  value={parentEmail}
                  onChange={(e) => setParentEmail(e.target.value)}
                  disabled={sendingEmail}
                  className="w-full bg-muted border border-border rounded-md px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 text-foreground"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setParentEmailModalOpen(false)}
                  disabled={sendingEmail}
                  className="px-3.5 py-2 border border-border rounded-md text-xs font-medium text-foreground hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={sendingEmail || !parentEmail}
                  className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-md text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors"
                >
                  {sendingEmail ? 'Sending...' : 'Send Alert Report'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default Dashboard;
