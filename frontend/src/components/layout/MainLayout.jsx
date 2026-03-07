/**
 * Main layout — sidebar + top bar + content area.
 * SOC dark theme with navigation.
 */
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, LayoutDashboard, Bell, AlertTriangle,
  FileText, Settings, Users, CreditCard,
  Activity, Brain, Globe, Crosshair,
  MessageSquare, LogOut, Menu, X, ChevronDown,
  Network, BookOpen, Zap, UserCog, ClipboardList, Play
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { authAPI } from '../../api/auth';
import toast from 'react-hot-toast';

const navItems = [
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Alerts', path: '/alerts', icon: Bell },
  { label: 'GeoIP Map', path: '/alerts/map', icon: Globe },
  { label: 'Threats', path: '/threats', icon: AlertTriangle },
  { label: 'Incidents', path: '/incidents', icon: Crosshair },
  { label: 'ML Config', path: '/ml-config', icon: Brain },
  { label: 'System', path: '/system', icon: Activity },
  { label: 'Reports', path: '/reports', icon: FileText },
  { label: 'DurianBot', path: '/chatbot', icon: MessageSquare },
  { label: 'Team', path: '/team', icon: Users },
  { label: 'Subscription', path: '/subscription', icon: CreditCard },
];

const wowItems = [
  { label: '3D Globe', path: '/globe', icon: Globe },
  { label: 'Attack Chains', path: '/attack-chains', icon: Zap },
  { label: 'MITRE ATT&CK', path: '/mitre', icon: BookOpen },
  { label: 'Packet Inspector', path: '/packets', icon: Network },
  { label: 'Demo Mode', path: '/demo', icon: Play },
];

const adminItems = [
  { label: 'User Management', path: '/admin/users', icon: UserCog },
  { label: 'Audit Logs', path: '/admin/audit', icon: ClipboardList },
  { label: 'System Health', path: '/admin/health', icon: Activity },
];

export default function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showWow, setShowWow] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const { user, tokens, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await authAPI.logout(tokens?.refresh);
    } catch {
      // Ignore errors
    }
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
  };

  const isAdmin = user?.role === 'admin';

  return (
    <div className="min-h-screen bg-soc-bg flex">
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            initial={{ x: -280 }}
            animate={{ x: 0 }}
            exit={{ x: -280 }}
            transition={{ type: 'spring', damping: 25 }}
            className="w-[260px] bg-soc-card border-r border-soc-border flex flex-col fixed h-full z-30"
          >
            {/* Logo */}
            <div className="p-5 border-b border-soc-border flex items-center gap-3">
              <Shield className="w-8 h-8 text-soc-accent" />
              <span className="text-lg font-bold text-white">
                Durian<span className="text-soc-accent">Detector</span>
              </span>
            </div>

            {/* Nav */}
            <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 ${
                      isActive
                        ? 'bg-soc-accent/10 text-soc-accent border border-soc-accent/20'
                        : 'text-soc-muted hover:bg-soc-surface hover:text-soc-text'
                    }`
                  }
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </NavLink>
              ))}

              {/* Wow Features Section */}
              <button
                onClick={() => setShowWow(!showWow)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-soc-muted hover:bg-soc-surface w-full mt-4"
              >
                <Zap className="w-4 h-4 text-yellow-400" />
                <span className="flex-1 text-left">Advanced</span>
                <ChevronDown className={`w-4 h-4 transition-transform ${showWow ? 'rotate-180' : ''}`} />
              </button>
              <AnimatePresence>
                {showWow && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden pl-2 space-y-1"
                  >
                    {wowItems.map((item) => (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                          `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150 ${
                            isActive
                              ? 'bg-soc-accent/10 text-soc-accent border border-soc-accent/20'
                              : 'text-soc-muted hover:bg-soc-surface hover:text-soc-text'
                          }`
                        }
                      >
                        <item.icon className="w-4 h-4" />
                        {item.label}
                      </NavLink>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Admin Section */}
              {isAdmin && (
                <>
                  <button
                    onClick={() => setShowAdmin(!showAdmin)}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-soc-muted hover:bg-soc-surface w-full mt-4"
                  >
                    <UserCog className="w-4 h-4 text-red-400" />
                    <span className="flex-1 text-left">Admin</span>
                    <ChevronDown className={`w-4 h-4 transition-transform ${showAdmin ? 'rotate-180' : ''}`} />
                  </button>
                  <AnimatePresence>
                    {showAdmin && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden pl-2 space-y-1"
                      >
                        {adminItems.map((item) => (
                          <NavLink
                            key={item.path}
                            to={item.path}
                            className={({ isActive }) =>
                              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150 ${
                                isActive
                                  ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                                  : 'text-soc-muted hover:bg-soc-surface hover:text-soc-text'
                              }`
                            }
                          >
                            <item.icon className="w-4 h-4" />
                            {item.label}
                          </NavLink>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </>
              )}
            </nav>

            {/* User section */}
            <div className="p-4 border-t border-soc-border">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-soc-accent/20 flex items-center justify-center">
                  <span className="text-soc-accent font-semibold text-sm">
                    {user?.first_name?.[0] || user?.email?.[0] || 'U'}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">
                    {user?.first_name || user?.username || 'User'}
                  </p>
                  <p className="text-xs text-soc-muted truncate">{user?.role}</p>
                </div>
                <button onClick={handleLogout} className="text-soc-muted hover:text-soc-danger transition-colors">
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main content */}
      <div className={`flex-1 transition-all duration-300 ${sidebarOpen ? 'ml-[260px]' : 'ml-0'}`}>
        {/* Top bar */}
        <header className="h-14 bg-soc-card border-b border-soc-border flex items-center px-4 sticky top-0 z-20">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-soc-muted hover:text-white transition-colors mr-4"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          {/* Live status indicator */}
          <div className="flex items-center gap-2 ml-auto">
            <div className="status-dot status-dot-active" />
            <span className="text-xs text-soc-muted">System Online</span>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
