import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../hooks/useTheme';
import { alertsService } from '../services/api';
import {
  LayoutDashboard,
  UserCheck,
  BarChart3,
  BrainCircuit,
  User,
  LogOut,
  Sun,
  Moon,
  Menu,
  X,
  GraduationCap,
  Bell,
} from 'lucide-react';

interface SidebarItem {
  name: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  roles: string[];
}

const sidebarItems: SidebarItem[] = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard, roles: ['admin', 'teacher', 'student'] },
  { name: 'Predict Performance', path: '/predict', icon: UserCheck, roles: ['admin', 'teacher'] },
  { name: 'Analytics', path: '/analytics', icon: BarChart3, roles: ['admin', 'teacher'] },
  { name: 'Model Insights', path: '/model-insights', icon: BrainCircuit, roles: ['admin', 'teacher'] },
  { name: 'Profile', path: '/profile', icon: User, roles: ['admin', 'teacher', 'student'] },
];

export const DashboardLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [alertsDropdownOpen, setAlertsDropdownOpen] = useState(false);

  useEffect(() => {
    let interval: any;
    if (user && (user.role === 'teacher' || user.role === 'admin')) {
      const fetchAlerts = async () => {
        try {
          const data = await alertsService.getAlerts();
          setAlerts(data);
        } catch (err) {
          console.error('Failed to fetch alerts in layout:', err);
        }
      };
      fetchAlerts();
      interval = setInterval(fetchAlerts, 15000); // refresh every 15s
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [user]);

  if (!user) return null;

  const allowedItems = sidebarItems.filter(item => item.roles.includes(user.role));
  const currentItem = allowedItems.find(item => item.path === location.pathname);
  const pageTitle = currentItem ? currentItem.name : 'Portal';

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 py-4 border-b border-border">
        <div className="flex items-center justify-center w-8 h-8 rounded-md bg-blue-600 text-white">
          <GraduationCap className="w-4 h-4" />
        </div>
        <span className="text-sm font-semibold text-foreground tracking-tight">PredictGrade</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {allowedItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              to={item.path}
              onClick={() => setMobileSidebarOpen(false)}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              }`}
            >
              <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-blue-600 dark:text-blue-400' : ''}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* User Footer */}
      <div className="p-3 border-t border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-7 h-7 rounded-full bg-gray-200 dark:bg-gray-700 text-foreground flex items-center justify-center font-semibold text-xs uppercase flex-shrink-0">
              {user.full_name.charAt(0)}
            </div>
            <div className="flex flex-col min-w-0">
              <span className="text-xs font-medium text-foreground truncate">{user.full_name}</span>
              <span className="text-[10px] text-muted-foreground capitalize">{user.role}</span>
            </div>
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-md text-muted-foreground hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
            title="Sign Out"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">

      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-56 h-full bg-card border-r border-border flex-shrink-0">
        <SidebarContent />
      </aside>

      {/* Mobile Sidebar Overlay */}
      {mobileSidebarOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/40 z-30 md:hidden"
            onClick={() => setMobileSidebarOpen(false)}
          />
          <aside className="fixed top-0 bottom-0 left-0 w-56 bg-card border-r border-border z-40 flex flex-col md:hidden">
            <SidebarContent />
          </aside>
        </>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

        {/* Top Header */}
        <header className="h-14 border-b border-border bg-card flex items-center justify-between px-4 flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileSidebarOpen(true)}
              className="p-1.5 rounded-md hover:bg-muted text-muted-foreground md:hidden"
            >
              <Menu className="w-4 h-4" />
            </button>
            <h1 className="text-sm font-semibold text-foreground">{pageTitle}</h1>
          </div>

          <div className="flex items-center gap-2">
            {user && (user.role === 'teacher' || user.role === 'admin') && (
              <div className="relative">
                <button
                  onClick={() => setAlertsDropdownOpen(!alertsDropdownOpen)}
                  className="p-1.5 rounded-md border border-border hover:bg-muted text-muted-foreground transition-colors relative"
                  title="Risk Alerts"
                >
                  <Bell className="w-4 h-4" />
                  {alerts.length > 0 && (
                    <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-600 text-[9px] font-bold text-white">
                      {alerts.length}
                    </span>
                  )}
                </button>
                {alertsDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-72 bg-card border border-border rounded-lg shadow-xl py-2 z-50 text-xs text-foreground animate-in fade-in slide-in-from-top-2">
                    <div className="px-3 py-1.5 border-b border-border font-semibold text-muted-foreground flex items-center justify-between">
                      <span>Active Risk Alerts</span>
                      <span className="text-[10px] bg-red-100 text-red-800 px-1.5 py-0.5 rounded-full dark:bg-red-950/40 dark:text-red-400">
                        {alerts.length} New
                      </span>
                    </div>
                    <div className="max-h-60 overflow-y-auto">
                      {alerts.length > 0 ? (
                        alerts.map(alert => (
                          <div key={alert.id} className="px-3 py-2 border-b border-border/50 hover:bg-muted/50 transition-colors">
                            <p className="font-semibold text-foreground">{alert.student_name}</p>
                            <p className="text-muted-foreground text-[10px] mt-0.5">
                              Score: {alert.predicted_score.toFixed(1)}% | Attendance: {alert.attendance}%
                            </p>
                          </div>
                        ))
                      ) : (
                        <div className="px-3 py-6 text-center text-muted-foreground">
                          No active risk alerts.
                        </div>
                      )}
                    </div>
                    <div className="px-3 pt-2 text-center border-t border-border">
                      <Link
                        to="/"
                        onClick={() => setAlertsDropdownOpen(false)}
                        className="text-blue-600 dark:text-blue-400 font-semibold hover:underline"
                      >
                        View in Dashboard
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            )}

            <button
              onClick={toggleTheme}
              className="p-1.5 rounded-md border border-border hover:bg-muted text-muted-foreground transition-colors"
              title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
            >
              {theme === 'dark'
                ? <Sun className="w-4 h-4 text-amber-500" />
                : <Moon className="w-4 h-4" />
              }
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
export default DashboardLayout;
