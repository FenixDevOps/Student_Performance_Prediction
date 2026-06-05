import React, { useState } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { GraduationCap, Loader2 } from 'lucide-react';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  React.useEffect(() => {
    if (searchParams.get('expired') === 'true') {
      showToast('Your session has expired. Please log in again.', 'info');
    }
  }, [searchParams, showToast]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      showToast('Please fill in all fields', 'error');
      return;
    }
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Invalid email or password';
      showToast(detail, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-card border border-border rounded-lg shadow-sm p-8 w-full">
      {/* Brand */}
      <div className="flex flex-col items-center mb-8">
        <div className="flex items-center justify-center w-9 h-9 rounded-md bg-blue-600 text-white mb-4">
          <GraduationCap className="w-5 h-5" />
        </div>
        <h1 className="text-xl font-semibold text-foreground">Sign in to PredictGrade</h1>
        <p className="text-sm text-muted-foreground mt-1">Student Performance Prediction Portal</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1">
          <label className="text-sm font-medium text-foreground" htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@example.com"
            className="w-full px-3 py-2 bg-background border border-border rounded-md text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-colors"
            required
            autoComplete="email"
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-foreground" htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            className="w-full px-3 py-2 bg-background border border-border rounded-md text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-colors"
            required
            autoComplete="current-password"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-2"
        >
          {loading ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Signing in...</>
          ) : (
            'Sign in'
          )}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Don't have an account?{' '}
        <Link to="/register" className="text-blue-600 hover:text-blue-700 font-medium hover:underline">
          Create one
        </Link>
      </p>

      {/* Demo credentials */}
      <div className="mt-6 p-3 bg-muted rounded-md border border-border">
        <p className="text-xs font-medium text-muted-foreground mb-1.5">Demo credentials</p>
        <div className="space-y-1 text-xs text-muted-foreground font-mono">
          <div>admin@example.com / admin123</div>
          <div>teacher@example.com / teacher123</div>
          <div>student@example.com / student123</div>
        </div>
      </div>
    </div>
  );
};
export default Login;
