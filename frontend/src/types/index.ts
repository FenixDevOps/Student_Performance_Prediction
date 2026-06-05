export type UserRole = 'admin' | 'teacher' | 'student';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  created_at: string;
  xp_points: number;
  current_streak: number;
}

export interface RoadmapWeek {
  week: number;
  title: string;
  focus: string;
  tasks: string[];
}

export interface PredictionRecord {
  id: number;
  student_name: string;
  attendance: number;
  previous_gpa: number;
  study_hours: number;
  assignment_completion: number;
  participation_score: number;
  sleep_hours: number;
  practice_test_score: number;
  practice_problems: number;
  
  predicted_score: number;
  performance_level: string;
  confidence_score: number;
  risk_level: string;
  
  summary?: string;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  learning_roadmap: RoadmapWeek[];
  
  created_at: string;
  created_by_id?: number;
  student_id?: number;
}

export interface StudentFeatureInput {
  student_name: string;
  attendance: number;
  previous_gpa: number;
  study_hours: number;
  assignment_completion: number;
  participation_score: number;
  sleep_hours: number;
  practice_test_score: number;
  practice_problems: number;
}

export interface ModelResult {
  name: string;
  rmse: number;
  mae: number;
  r2: number;
}

export interface ModelInfo {
  model_name: string;
  rmse: number;
  mae: number;
  r2: number;
  feature_cols: string[];
  feature_importances: Record<string, number>;
  all_results: ModelResult[];
  trained_at: string;
}

export interface HistoryPoint {
  date: string;
  score: number;
  attendance: number;
  study_hours: number;
}

export interface StudentDashboardAnalytics {
  role: 'student';
  total: number;
  avg_score: number;
  max_score: number;
  min_score: number;
  latest_score: number;
  performance_level: string;
  risk_level: string;
  confidence_score: number;
  history: HistoryPoint[];
  current_metrics: {
    attendance: number;
    study_hours: number;
    sleep_hours: number;
    assignment_completion: number;
    practice_test_score: number;
    practice_problems: number;
    previous_gpa: number;
    participation_score: number;
  };
}

export interface ScatterPoint {
  name: string;
  attendance: number;
  study_hours: number;
  previous_gpa: number;
  practice_test_score: number;
  score: number;
  risk: string;
  level: string;
}

export interface RecentHistoryItem {
  id: number;
  name: string;
  score: number;
  level: string;
  risk: string;
  date: string;
}

export interface TeacherDashboardAnalytics {
  role: 'teacher' | 'admin';
  total: number;
  avg_score: number;
  max_score: number;
  min_score: number;
  performance_dist: Record<string, number>;
  risk_dist: Record<string, number>;
  scatter_data: ScatterPoint[];
  recent_history: RecentHistoryItem[];
}

export type DashboardAnalytics = StudentDashboardAnalytics | TeacherDashboardAnalytics;
export type Theme = 'dark' | 'light';
export interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
}
export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}
