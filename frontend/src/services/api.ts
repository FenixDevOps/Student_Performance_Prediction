import axios from 'axios';

// Helper to sanitize and format backend API URL
const getApiBaseUrl = () => {
  const envVal = import.meta.env.VITE_API_URL;
  if (!envVal) return '/api';
  const cleanVal = envVal.replace(/\/$/, '');
  return cleanVal.endsWith('/api') ? cleanVal : `${cleanVal}/api`;
};

// Create Axios Instance
const api = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach JWT Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Catch Token Expiry (401)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // Redirect only if not on auth page to avoid redirect loops
      if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
        window.location.href = '/login?expired=true';
      }
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const authService = {
  login: async (username: string, password: string) => {
    // OAuth2 expects form-urlencoded payload
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    
    const res = await api.post('/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return res.data;
  },
  register: async (payload: any) => {
    const res = await api.post('/auth/register', payload);
    return res.data;
  },
  getMe: async () => {
    const res = await api.get('/auth/me');
    return res.data;
  },
  updateProfile: async (payload: any) => {
    const res = await api.put('/auth/profile', null, { params: payload });
    return res.data;
  }
};

// Prediction & Analytics endpoints
export const predictionService = {
  predict: async (features: any) => {
    const res = await api.post('/predict/predict', features);
    return res.data;
  },
  getHistory: async (params?: { query?: string; level?: string; sort?: string }) => {
    const res = await api.get('/predict/history', { params });
    return res.data;
  },
  getRecord: async (id: number) => {
    const res = await api.get(`/predict/record/${id}`);
    return res.data;
  },
  deleteRecord: async (id: number) => {
    const res = await api.delete(`/predict/record/${id}`);
    return res.data;
  },
  exportPdfUrl: (id: number) => {
    const token = localStorage.getItem('token');
    return `${getApiBaseUrl()}/predict/export/pdf/${id}?token=${token}`;
  },
  downloadPdf: async (id: number, studentName: string) => {
    const res = await api.get(`/predict/export/pdf/${id}`, { responseType: 'blob' });
    const blob = new Blob([res.data], { type: 'application/pdf' });
    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.download = `report_${studentName.replace(/\s+/g, '_')}_${id}.pdf`;
    link.click();
  },
  downloadExcel: async () => {
    const res = await api.get('/predict/export/excel', { responseType: 'blob' });
    const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.download = `predictions_export_${new Date().toISOString().slice(0,10)}.xlsx`;
    link.click();
  },
  getRoadmapTasks: async () => {
    const res = await api.get('/predict/roadmap/tasks');
    return res.data;
  },
  toggleRoadmapTask: async (payload: { prediction_id: number; week: number; task_index: number; completed: boolean }) => {
    const res = await api.put('/predict/roadmap/tasks', payload);
    return res.data;
  },
  chat: async (payload: { prediction_id: number; message: string }) => {
    const res = await api.post('/predict/chat', payload);
    return res.data;
  },
  uploadBulkCsv: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/predict/bulk', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  }
};

// Analytics API
export const analyticsService = {
  getAnalytics: async () => {
    const res = await api.get('/analytics');
    return res.data;
  }
};

// Alerts API
export const alertsService = {
  getAlerts: async () => {
    const res = await api.get('/alerts');
    return res.data;
  },
  resolveAlert: async (id: number) => {
    const res = await api.post(`/alerts/${id}/resolve`);
    return res.data;
  },
  sendParentEmail: async (payload: { record_id: number; parent_email: string }) => {
    const res = await api.post('/alerts/email', payload);
    return res.data;
  }
};

// Model Operations
export const modelService = {
  getInfo: async () => {
    const res = await api.get('/model/info');
    return res.data;
  },
  retrain: async () => {
    const res = await api.post('/model/retrain');
    return res.data;
  },
  clearData: async () => {
    const res = await api.post('/model/clear-data');
    return res.data;
  },
  seedData: async () => {
    const res = await api.post('/model/seed-data');
    return res.data;
  },
  getRetrainHistory: async () => {
    const res = await api.get('/model/history');
    return res.data;
  },
  changeActiveAlgorithm: async (active_algorithm: string) => {
    const res = await api.post('/model/active', { active_algorithm });
    return res.data;
  }
};

export default api;
