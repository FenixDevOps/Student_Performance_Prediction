import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { GraduationCap, Loader2 } from 'lucide-react';

export const Register: React.FC = () => {
  const { register } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('student');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !email || !password) {
      showToast('Please fill in all fields', 'error');
      return;
    }
    if (password.length < 6) {
      showToast('Password must be at least 6 characters', 'error');
      return;
    }
    setLoading(true);
    try {
      await register({ full_name: fullName, email, password, role });
      navigate('/');
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Registration failed. Try a different email.';
      showToast(detail, 'error');
    } finally {
      setLoading(false);
    }
  };

  const inputClass = "w-full px-3 py-2 bg-background border border-border rounded-md text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-colors";

  return (
    <div className="bg-card border border-border rounded-lg shadow-sm p-8 w-full">
      {/* Brand */}
      <div className="flex flex-col items-center mb-7">
        <div className="flex items-center justify-center w-9 h-9 rounded-md bg-blue-600 text-white mb-4">
          <GraduationCap className="w-5 h-5" />
        </div>
        <h1 className="text-xl font-semibold text-foreground">Create an account</h1>
        <p className="text-sm text-muted-foreground mt-1">Get started with PredictGrade</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1">
          <label className="text-sm font-medium text-foreground" htmlFor="fullname">Full name</label>
          <input
            id="fullname"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Sarah Jenkins"
            className={inputClass}
            required
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-foreground" htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@example.com"
            className={inputClass}
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
            placeholder="At least 6 characters"
            className={inputClass}
            required
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-foreground" htmlFor="role">Role</label>
          <select
            id="role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className={inputClass + " cursor-pointer"}
          >
            <option value="student">Student — View reports only</option>
            <option value="teacher">Teacher — Run predictions & exports</option>
            <option value="admin">Administrator — Full control</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-2"
        >
          {loading ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Creating account...</>
          ) : (
            'Create account'
          )}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{' '}
        <Link to="/login" className="text-blue-600 hover:text-blue-700 font-medium hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
};
export default Register;
