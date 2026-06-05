import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { authService, modelService } from '../services/api';
import { Loader2, Database, Trash2, PlusCircle, Shield, Mail } from 'lucide-react';

export const Profile: React.FC = () => {
  const { user, updateUser } = useAuth();
  const { showToast } = useToast();

  const [name, setName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [dbLoading, setDbLoading] = useState(false);
  const [showSeedConfirm, setShowSeedConfirm] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  if (!user) return null;

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email) { showToast('Name and email cannot be blank.', 'error'); return; }
    setLoading(true);
    try {
      const updatedUser = await authService.updateProfile({ name, email, password: password || undefined });
      updateUser(updatedUser);
      setPassword('');
      showToast('Profile updated.', 'success');
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to update profile.', 'error');
    } finally { setLoading(false); }
  };

  const handleClearDb = async () => {
    if (!showClearConfirm) { setShowClearConfirm(true); setTimeout(() => setShowClearConfirm(false), 4000); return; }
    setShowClearConfirm(false);
    setDbLoading(true);
    try {
      const res = await modelService.clearData();
      showToast(res.message || 'Database cleared.', 'success');
    } catch { showToast('Failed to clear database.', 'error'); }
    finally { setDbLoading(false); }
  };

  const handleSeedDb = async () => {
    if (!showSeedConfirm) { setShowSeedConfirm(true); setTimeout(() => setShowSeedConfirm(false), 4000); return; }
    setShowSeedConfirm(false);
    setDbLoading(true);
    try {
      const res = await modelService.seedData();
      showToast(res.message || 'Database seeded.', 'success');
    } catch { showToast('Failed to seed database.', 'error'); }
    finally { setDbLoading(false); }
  };

  const inputClass = "w-full px-3 py-2 bg-background border border-border rounded-md text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition-colors";

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      {/* Profile Header */}
      <div className="card p-5 flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-800 text-foreground flex items-center justify-center font-semibold text-lg uppercase">
          {user.full_name.charAt(0)}
        </div>
        <div>
          <h2 className="text-base font-semibold text-foreground">{user.full_name}</h2>
          <div className="flex items-center gap-2 mt-1">
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Mail className="w-3.5 h-3.5" />{user.email}
            </span>
            <span className="text-muted-foreground/40">·</span>
            <span className="flex items-center gap-1 text-xs text-blue-600 font-medium bg-blue-50 dark:bg-blue-950/30 px-2 py-0.5 rounded">
              <Shield className="w-3 h-3" />{user.role}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Account Settings Form */}
        <div className="card p-5 md:col-span-2 space-y-4">
          <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">Account settings</h3>

          <form onSubmit={handleUpdateProfile} className="space-y-4">
            <div className="space-y-1">
              <label className="text-sm font-medium text-foreground">Full name</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} className={inputClass} required />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-foreground">Email address</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputClass} required />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-foreground">New password <span className="text-muted-foreground font-normal">(leave blank to keep current)</span></label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters" className={inputClass} />
            </div>
            <div className="flex justify-end pt-1">
              <button type="submit" disabled={loading}
                className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md text-sm transition-colors disabled:opacity-50">
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                Save changes
              </button>
            </div>
          </form>
        </div>

        {/* Side Panel */}
        <div className="space-y-4">
          {user.role === 'admin' ? (
            <div className="card p-5 space-y-4">
              <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2 flex items-center gap-1.5">
                <Database className="w-4 h-4" /> Admin DB Tools
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Manage prediction database. Useful for resetting demos or clearing test data.
              </p>
              <div className="space-y-2">
                <button onClick={handleSeedDb} disabled={dbLoading}
                  className={`w-full py-2 border font-medium rounded-md text-sm flex items-center justify-center gap-1.5 transition-colors ${
                    showSeedConfirm
                      ? 'border-amber-400 bg-amber-50 text-amber-700 dark:bg-amber-950/20 dark:text-amber-400'
                      : 'border-emerald-300 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/20 dark:hover:bg-emerald-950/40 dark:text-emerald-400'
                  }`}>
                  <PlusCircle className="w-4 h-4" />
                  {showSeedConfirm ? 'Click again to confirm' : 'Seed Sample Data'}
                </button>
                <button onClick={handleClearDb} disabled={dbLoading}
                  className={`w-full py-2 border font-medium rounded-md text-sm flex items-center justify-center gap-1.5 transition-colors ${
                    showClearConfirm
                      ? 'border-red-400 bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400'
                      : 'border-red-200 bg-red-50 hover:bg-red-100 text-red-600 dark:border-red-900 dark:bg-red-950/20 dark:hover:bg-red-950/40 dark:text-red-400'
                  }`}>
                  <Trash2 className="w-4 h-4" />
                  {showClearConfirm ? 'Click again to confirm' : 'Wipe Predictions DB'}
                </button>
              </div>
            </div>
          ) : (
            <div className="card p-5 space-y-2">
              <h3 className="text-sm font-semibold text-foreground">About your role</h3>
              <div className="space-y-2 text-sm text-muted-foreground">
                <p>Your current role is <strong className="text-foreground">{user.role}</strong>.</p>
                {user.role === 'student' && (
                  <p>To run predictions and view analytics, register a new account with the <em>Teacher</em> role.</p>
                )}
                <p>Administrators have full access including database management and ML model controls.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
export default Profile;
