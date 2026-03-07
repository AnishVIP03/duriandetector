/**
 * System Status page — US-21, US-35.
 * Monitors system health, services, and capture sessions.
 */
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Activity, Server, Cpu, HardDrive, MemoryStick,
  Wifi, RefreshCw, CheckCircle, XCircle, AlertCircle
} from 'lucide-react';
import { systemAPI } from '../../api/incidents';

const SERVICE_ICONS = {
  database: Server,
  redis: Server,
  celery: Activity,
  capture: Wifi,
};

function ServiceCard({ name, status, type, sessions }) {
  const Icon = SERVICE_ICONS[name] || Server;
  const isOnline = status === 'online' || status === 'active';

  return (
    <div className="bg-soc-surface rounded-lg p-4 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
        isOnline ? 'bg-green-500/10' : 'bg-red-500/10'
      }`}>
        <Icon className={`w-5 h-5 ${isOnline ? 'text-green-400' : 'text-red-400'}`} />
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium text-white capitalize">{name}</p>
        <p className="text-xs text-soc-muted">{type}</p>
      </div>
      <div className="flex items-center gap-2">
        {isOnline ? (
          <CheckCircle className="w-5 h-5 text-green-400" />
        ) : (
          <XCircle className="w-5 h-5 text-red-400" />
        )}
        <span className={`text-xs font-medium ${isOnline ? 'text-green-400' : 'text-red-400'}`}>
          {status}
        </span>
      </div>
    </div>
  );
}

function MetricGauge({ label, value, icon: Icon, unit = '%', maxLabel = '100%' }) {
  const pct = Math.min(value, 100);
  const color = pct > 90 ? 'text-red-400' : pct > 70 ? 'text-yellow-400' : 'text-green-400';
  const barColor = pct > 90 ? 'bg-red-500' : pct > 70 ? 'bg-yellow-500' : 'bg-green-500';

  return (
    <div className="bg-soc-surface rounded-lg p-4">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4 text-soc-muted" />
        <span className="text-sm text-soc-muted">{label}</span>
      </div>
      <p className={`text-2xl font-bold ${color} mb-2`}>{value?.toFixed(1)}{unit}</p>
      <div className="w-full h-2 bg-soc-bg rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8 }}
          className={`h-full rounded-full ${barColor}`}
        />
      </div>
    </div>
  );
}

export default function SystemStatusPage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const { data } = await systemAPI.getHealth();
      setHealth(data);
    } catch {
      // API may not be available
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !health) {
    return <div className="text-center py-20 text-soc-muted">Loading system status...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-soc-accent" /> System Status
          </h1>
          <p className="text-sm text-soc-muted mt-1">Monitor system health and service status</p>
        </div>
        <button onClick={fetchHealth} className="soc-btn-ghost !py-2 !px-3">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Services */}
      <div className="soc-card">
        <h3 className="text-base font-semibold text-white mb-4">Services</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {health?.services && Object.entries(health.services).map(([name, svc]) => (
            <ServiceCard key={name} name={name} {...svc} />
          ))}
        </div>
      </div>

      {/* System Metrics */}
      <div className="soc-card">
        <h3 className="text-base font-semibold text-white mb-4">System Resources</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <MetricGauge
            label="CPU Usage"
            value={health?.system?.cpu_percent || 0}
            icon={Cpu}
          />
          <MetricGauge
            label="Memory Usage"
            value={health?.system?.memory_percent || 0}
            icon={MemoryStick}
          />
          <MetricGauge
            label="Disk Usage"
            value={health?.system?.disk_percent || 0}
            icon={HardDrive}
          />
        </div>
        {health?.system && (
          <div className="grid grid-cols-3 gap-4 mt-4">
            <div className="bg-soc-bg rounded-lg p-3 text-center">
              <p className="text-xs text-soc-muted">Memory</p>
              <p className="text-sm text-white">{health.system.memory_used_gb} / {health.system.memory_total_gb} GB</p>
            </div>
            <div className="bg-soc-bg rounded-lg p-3 text-center">
              <p className="text-xs text-soc-muted">Disk</p>
              <p className="text-sm text-white">{health.system.disk_used_gb} / {health.system.disk_total_gb} GB</p>
            </div>
            <div className="bg-soc-bg rounded-lg p-3 text-center">
              <p className="text-xs text-soc-muted">Alerts / Hour</p>
              <p className="text-sm text-white">{health.alerts_last_hour}</p>
            </div>
          </div>
        )}
      </div>

      {/* Health History */}
      {health?.history?.length > 1 && (
        <div className="soc-card">
          <h3 className="text-base font-semibold text-white mb-4">Health History</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-soc-border">
                  <th className="text-left px-3 py-2 text-xs text-soc-muted">Time</th>
                  <th className="text-left px-3 py-2 text-xs text-soc-muted">CPU</th>
                  <th className="text-left px-3 py-2 text-xs text-soc-muted">Memory</th>
                  <th className="text-left px-3 py-2 text-xs text-soc-muted">Disk</th>
                  <th className="text-left px-3 py-2 text-xs text-soc-muted">Alerts/hr</th>
                  <th className="text-left px-3 py-2 text-xs text-soc-muted">Captures</th>
                </tr>
              </thead>
              <tbody>
                {health.history.slice(0, 10).map((h) => (
                  <tr key={h.id} className="border-b border-soc-border/50">
                    <td className="px-3 py-2 text-soc-muted">{new Date(h.checked_at).toLocaleTimeString()}</td>
                    <td className="px-3 py-2 text-soc-text">{h.cpu_percent?.toFixed(1)}%</td>
                    <td className="px-3 py-2 text-soc-text">{h.memory_percent?.toFixed(1)}%</td>
                    <td className="px-3 py-2 text-soc-text">{h.disk_usage_percent?.toFixed(1)}%</td>
                    <td className="px-3 py-2 text-soc-text">{h.alerts_last_hour}</td>
                    <td className="px-3 py-2 text-soc-text">{h.capture_sessions_active}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
