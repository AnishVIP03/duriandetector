/**
 * Traffic Filter Configuration Page — manage auto-categorisation rules.
 */
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Filter, Plus, Trash2, Edit3, RefreshCw, ToggleLeft, ToggleRight } from 'lucide-react';
import { alertsAPI } from '../../api/alerts';
import toast from 'react-hot-toast';

const FILTER_TYPES = [
  { value: 'ip_range', label: 'IP Range', placeholder: 'e.g. 192.168.0.0/24' },
  { value: 'port_range', label: 'Port Range', placeholder: 'e.g. 80-443' },
  { value: 'protocol', label: 'Protocol', placeholder: 'e.g. ICMP, TCP' },
  { value: 'country', label: 'Country', placeholder: 'e.g. CN, RU' },
  { value: 'alert_type', label: 'Alert Type', placeholder: 'e.g. port_scan, dos' },
];
const TRAFFIC_CATEGORIES = [
  { value: 'custom', label: 'Custom' },
  { value: 'volume', label: 'Volume-based', hint: 'e.g. Block IP if > 500 requests per minute' },
  { value: 'login', label: 'Login-based', hint: 'e.g. Flag IP if > 5 failed logins in 60 seconds' },
  { value: 'domain', label: 'Domain-based', hint: 'e.g. Block requests to suspicious domains' },
];
const ACTIONS = [
  { value: 'suppress', label: 'Suppress', desc: 'Hide matching alerts from default view' },
  { value: 'highlight', label: 'Highlight', desc: 'Flag matching alerts for attention' },
  { value: 'auto_block', label: 'Auto Block', desc: 'Automatically block matching IPs' },
  { value: 'alert_only', label: 'Alert Only', desc: 'Generate an alert without blocking' },
  { value: 'auto_block_timed', label: 'Auto-Block 1hr', desc: 'Auto-block the IP for 1 hour' },
];

export default function TrafficFilterPage() {
  const [filters, setFilters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '', filter_type: 'ip_range', value: '', action: 'suppress',
    traffic_category: 'custom', threshold_count: '', threshold_window_seconds: '',
  });

  const fetchFilters = async () => {
    setLoading(true);
    try {
      const res = await alertsAPI.getTrafficFilters();
      setFilters(res.data?.results || res.data || []);
    } catch {
      toast.error('Failed to load traffic filters');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchFilters(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.value) return toast.error('Name and value are required');
    try {
      const payload = { ...formData };
      if (payload.threshold_count) payload.threshold_count = parseInt(payload.threshold_count, 10);
      else delete payload.threshold_count;
      if (payload.threshold_window_seconds) payload.threshold_window_seconds = parseInt(payload.threshold_window_seconds, 10);
      else delete payload.threshold_window_seconds;
      await alertsAPI.createTrafficFilter(payload);
      toast.success('Filter rule created');
      setFormData({ name: '', filter_type: 'ip_range', value: '', action: 'suppress', traffic_category: 'custom', threshold_count: '', threshold_window_seconds: '' });
      setShowForm(false);
      fetchFilters();
    } catch {
      toast.error('Failed to create filter');
    }
  };

  const handleToggle = async (id) => {
    try {
      await alertsAPI.toggleTrafficFilter(id);
      toast.success('Filter toggled');
      fetchFilters();
    } catch {
      toast.error('Failed to toggle filter');
    }
  };

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete filter "${name}"?`)) return;
    try {
      await alertsAPI.deleteTrafficFilter(id);
      toast.success('Filter deleted');
      fetchFilters();
    } catch {
      toast.error('Failed to delete filter');
    }
  };

  const currentType = FILTER_TYPES.find(t => t.value === formData.filter_type);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Filter className="w-7 h-7 text-cyan-400" />
            Traffic Filters
          </h1>
          <p className="text-soc-muted mt-1">Configure rules to auto-categorise network traffic</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchFilters} className="p-2 rounded-lg bg-soc-surface text-soc-muted hover:text-white transition-colors">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 transition-colors text-sm font-medium"
          >
            <Plus className="w-4 h-4" />
            New Rule
          </button>
        </div>
      </div>

      {/* Action descriptions */}
      <div className="grid grid-cols-3 gap-3">
        {ACTIONS.map(a => (
          <div key={a.value} className="bg-soc-card border border-soc-border rounded-xl p-3">
            <span className={`text-sm font-medium ${
              a.value === 'suppress' ? 'text-yellow-400' : a.value === 'highlight' ? 'text-blue-400' : 'text-red-400'
            }`}>{a.label}</span>
            <p className="text-xs text-soc-muted mt-1">{a.desc}</p>
          </div>
        ))}
      </div>

      {/* Create Form */}
      {showForm && (
        <motion.form
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={handleCreate}
          className="bg-soc-card border border-soc-border rounded-xl p-4 space-y-4"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-soc-muted mb-1 block">Rule Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g. Block China Traffic"
                className="w-full px-3 py-2 bg-soc-surface border border-soc-border rounded-lg text-white placeholder:text-soc-muted focus:outline-none focus:border-cyan-400"
              />
            </div>
            <div>
              <label className="text-sm text-soc-muted mb-1 block">Traffic Category</label>
              <select
                value={formData.traffic_category}
                onChange={(e) => setFormData(prev => ({ ...prev, traffic_category: e.target.value }))}
                className="w-full px-3 py-2 bg-soc-surface border border-soc-border rounded-lg text-white text-sm focus:outline-none focus:border-cyan-400"
              >
                {TRAFFIC_CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
              {TRAFFIC_CATEGORIES.find(c => c.value === formData.traffic_category)?.hint && (
                <p className="text-xs text-cyan-400/60 mt-1">
                  {TRAFFIC_CATEGORIES.find(c => c.value === formData.traffic_category).hint}
                </p>
              )}
            </div>
            <div>
              <label className="text-sm text-soc-muted mb-1 block">Filter Type</label>
              <select
                value={formData.filter_type}
                onChange={(e) => setFormData(prev => ({ ...prev, filter_type: e.target.value }))}
                className="w-full px-3 py-2 bg-soc-surface border border-soc-border rounded-lg text-white text-sm focus:outline-none focus:border-cyan-400"
              >
                {FILTER_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm text-soc-muted mb-1 block">Value</label>
              <input
                type="text"
                value={formData.value}
                onChange={(e) => setFormData(prev => ({ ...prev, value: e.target.value }))}
                placeholder={currentType?.placeholder}
                className="w-full px-3 py-2 bg-soc-surface border border-soc-border rounded-lg text-white placeholder:text-soc-muted focus:outline-none focus:border-cyan-400"
              />
            </div>
            <div>
              <label className="text-sm text-soc-muted mb-1 block">Action</label>
              <select
                value={formData.action}
                onChange={(e) => setFormData(prev => ({ ...prev, action: e.target.value }))}
                className="w-full px-3 py-2 bg-soc-surface border border-soc-border rounded-lg text-white text-sm focus:outline-none focus:border-cyan-400"
              >
                {ACTIONS.map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
              </select>
            </div>
          </div>

          {/* Threshold Configuration — shown when category is not custom */}
          {formData.traffic_category !== 'custom' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 p-3 bg-soc-surface/50 border border-cyan-400/20 rounded-lg">
              <div>
                <label className="text-sm text-soc-muted mb-1 block">Threshold Count</label>
                <input
                  type="number"
                  min="1"
                  value={formData.threshold_count}
                  onChange={(e) => setFormData(prev => ({ ...prev, threshold_count: e.target.value }))}
                  placeholder={formData.traffic_category === 'volume' ? 'e.g. 500 requests' : formData.traffic_category === 'login' ? 'e.g. 5 failed attempts' : 'e.g. 100 requests'}
                  className="w-full px-3 py-2 bg-soc-surface border border-soc-border rounded-lg text-white placeholder:text-soc-muted focus:outline-none focus:border-cyan-400"
                />
              </div>
              <div>
                <label className="text-sm text-soc-muted mb-1 block">Time Window (seconds)</label>
                <input
                  type="number"
                  min="1"
                  value={formData.threshold_window_seconds}
                  onChange={(e) => setFormData(prev => ({ ...prev, threshold_window_seconds: e.target.value }))}
                  placeholder="e.g. 60 for per-minute"
                  className="w-full px-3 py-2 bg-soc-surface border border-soc-border rounded-lg text-white placeholder:text-soc-muted focus:outline-none focus:border-cyan-400"
                />
              </div>
            </div>
          )}
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 rounded-lg bg-soc-surface text-soc-muted hover:text-white text-sm">
              Cancel
            </button>
            <button type="submit" className="px-4 py-2 rounded-lg bg-cyan-500 text-white hover:bg-cyan-600 text-sm font-medium">
              Create Rule
            </button>
          </div>
        </motion.form>
      )}

      {/* Rules Table */}
      <div className="bg-soc-card border border-soc-border rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-soc-border">
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Name</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Category</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Type</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Value</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Threshold</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Action</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Active</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Controls</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="8" className="px-4 py-8 text-center text-soc-muted">Loading...</td></tr>
            ) : filters.length === 0 ? (
              <tr><td colSpan="8" className="px-4 py-8 text-center text-soc-muted">No traffic filter rules. Create one above.</td></tr>
            ) : (
              filters.map((rule) => (
                <motion.tr
                  key={rule.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="border-b border-soc-border/50 hover:bg-soc-surface/50 transition-colors"
                >
                  <td className="px-4 py-3 text-sm text-white font-medium">{rule.name}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      rule.traffic_category === 'volume' ? 'bg-purple-500/20 text-purple-400' :
                      rule.traffic_category === 'login' ? 'bg-orange-500/20 text-orange-400' :
                      rule.traffic_category === 'domain' ? 'bg-teal-500/20 text-teal-400' :
                      'bg-soc-surface text-soc-muted'
                    }`}>
                      {TRAFFIC_CATEGORIES.find(c => c.value === rule.traffic_category)?.label || 'Custom'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 rounded bg-soc-surface text-xs text-soc-muted">
                      {FILTER_TYPES.find(t => t.value === rule.filter_type)?.label || rule.filter_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-sm text-soc-muted">{rule.value}</td>
                  <td className="px-4 py-3 text-xs text-soc-muted">
                    {rule.threshold_count ? (
                      <span>{rule.threshold_count} / {rule.threshold_window_seconds}s</span>
                    ) : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      rule.action === 'suppress' ? 'bg-yellow-500/20 text-yellow-400' :
                      rule.action === 'highlight' ? 'bg-blue-500/20 text-blue-400' :
                      rule.action === 'alert_only' ? 'bg-green-500/20 text-green-400' :
                      rule.action === 'auto_block_timed' ? 'bg-orange-500/20 text-orange-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {ACTIONS.find(a => a.value === rule.action)?.label || rule.action}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button onClick={() => handleToggle(rule.id)} className="transition-colors">
                      {rule.is_active ? (
                        <ToggleRight className="w-6 h-6 text-green-400" />
                      ) : (
                        <ToggleLeft className="w-6 h-6 text-soc-muted" />
                      )}
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleDelete(rule.id, rule.name)}
                      className="p-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </motion.tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
