/**
 * Alert List page — US-07, US-09, US-10.
 * Filterable, searchable alert table with severity badges and actions.
 */
import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Bell, Filter, Search, Shield, Ban, ExternalLink,
  ChevronLeft, ChevronRight, RefreshCw, X
} from 'lucide-react';
import toast from 'react-hot-toast';
import { alertsAPI } from '../../api/alerts';
import { useWebSocket } from '../../hooks/useWebSocket';

const SEVERITY_COLORS = {
  low: 'badge-low',
  medium: 'badge-medium',
  high: 'badge-high',
  critical: 'badge-critical',
};

const ALERT_TYPE_LABELS = {
  port_scan: 'Port Scan',
  dos: 'DoS',
  brute_force: 'Brute Force',
  sql_injection: 'SQL Injection',
  xss: 'XSS',
  protocol_anomaly: 'Protocol Anomaly',
  suspicious_ip: 'Suspicious IP',
  other: 'Other',
};

export default function AlertListPage() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    severity: '',
    alert_type: '',
    protocol: '',
    search: '',
    date_from: '',
    date_to: '',
  });
  const [showFilters, setShowFilters] = useState(false);

  // Real-time alerts via WebSocket
  useWebSocket('ws/alerts/', {
    onMessage: (data) => {
      setAlerts((prev) => [data, ...prev].slice(0, 100));
      toast(`New ${data.severity} alert: ${data.alert_type}`, {
        icon: data.severity === 'critical' ? '🔴' : '🟡',
      });
    },
  });

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page };
      if (filters.severity) params.severity = filters.severity;
      if (filters.alert_type) params.alert_type = filters.alert_type;
      if (filters.protocol) params.protocol = filters.protocol;
      if (filters.search) params.search = filters.search;
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;

      const { data } = await alertsAPI.getAll(params);
      setAlerts(data.results || data);
      if (data.count) {
        setTotalPages(Math.ceil(data.count / 25));
      }
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const handleBlock = async (alertId) => {
    try {
      await alertsAPI.blockIP(alertId, 'Blocked from alert list');
      toast.success('IP blocked successfully');
      fetchAlerts();
    } catch {
      toast.error('Failed to block IP');
    }
  };

  const clearFilters = () => {
    setFilters({ severity: '', alert_type: '', protocol: '', search: '', date_from: '', date_to: '' });
    setPage(1);
  };

  const hasActiveFilters = Object.values(filters).some(Boolean);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Bell className="w-6 h-6 text-soc-accent" />
            Alerts
          </h1>
          <p className="text-sm text-soc-muted mt-1">
            Real-time network security alerts
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchAlerts} className="soc-btn-ghost !py-2 !px-3">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`soc-btn-ghost !py-2 !px-3 flex items-center gap-2 ${showFilters ? 'border-soc-accent text-soc-accent' : ''}`}
          >
            <Filter className="w-4 h-4" />
            Filters
            {hasActiveFilters && (
              <span className="w-2 h-2 rounded-full bg-soc-accent" />
            )}
          </button>
        </div>
      </div>

      {/* Search bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-soc-muted" />
        <input
          type="text"
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          className="soc-input pl-10"
          placeholder="Search by IP address, country, city..."
        />
      </div>

      {/* Filters panel */}
      {showFilters && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          className="soc-card"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Filter Alerts</h3>
            {hasActiveFilters && (
              <button onClick={clearFilters} className="text-xs text-soc-accent flex items-center gap-1">
                <X className="w-3 h-3" /> Clear all
              </button>
            )}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div>
              <label className="text-xs text-soc-muted mb-1 block">Severity</label>
              <select
                value={filters.severity}
                onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
                className="soc-input !py-2"
              >
                <option value="">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-soc-muted mb-1 block">Alert Type</label>
              <select
                value={filters.alert_type}
                onChange={(e) => setFilters({ ...filters, alert_type: e.target.value })}
                className="soc-input !py-2"
              >
                <option value="">All Types</option>
                {Object.entries(ALERT_TYPE_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-soc-muted mb-1 block">Protocol</label>
              <select
                value={filters.protocol}
                onChange={(e) => setFilters({ ...filters, protocol: e.target.value })}
                className="soc-input !py-2"
              >
                <option value="">All Protocols</option>
                <option value="TCP">TCP</option>
                <option value="UDP">UDP</option>
                <option value="ICMP">ICMP</option>
                <option value="HTTP">HTTP</option>
                <option value="DNS">DNS</option>
                <option value="SSH">SSH</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-soc-muted mb-1 block">Date From</label>
              <input
                type="datetime-local"
                value={filters.date_from}
                onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
                className="soc-input !py-2"
              />
            </div>
            <div>
              <label className="text-xs text-soc-muted mb-1 block">Date To</label>
              <input
                type="datetime-local"
                value={filters.date_to}
                onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
                className="soc-input !py-2"
              />
            </div>
          </div>
        </motion.div>
      )}

      {/* Alerts table */}
      <div className="soc-card overflow-hidden !p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-soc-border">
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Severity</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Type</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Source IP</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Dest IP</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Protocol</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Confidence</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Country</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Time</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-soc-border">
              {loading && alerts.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-12 text-soc-muted">
                    Loading alerts...
                  </td>
                </tr>
              ) : alerts.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-12 text-soc-muted">
                    <Shield className="w-12 h-12 mx-auto mb-3 opacity-20" />
                    <p>No alerts found</p>
                  </td>
                </tr>
              ) : (
                alerts.map((alert) => (
                  <motion.tr
                    key={alert.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className={`hover:bg-soc-surface/50 transition-colors ${
                      alert.is_blocked ? 'opacity-50' : ''
                    }`}
                  >
                    <td className="px-4 py-3">
                      <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${SEVERITY_COLORS[alert.severity]}`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-soc-text">
                      {ALERT_TYPE_LABELS[alert.alert_type] || alert.alert_type}
                      {alert.mitre_technique_id && (
                        <span className="ml-2 text-xs text-soc-accent bg-soc-accent/10 px-1.5 py-0.5 rounded">
                          {alert.mitre_technique_id}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-soc-text">{alert.src_ip}</td>
                    <td className="px-4 py-3 text-sm font-mono text-soc-muted">{alert.dst_ip}</td>
                    <td className="px-4 py-3 text-sm text-soc-muted">{alert.protocol}</td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-soc-surface rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full bg-soc-accent"
                            style={{ width: `${(alert.confidence * 100 || alert.confidence_score * 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-soc-muted">
                          {((alert.confidence || alert.confidence_score) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-soc-muted">{alert.country || '—'}</td>
                    <td className="px-4 py-3 text-xs text-soc-muted">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <Link
                          to={`/alerts/${alert.id}`}
                          className="p-1.5 rounded hover:bg-soc-accent/10 text-soc-muted hover:text-soc-accent transition-colors"
                          title="View details"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </Link>
                        {!alert.is_blocked && (
                          <button
                            onClick={() => handleBlock(alert.id)}
                            className="p-1.5 rounded hover:bg-red-500/10 text-soc-muted hover:text-red-400 transition-colors"
                            title="Block IP"
                          >
                            <Ban className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-soc-border">
            <span className="text-sm text-soc-muted">Page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="soc-btn-ghost !py-1.5 !px-3 disabled:opacity-30"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="soc-btn-ghost !py-1.5 !px-3 disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
