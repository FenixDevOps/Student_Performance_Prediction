import React, { useEffect, useState } from 'react';
import { modelService } from '../services/api';
import { useToast } from '../hooks/useToast';
import { ModelInfo } from '../types';
import { Cpu, CheckCircle, Calendar, Activity } from 'lucide-react';
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
  const { showToast } = useToast();
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const data = await modelService.getInfo();
        setModelInfo(data);
      } catch {
        showToast('Failed to load ML model details.', 'error');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

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
            <p><strong>RMSE</strong> — Root mean squared error. Penalizes large errors. Lower is better.</p>
            <p><strong>MAE</strong> — Mean absolute error. Average magnitude of errors. Lower is better.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
export default ModelInsights;
