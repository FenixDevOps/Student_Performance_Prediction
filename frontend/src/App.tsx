import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './context/ToastContext';

// Layouts
import DashboardLayout from './layouts/DashboardLayout';
import AuthLayout from './layouts/AuthLayout';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Predict from './pages/Predict';
import Results from './pages/Results';
import Analytics from './pages/Analytics';
import ModelInsights from './pages/ModelInsights';
import Profile from './pages/Profile';

// Route Guards
import ProtectedRoute from './components/ProtectedRoute';

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <BrowserRouter>
            <Routes>
              
              {/* ── AUTHENTICATION ROUTES ───────────────────────────────────────── */}
              <Route element={<AuthLayout />}>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
              </Route>

              {/* ── SECURE PORTAL ROUTES ────────────────────────────────────────── */}
              <Route
                element={
                  <ProtectedRoute>
                    <DashboardLayout />
                  </ProtectedRoute>
                }
              >
                {/* Dashboard (Home) */}
                <Route path="/" element={<Dashboard />} />
                
                {/* Predict Student Performance (Teacher / Admin only) */}
                <Route 
                  path="/predict" 
                  element={
                    <ProtectedRoute allowedRoles={['admin', 'teacher']}>
                      <Predict />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Prediction Result Report Card */}
                <Route path="/results" element={<Results />} />
                
                {/* School-wide Analytics (Teacher / Admin only) */}
                <Route 
                  path="/analytics" 
                  element={
                    <ProtectedRoute allowedRoles={['admin', 'teacher']}>
                      <Analytics />
                    </ProtectedRoute>
                  } 
                />
                
                {/* ML Model Insights (Teacher / Admin only) */}
                <Route 
                  path="/model-insights" 
                  element={
                    <ProtectedRoute allowedRoles={['admin', 'teacher']}>
                      <ModelInsights />
                    </ProtectedRoute>
                  } 
                />
                
                {/* User Settings & DB controls */}
                <Route path="/profile" element={<Profile />} />
              </Route>

              {/* Fallback Redirect */}
              <Route path="*" element={<Navigate to="/" replace />} />

            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
