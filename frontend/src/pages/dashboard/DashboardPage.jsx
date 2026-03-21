/**
 * Main Dashboard — US-07, US-24.
 * SOC-style dark dashboard with real-time metrics, charts, and live feed.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Shield, Bell, AlertTriangle, Activity,
  TrendingUp, Clock, Zap, Ban, Play, Square,
  ExternalLink
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuthStore } from '../../store/authStore';
import { alertsAPI, captureAPI } from '../../api/alerts';
import { useWebSocket } from '../../hooks/useWebSocket';

function StatCard({ icon: Icon, label, value, color = 'text-soc-accent', trend, onClick }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="soc-card flex items-start gap-4 cursor-pointer hover:soc-glow transition-all"
      onClick={onClick}
    >
      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${color.replace('text-', 'bg-')}/10`}>
        <Icon className={`w-6 h-6 ${color}`} />
      </div>
      <div className="flex-1">
        <p className="text-sm text-soc-muted mb-1">{label}</p>
        <p className="text-2xl font-bold text-white">{value}</p>
        {trend !== undefined && trend !== 0 && (
          <p className={`text-xs mt-1 flex items-center gap-1 ${
            trend > 0 ? 'text-red-400' : 'text-green-400'
          }`}>
            <TrendingUp className="w-3 h-3" />
            {trend > 0 ? '+' : ''}{trend}% from last hour
          </p>
        )}
      </div>
    </motion.div>
  );
}

function RiskGauge({ score }) {
  const getColor = (s) => {
    if (s <= 25) return '#10b981';
    if (s <= 50) return '#f59e0b';
    if (s <= 75) return '#f97316';
    return '#ef4444';
  };

  const rotation = (score / 100) * 180 - 90;
  const color = getColor(score);

  return (
    <div className="soc-card flex flex-col items-center justify-center py-8">
      <p className="text-sm text-soc-muted mb-4">Environment Risk Score</p>
      <div className="relative w-48 h-24 overflow-hidden">
        <div className="absolute bottom-0 left-0 right-0 h-24 border-[12px] border-soc-surface rounded-t-full" />
        <div
          className="absolute bottom-0 left-1/2 w-1 h-20 origin-bottom transition-transform duration-1000"
          style={{
            transform: `translateX(-50%) rotate(${rotation}deg)`,
            background: `linear-gradient(to top, ${color}, transparent)`,
          }}
        />
        <div
          className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-4 h-4 rounded-full"
          style={{ backgroundColor: color }}
        />
      </div>
      <p className="text-4xl font-bold mt-4" style={{ color }}>{score}</p>
      <p className="text-xs text-soc-muted mt-1">/ 100</p>
    </div>
  );
}

function SeverityBar({ label, count, total, color }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-soc-muted w-16">{label}</span>
      <div className="flex-1 h-2 bg-soc-surface rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8 }}
          className={`h-full rounded-full ${color}`}
        />
      </div>
      <span className="text-xs text-soc-text w-10 text-right">{count}</span>
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [liveAlerts, setLiveAlerts] = useState([]);
  const [captureRunning, setCaptureRunning] = useState(false);

  // Throttle toast notifications (max 1 every 3 seconds)
  const lastToastRef = useRef(0);

  // Real-time alerts with toast notifications
  useWebSocket('ws/alerts/', {
    onMessage: (data) => {
      setLiveAlerts((prev) => [data, ...prev].slice(0, 20));

      // Re-fetch stats so counters update in real-time
      fetchStats();

      // Throttled toast notification
      const now = Date.now();
      if (now - lastToastRef.current > 3000) {
        lastToastRef.current = now;
        const severityIcons = {
          critical: '🔴',
          high: '🟠',
          medium: '🟡',
          low: '🔵',
        };
        const icon = severityIcons[data.severity] || '⚪';
        toast(
          `${data.alert_type?.replace('_', ' ').toUpperCase()} detected from ${data.src_ip || 'unknown'}`,
          {
            icon,
            duration: 3000,
            style: {
              background: data.severity === 'critical' ? '#991b1b' : '#1e293b',
              color: '#fff',
              border: data.severity === 'critical' ? '1px solid #ef4444' : '1px solid #334155',
            },
          }
        );
      }
    },
  });

  const fetchStats = useCallback(async () => {
    try {
      const [statsRes, captureRes] = await Promise.allSettled([
        alertsAPI.getStats(),
        captureAPI.getStatus(),
      ]);
      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value.data);
      }
      // Use capture status endpoint as source of truth for button state
      if (captureRes.status === 'fulfilled') {
        setCaptureRunning(captureRes.value.data.is_capturing);
      } else if (statsRes.status === 'fulfilled') {
        setCaptureRunning(statsRes.value.data.capture_running);
      }
    } catch {
      // API may not be available yet
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, [fetchStats]);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleStartCapture = async () => {
    try {
      await captureAPI.start({ duration: 3600 });
      setCaptureRunning(true);
      toast.success('Packet capture started!');
      fetchStats();
    } catch (err) {
      // If already running, just sync the state
      if (err.response?.status === 409) {
        setCaptureRunning(true);
        toast('Capture is already running', { icon: '🟢' });
      } else {
        toast.error(err.response?.data?.error || 'Failed to start capture');
      }
    }
  };

  const handleStopCapture = async () => {
    try {
      await captureAPI.stop();
      setCaptureRunning(false);
      toast.success('Capture stopped');
      fetchStats();
    } catch {
      toast.error('Failed to stop capture');
    }
  };

  const totalAlerts24h = stats?.alerts_24h || 0;
  const severityBreakdown = stats?.severity_breakdown || {};
  const riskScore = Math.min(100, Math.round(
    ((severityBreakdown.critical || 0) * 25 +
     (severityBreakdown.high || 0) * 10 +
     (severityBreakdown.medium || 0) * 3 +
     (severityBreakdown.low || 0)) / Math.max(totalAlerts24h, 1) * 20
  ));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-soc-muted">
            Welcome back, {user?.first_name || user?.username || 'Operator'}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-soc-muted">
            <Clock className="w-4 h-4" />
            {currentTime.toLocaleTimeString()}
          </div>
          {captureRunning ? (
            <button onClick={handleStopCapture} className="soc-btn-danger !py-2 flex items-center gap-2">
              <Square className="w-4 h-4" /> Stop Capture
            </button>
          ) : (
            <button onClick={handleStartCapture} className="soc-btn-primary !py-2 flex items-center gap-2">
              <Play className="w-4 h-4" /> Start Capture
            </button>
          )}
        </div>
      </div>

      {/* Live alert ticker */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-soc-card border border-soc-border rounded-xl p-3 flex items-center gap-3 overflow-hidden"
      >
        <div className="flex items-center gap-2 text-soc-accent shrink-0">
          <div className={`status-dot ${captureRunning ? 'status-dot-active' : 'bg-soc-muted'}`} />
          <span className="text-xs font-semibold uppercase tracking-wider">Live Feed</span>
        </div>
        <div className="text-sm text-soc-muted overflow-hidden whitespace-nowrap">
          {liveAlerts.length > 0 ? (
            <span>
              Latest: <span className="text-white">{liveAlerts[0].alert_type}</span> from{' '}
              <span className="font-mono text-soc-accent">{liveAlerts[0].src_ip}</span>
              {liveAlerts[0].country && ` (${liveAlerts[0].country})`}
            </span>
          ) : captureRunning ? (
            'Monitoring network traffic...'
          ) : (
            'Start packet capture to begin monitoring.'
          )}
        </div>
      </motion.div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link to="/alerts">
          <StatCard
            icon={Bell}
            label="Alerts (24h)"
            value={totalAlerts24h}
            color="text-soc-accent"
          />
        </Link>
        <Link to="/alerts?severity=critical">
          <StatCard
            icon={AlertTriangle}
            label="Critical Alerts"
            value={severityBreakdown.critical || 0}
            color="text-soc-critical"
          />
        </Link>
        <StatCard
          icon={Ban}
          label="Blocked IPs"
          value={stats?.blocked_ips || 0}
          color="text-soc-warning"
        />
        <StatCard
          icon={Zap}
          label="Alerts / Hour"
          value={stats?.alerts_1h || 0}
          color="text-orange-400"
        />
      </div>

      {/* Second row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk gauge */}
        <RiskGauge score={riskScore} />

        {/* Severity breakdown + System status */}
        <div className="soc-card lg:col-span-2 space-y-6">
          <div>
            <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-soc-accent" />
              Severity Breakdown (24h)
            </h3>
            <div className="space-y-3">
              <SeverityBar label="Critical" count={severityBreakdown.critical || 0} total={totalAlerts24h} color="bg-red-500" />
              <SeverityBar label="High" count={severityBreakdown.high || 0} total={totalAlerts24h} color="bg-orange-500" />
              <SeverityBar label="Medium" count={severityBreakdown.medium || 0} total={totalAlerts24h} color="bg-yellow-500" />
              <SeverityBar label="Low" count={severityBreakdown.low || 0} total={totalAlerts24h} color="bg-blue-500" />
            </div>
          </div>

          {/* Top source IPs */}
          {stats?.top_source_ips?.length > 0 && (
            <div>
              <h3 className="text-base font-semibold text-white mb-3">Top Threat Sources</h3>
              <div className="space-y-2">
                {stats.top_source_ips.slice(0, 5).map((ip) => (
                  <div key={ip.src_ip} className="flex items-center justify-between bg-soc-surface rounded-lg px-3 py-2">
                    <span className="text-sm font-mono text-soc-text">{ip.src_ip}</span>
                    <span className="text-sm text-soc-accent font-medium">{ip.count} alerts</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recent live alerts */}
      <div className="soc-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Bell className="w-5 h-5 text-soc-accent" />
            Recent Alerts
          </h3>
          <Link to="/alerts" className="text-sm text-soc-accent hover:underline flex items-center gap-1">
            View all <ExternalLink className="w-3 h-3" />
          </Link>
        </div>

        {liveAlerts.length > 0 ? (
          <div className="space-y-2">
            {liveAlerts.slice(0, 8).map((alert, idx) => (
              <motion.div
                key={alert.id || idx}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="flex items-center gap-4 bg-soc-surface rounded-lg px-4 py-2.5"
              >
                <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                  alert.severity === 'critical' ? 'badge-critical' :
                  alert.severity === 'high' ? 'badge-high' :
                  alert.severity === 'medium' ? 'badge-medium' : 'badge-low'
                }`}>
                  {alert.severity}
                </span>
                <span className="text-sm text-soc-text flex-1">
                  {alert.alert_type?.replace(/_/g, ' ')}
                </span>
                <span className="text-sm font-mono text-soc-muted">{alert.src_ip}</span>
                {alert.country && (
                  <span className="text-xs text-soc-muted">{alert.country}</span>
                )}
                {alert.mitre_technique_id && (
                  <span className="text-xs text-soc-accent bg-soc-accent/10 px-1.5 py-0.5 rounded">
                    {alert.mitre_technique_id}
                  </span>
                )}
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-soc-muted">
            <Shield className="w-16 h-16 mx-auto mb-4 opacity-20" />
            <p className="text-lg font-medium">No alerts yet</p>
            <p className="text-sm mt-1">Start a packet capture session to begin monitoring.</p>
          </div>
        )}
      </div>
    </div>
  );
}
