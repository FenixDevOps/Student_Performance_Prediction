import React, { useEffect, useState } from 'react';
import { modelService } from '../services/api';
import { useToast } from '../hooks/useToast';
import { useAuth } from '../hooks/useAuth';
import { ModelInfo } from '../types';
import { Cpu, CheckCircle, Calendar, Activity, Loader2, Play, Database, Trash2, RefreshCw } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

export const ModelInsights: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState(true);

  // Admin states
  const [retrainHistory, setRetrainHistory] = useState<any[]>([]);
  const [activeAlgo, setActiveAlgo] = useState('');
  const [retraining, setRetraining] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [seeding, setSeeding] = useState(false);

  const fetchModelData = async () => {
    try {
      const data = await modelService.getInfo();
      setModelInfo(data);
      setActiveAlgo(data.model_name);

      if (user?.role === 'admin') {
        const hist = await modelService.getRetrainHistory();
        setRetrainHistory(hist);
      }
    } catch {
      showToast('Failed to load ML model details.', 'error');
    }
  };

  useEffect(() => {
    (async () => {
      setLoading(true);
      await fetchModelData();
      setLoading(false);
    })();
  }, [user?.role]);

  const handleAlgorithmChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const algo = e.target.value;
    if (!algo) return;

    try {
      setLoading(true);
      const res = await modelService.changeActiveAlgorithm(algo);
      showToast(res.message, 'success');
      await fetchModelData();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to switch algorithm.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRetrain = async () => {
    try {
      setRetraining(true);
      showToast('Retraining algorithm candidates on database records...', 'info');
      const res = await modelService.retrain();
      showToast(res.message, 'success');
      await fetchModelData();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Retraining failed.', 'error');
    } finally {
      setRetraining(false);
    }
  };

  const handleClearData = async () => {
    if (!window.confirm('CRITICAL: Delete all historical student evaluations? This action is irreversible.')) return;
    try {
      setClearing(true);
      const res = await modelService.clearData();
      showToast(res.message, 'success');
      await fetchModelData();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to purge data.', 'error');
    } finally {
      setClearing(false);
    }
  };

  const handleSeedData = async () => {
    try {
      setSeeding(true);
      const res = await modelService.seedData();
      showToast(res.message, 'success');
      await fetchModelData();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to seed mock evaluations.', 'error');
    } finally {
      setSeeding(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-20 card rounded-lg" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-80 card rounded-lg" />
          <div className="h-80 card rounded-lg" />
        </div>
      </div>
    );
  }

  if (!modelInfo) return <div className="text-center py-10 text-muted-foreground text-sm">No model statistics found.</div>;

  const featureLabels: Record<string, string> = {
    attendance: 'Attendance Rate',
    previous_gpa: 'Previous GPA',
    study_hours: 'Study Hours',
    assignment_completion: 'Assignment Completion',
    participation_score: 'Class Participation',
    sleep_hours: 'Sleep Hours',
    practice_test_score: 'Mock Exam Score',
    practice_problems: 'Problems Solved',
  };

  const importanceData = Object.entries(modelInfo.feature_importances)
    .map(([feature, value]) => ({ name: featureLabels[feature] || feature, value: value * 100 }))
    .sort((a, b) => b.value - a.value);

  const chartColors = ['#3b82f6', '#10b981', '#6366f1', '#f59e0b', '#f43f5e', '#8b5cf6', '#06b6d4', '#14b8a6'];

  const algorithms = [
    "Linear Regression",
    "Random Forest",
    "Gradient Boosting",
    "Neural Network",
    "Ridge Regression"
  ];

  return (
    <div className="space-y-4">
      {/* Model info header */}
      <div className="card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-md bg-blue-50 text-blue-600 dark:bg-blue-950/40 flex items-center justify-center">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">Active Model: {modelInfo.model_name}</h3>
            <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                Trained: {new Date(modelInfo.trained_at).toLocaleDateString()}
              </span>
              <span className="flex items-center gap-1">
                <Activity className="w-3 h-3" />
                Status: Active
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Charts + Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Feature Importances Chart */}
        <div className="card p-5 flex flex-col" style={{ height: 400 }}>
          <div className="mb-3">
            <h3 className="text-sm font-semibold text-foreground">Feature Importances</h3>
            <p className="text-xs text-muted-foreground">Relative impact of each input on predicted grade</p>
          </div>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={importanceData} layout="vertical" margin={{ top: 5, right: 15, bottom: 5, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal opacity={0.15} vertical={false} />
                <XAxis type="number" unit="%" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 9.5 }} width={125} tickLine={false} axisLine={false} />
                <Tooltip
                  formatter={(val: number) => [`${val.toFixed(2)}%`, 'Importance']}
                  contentStyle={{ fontSize: 12, borderRadius: 6, border: '1px solid #E5E7EB' }}
                />
                <Bar dataKey="value" radius={[0, 3, 3, 0]}>
                  {importanceData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={chartColors[index % chartColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Model comparison */}
        <div className="card p-5 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-foreground">Model Comparison</h3>
            <p className="text-xs text-muted-foreground">Evaluation scores of tested regressors</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border text-muted-foreground">
                  <th className="py-2 pr-3 font-medium">Model</th>
                  <th className="py-2 text-center font-medium">R²</th>
                  <th className="py-2 text-center font-medium">RMSE</th>
                  <th className="py-2 text-center font-medium">MAE</th>
                </tr>
              </thead>
              <tbody>
                {modelInfo.all_results.map((r, idx) => {
                  const isActive = r.name === modelInfo.model_name;
                  return (
                    <tr key={idx} className={`border-b border-border/50 ${isActive ? 'bg-blue-50/50 dark:bg-blue-950/20' : ''}`}>
                      <td className="py-2.5 pr-3">
                        <div className="flex items-center gap-1.5">
                          {isActive && <CheckCircle className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" />}
                          <span className={`font-medium ${isActive ? 'text-blue-700 dark:text-blue-400' : 'text-muted-foreground'}`}>
                            {r.name}
                          </span>
                          {isActive && (
                            <span className="text-[10px] bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400 px-1.5 py-0.5 rounded font-semibold">
                              Active
                            </span>
                          )}
                        </div>
                      </td>
                      <td className={`py-2.5 text-center ${isActive ? 'font-semibold text-foreground' : 'text-muted-foreground'}`}>
                        {r.r2.toFixed(4)}
                      </td>
                      <td className={`py-2.5 text-center ${isActive ? 'font-semibold text-foreground' : 'text-muted-foreground'}`}>
                        {r.rmse.toFixed(3)}
                      </td>
                      <td className={`py-2.5 text-center ${isActive ? 'font-semibold text-foreground' : 'text-muted-foreground'}`}>
                        {r.mae.toFixed(3)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="p-3 bg-muted/40 border border-border rounded-md space-y-1.5 text-xs text-muted-foreground">
            <p className="font-medium text-foreground text-[11px]">Metrics guide</p>
            <p><strong>R²</strong> — Proportion of variance explained. Higher is better.</p>
            <p><strong>RMSE</strong> — Root mean squared error. Lower is better.</p>
            <p><strong>MAE</strong> — Mean absolute error. Lower is better.</p>
          </div>
        </div>
      </div>

      {/* Admin ML Controls & Logs */}
      {user?.role === 'admin' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Controls Card */}
          <div className="card p-5 space-y-5">
            <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2 flex items-center gap-1.5">
              <Database className="w-4 h-4 text-blue-500" /> Admin ML Pipeline Controls
            </h3>

            {/* Algorithm Select */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground">Select Active Regressor Algorithm</label>
              <select
                value={activeAlgo}
                onChange={handleAlgorithmChange}
                className="w-full px-3 py-2 bg-background border border-border rounded-md text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors"
              >
                {algorithms.map(algo => (
                  <option key={algo} value={algo}>{algo}</option>
                ))}
              </select>
            </div>

            {/* Retrain Trigger */}
            <div className="pt-2">
              <button
                onClick={handleRetrain}
                disabled={retraining}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-bold transition-all shadow-md hover:shadow-blue-500/20 active:scale-[0.98] disabled:opacity-50"
              >
                {retraining ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Training Regressors...</>
                ) : (
                  <><Play className="w-3.5 h-3.5 fill-white" /> Trigger Pipeline Retraining</>
                )}
              </button>
            </div>

            {/* DB Tools */}
            <div className="border-t border-border pt-4 space-y-2">
              <p className="text-xs font-semibold text-muted-foreground">Evaluation Database Utilities</p>
              <div className="flex gap-2">
                <button
                  onClick={handleClearData}
                  disabled={clearing}
                  className="flex-1 flex items-center justify-center gap-1 px-3 py-2 border border-red-200 hover:bg-red-50 hover:text-red-700 text-muted-foreground dark:border-red-950 dark:hover:bg-red-950/20 text-xs font-semibold rounded transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" /> Purge Records
                </button>
                <button
                  onClick={handleSeedData}
                  disabled={seeding}
                  className="flex-1 flex items-center justify-center gap-1 px-3 py-2 border border-border hover:bg-muted text-muted-foreground hover:text-foreground text-xs font-semibold rounded transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" /> Reset Seed
                </button>
              </div>
            </div>
          </div>

          {/* Training Logs History Card */}
          <div className="card p-5 flex flex-col h-[320px]">
            <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2 flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-emerald-500" /> Pipeline Retraining History Logs
            </h3>
            <div className="flex-1 overflow-y-auto mt-3 pr-1">
              {retrainHistory.length > 0 ? (
                <div className="border border-border/60 rounded-lg overflow-hidden">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-muted/30 border-b border-border text-muted-foreground font-semibold">
                        <th className="py-2 px-3">Selected Algorithm</th>
                        <th className="py-2 px-3 text-right">Training Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {retrainHistory.map((log) => (
                        <tr key={log.id} className="border-b border-border/40 hover:bg-muted/10">
                          <td className="py-2 px-3 font-medium text-foreground">{log.algorithm_name}</td>
                          <td className="py-2 px-3 text-right text-muted-foreground">
                            {new Date(log.trained_at).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-muted-foreground italic">
                  No retraining records log found in DB.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default ModelInsights;
