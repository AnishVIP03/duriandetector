/**
 * Admin System Health page.
 * Extended health monitoring with service status, resource gauges, and health history.
 */
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Activity, Server, Cpu, HardDrive, MemoryStick,
  Wifi, RefreshCw, CheckCircle, XCircle, Shield
} from 'lucide-react';
import { systemAPI } from '../../api/incidents';

const SERVICE_ICONS = {
  database: Server,
  redis: Server,
  celery: Activity,
  capture: Wifi,
};

function ServiceCard({ name, status, type }) {
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

function MetricGauge({ label, value, icon: Icon, unit = '%' }) {
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

function getOverallStatus(services) {
  if (!services) return { label: 'Unknown', color: 'text-soc-muted', bg: 'bg-soc-surface' };
  const statuses = Object.values(services).map((s) => s.status);
  const allOnline = statuses.every((s) => s === 'online' || s === 'active');
  const someDown = statuses.some((s) => s !== 'online' && s !== 'active');

  if (allOnline) {
    return { label: 'All Systems Operational', color: 'text-green-400', bg: 'bg-green-500/10 border border-green-500/20' };
  }
  if (someDown) {
    return { label: 'Degraded Performance', color: 'text-yellow-400', bg: 'bg-yellow-500/10 border border-yellow-500/20' };
  }
  return { label: 'System Outage', color: 'text-red-400', bg: 'bg-red-500/10 border border-red-500/20' };
}

export default function AdminHealthPage() {
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
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const overallStatus = getOverallStatus(health?.services);

  if (loading && !health) {
    return <div className="text-center py-20 text-soc-muted">Loading system health...</div>;
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield className="w-6 h-6 text-soc-accent" />
            System Health
          </h1>
          <p className="text-sm text-soc-muted mt-1">
            Admin health monitoring &middot; Auto-refreshes every 15s
          </p>
        </div>
        <button onClick={fetchHealth} className="soc-btn-ghost !py-2 !px-3">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Overall Status Banner */}
      <div className={`rounded-lg p-4 flex items-center gap-3 ${overallStatus.bg}`}>
        {overallStatus.label === 'All Systems Operational' ? (
          <CheckCircle className={`w-6 h-6 ${overallStatus.color}`} />
        ) : (
          <XCircle className={`w-6 h-6 ${overallStatus.color}`} />
        )}
        <div>
          <p className={`text-lg font-semibold ${overallStatus.color}`}>
            {overallStatus.label}
          </p>
          <p className="text-xs text-soc-muted">
            Last checked: {health ? new Date().toLocaleTimeString() : 'N/A'}
          </p>
        </div>
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
      {health?.history?.length > 0 && (
        <div className="soc-card">
          <h3 className="text-base font-semibold text-white mb-4">Health History</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-soc-border">
                  <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-3 py-2">Time</th>
                  <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-3 py-2">CPU</th>
                  <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-3 py-2">Memory</th>
                  <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-3 py-2">Disk</th>
                  <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-3 py-2">Alerts/hr</th>
                  <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-3 py-2">Captures</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-soc-border/50">
                {health.history.slice(0, 20).map((h) => {
                  const cpuColor = h.cpu_percent > 90 ? 'text-red-400' : h.cpu_percent > 70 ? 'text-yellow-400' : 'text-soc-text';
                  const memColor = h.memory_percent > 90 ? 'text-red-400' : h.memory_percent > 70 ? 'text-yellow-400' : 'text-soc-text';
                  const diskColor = h.disk_usage_percent > 90 ? 'text-red-400' : h.disk_usage_percent > 70 ? 'text-yellow-400' : 'text-soc-text';

                  return (
                    <tr key={h.id} className="hover:bg-soc-surface/30 transition-colors">
                      <td className="px-3 py-2 text-soc-muted whitespace-nowrap">
                        {new Date(h.checked_at).toLocaleString()}
                      </td>
                      <td className={`px-3 py-2 ${cpuColor}`}>{h.cpu_percent?.toFixed(1)}%</td>
                      <td className={`px-3 py-2 ${memColor}`}>{h.memory_percent?.toFixed(1)}%</td>
                      <td className={`px-3 py-2 ${diskColor}`}>{h.disk_usage_percent?.toFixed(1)}%</td>
                      <td className="px-3 py-2 text-soc-text">{h.alerts_last_hour}</td>
                      <td className="px-3 py-2 text-soc-text">{h.capture_sessions_active}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </motion.div>
  );
}
