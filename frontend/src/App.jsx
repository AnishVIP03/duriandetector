import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';

// Layout
import MainLayout from './components/layout/MainLayout';
import AuthLayout from './components/layout/AuthLayout';

// Tier gating
import TierGate from './components/common/TierGate';

// Pages — Auth & Setup
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import CreateEnvironmentPage from './pages/environments/CreateEnvironmentPage';
import JoinEnvironmentPage from './pages/environments/JoinEnvironmentPage';

// Pages — Core (Phase 1 + 2)
import DashboardPage from './pages/dashboard/DashboardPage';
import AlertListPage from './pages/alerts/AlertListPage';
import AlertDetailPage from './pages/alerts/AlertDetailPage';
import GeoIPMapPage from './pages/alerts/GeoIPMapPage';
import ThreatsPage from './pages/threats/ThreatsPage';

// Pages — Phase 3 (Premium Features)
import IncidentListPage from './pages/incidents/IncidentListPage';
import MLConfigPage from './pages/ml/MLConfigPage';
import ReportsPage from './pages/reports/ReportsPage';
import SystemStatusPage from './pages/dashboard/SystemStatusPage';

// Pages — MITRE & Globe
import MitreHeatmapPage from './pages/mitre/MitreHeatmapPage';
import GlobePage from './pages/globe/GlobePage';

// Pages — Phase 4 (Team, Subscription, Admin)
import TeamPage from './pages/team/TeamPage';
import SubscriptionPage from './pages/subscription/SubscriptionPage';
import AdminUsersPage from './pages/admin/AdminUsersPage';
import AdminAuditPage from './pages/admin/AdminAuditPage';
import AdminHealthPage from './pages/admin/AdminHealthPage';

// Pages — AI Chatbot
import ChatbotPage from './pages/chatbot/ChatbotPage';

// Pages — Phase 5 (Wow Features)
import AttackChainPage from './pages/attacks/AttackChainPage';
import PacketInspectorPage from './pages/packets/PacketInspectorPage';
import DemoPage from './pages/demo/DemoPage';

// Pages — Phase 6 (Feedback Features)
import BlockedIPsPage from './pages/alerts/BlockedIPsPage';
import WhitelistPage from './pages/alerts/WhitelistPage';
import TrafficFilterPage from './pages/alerts/TrafficFilterPage';
import LogIngestionPage from './pages/alerts/LogIngestionPage';
import CustomVisualizationPage from './pages/analytics/CustomVisualizationPage';
import AdminTeamsPage from './pages/admin/AdminTeamsPage';

/**
 * Protected route wrapper.
 * Redirects to login if user is not authenticated.
 */
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

/**
 * Guest route wrapper.
 * Redirects to dashboard if user is already authenticated.
 */
function GuestRoute({ children }) {
  const { isAuthenticated } = useAuthStore();
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/"
        element={
          <GuestRoute>
            <LandingPage />
          </GuestRoute>
        }
      />

      {/* Auth routes */}
      <Route element={<AuthLayout />}>
        <Route
          path="/login"
          element={
            <GuestRoute>
              <LoginPage />
            </GuestRoute>
          }
        />
        <Route
          path="/register"
          element={
            <GuestRoute>
              <RegisterPage />
            </GuestRoute>
          }
        />
        <Route
          path="/forgot-password"
          element={
            <GuestRoute>
              <ForgotPasswordPage />
            </GuestRoute>
          }
        />
      </Route>

      {/* Environment setup (authenticated but no layout) */}
      <Route
        path="/setup/create"
        element={
          <ProtectedRoute>
            <CreateEnvironmentPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/setup/join"
        element={
          <ProtectedRoute>
            <JoinEnvironmentPage />
          </ProtectedRoute>
        }
      />

      {/* Protected routes with main layout */}
      <Route
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        {/* Free tier — accessible to all users */}
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/alerts" element={<AlertListPage />} />
        <Route path="/alerts/:id" element={<AlertDetailPage />} />
        <Route path="/alerts/map" element={<GeoIPMapPage />} />
        <Route path="/threats" element={<ThreatsPage />} />
        <Route path="/chatbot" element={<ChatbotPage />} />
        <Route path="/subscription" element={<SubscriptionPage />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="/blocked-ips" element={<BlockedIPsPage />} />
        <Route path="/whitelist" element={<WhitelistPage />} />
        <Route path="/traffic-filters" element={<TrafficFilterPage />} />
        <Route path="/log-ingestion" element={<LogIngestionPage />} />
        <Route path="/analytics" element={<CustomVisualizationPage />} />

        {/* Premium tier — requires premium subscription or above */}
        <Route path="/incidents" element={<TierGate requiredTier="premium" featureName="Incident Management"><IncidentListPage /></TierGate>} />
        <Route path="/ml-config" element={<TierGate requiredTier="premium" featureName="ML Configuration"><MLConfigPage /></TierGate>} />
        <Route path="/reports" element={<TierGate requiredTier="premium" featureName="Reports"><ReportsPage /></TierGate>} />
        <Route path="/system" element={<TierGate requiredTier="premium" featureName="System Status"><SystemStatusPage /></TierGate>} />
        <Route path="/mitre" element={<TierGate requiredTier="premium" featureName="MITRE ATT&CK"><MitreHeatmapPage /></TierGate>} />
        <Route path="/packets" element={<TierGate requiredTier="premium" featureName="Packet Inspector"><PacketInspectorPage /></TierGate>} />

        {/* Exclusive tier — requires exclusive subscription or above */}
        <Route path="/globe" element={<TierGate requiredTier="exclusive" featureName="3D Globe"><GlobePage /></TierGate>} />
        <Route path="/attack-chains" element={<TierGate requiredTier="exclusive" featureName="Attack Chains"><AttackChainPage /></TierGate>} />
        <Route path="/team" element={<TierGate requiredTier="exclusive" featureName="Team Management"><TeamPage /></TierGate>} />

        {/* Admin only */}
        <Route path="/admin/users" element={<AdminUsersPage />} />
        <Route path="/admin/audit" element={<AdminAuditPage />} />
        <Route path="/admin/health" element={<AdminHealthPage />} />
        <Route path="/admin/teams" element={<AdminTeamsPage />} />
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
