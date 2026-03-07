/**
 * Admin Audit Logs page.
 * Displays audit trail of user actions with search, filter, pagination, and auto-refresh.
 */
import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ClipboardList, Search, Filter, RefreshCw, Clock,
  ChevronLeft, ChevronRight, ChevronDown, ChevronUp, X
} from 'lucide-react';
import toast from 'react-hot-toast';
import { adminAPI } from '../../api/admin';

const ACTION_COLORS = {
  login: 'text-green-400 bg-green-500/10',
  logout: 'text-soc-muted bg-soc-surface',
  create: 'text-blue-400 bg-blue-500/10',
  update: 'text-yellow-400 bg-yellow-500/10',
  delete: 'text-red-400 bg-red-500/10',
  suspend: 'text-red-400 bg-red-500/10',
  unsuspend: 'text-green-400 bg-green-500/10',
  export: 'text-purple-400 bg-purple-500/10',
};

function getActionColor(action) {
  const lower = action?.toLowerCase() || '';
  for (const [key, cls] of Object.entries(ACTION_COLORS)) {
    if (lower.includes(key)) return cls;
  }
  return 'text-soc-text bg-soc-surface';
}

export default function AdminAuditPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [expandedRow, setExpandedRow] = useState(null);
  const [actionTypes, setActionTypes] = useState([]);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page };
      if (search) params.search = search;
      if (actionFilter) params.action = actionFilter;

      const { data } = await adminAPI.getAuditLogs(params);
      setLogs(data.results || data);
      setTotalCount(data.count || 0);
      if (data.count) {
        setTotalPages(Math.ceil(data.count / 25));
      }

      // Extract unique action types for filtering
      const results = data.results || data;
      if (results.length > 0 && actionTypes.length === 0) {
        const unique = [...new Set(results.map((l) => l.action).filter(Boolean))];
        setActionTypes(unique);
      }
    } catch (err) {
      console.error('Failed to fetch audit logs:', err);
      toast.error('Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }, [page, search, actionFilter]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(fetchLogs, 30000);
    return () => clearInterval(interval);
  }, [fetchLogs]);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const clearFilters = () => {
    setSearch('');
    setActionFilter('');
    setPage(1);
  };

  const hasActiveFilters = search || actionFilter;

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
            <ClipboardList className="w-6 h-6 text-soc-accent" />
            Audit Logs
          </h1>
          <p className="text-sm text-soc-muted mt-1">
            {totalCount} total entries &middot; Auto-refreshes every 30s
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchLogs} className="soc-btn-ghost !py-2 !px-3">
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
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="soc-input pl-10"
          placeholder="Search by user email or action..."
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
            <h3 className="text-sm font-semibold text-white">Filter Logs</h3>
            {hasActiveFilters && (
              <button onClick={clearFilters} className="text-xs text-soc-accent flex items-center gap-1">
                <X className="w-3 h-3" /> Clear all
              </button>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-soc-muted mb-1 block">Action Type</label>
              <select
                value={actionFilter}
                onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
                className="soc-input !py-2"
              >
                <option value="">All Actions</option>
                {actionTypes.map((action) => (
                  <option key={action} value={action}>{action}</option>
                ))}
              </select>
            </div>
          </div>
        </motion.div>
      )}

      {/* Audit Logs Table */}
      <div className="soc-card overflow-hidden !p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-soc-border">
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Timestamp</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">User</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Action</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Target Type</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Target ID</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">IP Address</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-soc-border">
              {loading && logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-soc-muted">
                    Loading audit logs...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-soc-muted">
                    <ClipboardList className="w-12 h-12 mx-auto mb-3 opacity-20" />
                    <p>No audit logs found</p>
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr
                    key={log.id}
                    className="hover:bg-soc-surface/50 transition-colors"
                  >
                    <td className="px-4 py-3 text-xs text-soc-muted whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3 h-3" />
                        {new Date(log.timestamp).toLocaleString()}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-soc-text font-mono">
                      {log.user_email || log.user || '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${getActionColor(log.action)}`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-soc-muted">
                      {log.target_type || '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-soc-muted font-mono">
                      {log.target_id || '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-soc-muted font-mono">
                      {log.ip_address || '—'}
                    </td>
                    <td className="px-4 py-3">
                      {log.metadata && Object.keys(log.metadata).length > 0 ? (
                        <button
                          onClick={() => setExpandedRow(expandedRow === log.id ? null : log.id)}
                          className="flex items-center gap-1 text-xs text-soc-accent hover:text-soc-accent/80 transition-colors"
                        >
                          {expandedRow === log.id ? (
                            <>
                              <ChevronUp className="w-3 h-3" /> Hide
                            </>
                          ) : (
                            <>
                              <ChevronDown className="w-3 h-3" /> View
                            </>
                          )}
                        </button>
                      ) : (
                        <span className="text-xs text-soc-muted">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {/* Expanded Metadata Rows */}
          <AnimatePresence>
            {logs.map((log) =>
              expandedRow === log.id && log.metadata ? (
                <motion.div
                  key={`meta-${log.id}`}
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="border-t border-soc-border bg-soc-bg/50 px-6 py-3 overflow-hidden"
                >
                  <p className="text-xs font-medium text-soc-muted mb-2">Metadata</p>
                  <pre className="text-xs text-soc-text bg-soc-surface rounded-lg p-3 overflow-x-auto">
                    {JSON.stringify(log.metadata, null, 2)}
                  </pre>
                </motion.div>
              ) : null
            )}
          </AnimatePresence>
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
    </motion.div>
  );
}
