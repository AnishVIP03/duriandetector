/**
 * IP Whitelist Page — manage false-positive IP suppression.
 */
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, Plus, Trash2, RefreshCw } from 'lucide-react';
import { alertsAPI } from '../../api/alerts';
import toast from 'react-hot-toast';

export default function WhitelistPage() {
  const [whitelist, setWhitelist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ ip_address: '', reason: '' });

  const fetchWhitelist = async () => {
    setLoading(true);
    try {
      const res = await alertsAPI.getWhitelist();
      setWhitelist(res.data?.results || res.data || []);
    } catch {
      toast.error('Failed to load whitelist');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchWhitelist(); }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!formData.ip_address) return toast.error('IP address is required');
    try {
      await alertsAPI.addToWhitelist(formData);
      toast.success(`Whitelisted ${formData.ip_address}`);
      setFormData({ ip_address: '', reason: '' });
      setShowForm(false);
      fetchWhitelist();
    } catch (err) {
      toast.error(err.response?.data?.ip_address?.[0] || 'Failed to add IP');
    }
  };

  const handleRemove = async (id, ip) => {
    if (!confirm(`Remove ${ip} from whitelist?`)) return;
    try {
      await alertsAPI.removeFromWhitelist(id);
      toast.success(`Removed ${ip} from whitelist`);
      fetchWhitelist();
    } catch {
      toast.error('Failed to remove IP');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <ShieldCheck className="w-7 h-7 text-green-400" />
            IP Whitelist
          </h1>
          <p className="text-soc-muted mt-1">Manage trusted IPs to suppress false-positive alerts</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchWhitelist} className="p-2 rounded-lg bg-soc-surface text-soc-muted hover:text-white transition-colors">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors text-sm font-medium"
          >
            <Plus className="w-4 h-4" />
            Add IP
          </button>
        </div>
      </div>

      {/* Add Form */}
      {showForm && (
        <motion.form
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={handleAdd}
          className="bg-soc-card border border-soc-border rounded-xl p-4 space-y-4"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-soc-muted mb-1 block">IP Address</label>
              <input
                type="text"
                value={formData.ip_address}
                onChange={(e) => setFormData(prev => ({ ...prev, ip_address: e.target.value }))}
                placeholder="e.g. 192.168.1.100"
                className="w-full px-3 py-2 bg-soc-surface border border-soc-border rounded-lg text-white placeholder:text-soc-muted focus:outline-none focus:border-green-400"
              />
            </div>
            <div>
              <label className="text-sm text-soc-muted mb-1 block">Reason</label>
              <input
                type="text"
                value={formData.reason}
                onChange={(e) => setFormData(prev => ({ ...prev, reason: e.target.value }))}
                placeholder="e.g. Internal scanner, known safe device"
                className="w-full px-3 py-2 bg-soc-surface border border-soc-border rounded-lg text-white placeholder:text-soc-muted focus:outline-none focus:border-green-400"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 rounded-lg bg-soc-surface text-soc-muted hover:text-white text-sm">
              Cancel
            </button>
            <button type="submit" className="px-4 py-2 rounded-lg bg-green-500 text-white hover:bg-green-600 text-sm font-medium">
              Add to Whitelist
            </button>
          </div>
        </motion.form>
      )}

      {/* Stats */}
      <div className="bg-soc-card border border-soc-border rounded-xl p-4">
        <p className="text-soc-muted text-sm">Whitelisted IPs</p>
        <p className="text-2xl font-bold text-green-400">{whitelist.length}</p>
      </div>

      {/* Table */}
      <div className="bg-soc-card border border-soc-border rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-soc-border">
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">IP Address</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Reason</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Added By</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Date</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="5" className="px-4 py-8 text-center text-soc-muted">Loading...</td></tr>
            ) : whitelist.length === 0 ? (
              <tr><td colSpan="5" className="px-4 py-8 text-center text-soc-muted">No whitelisted IPs. Add one above.</td></tr>
            ) : (
              whitelist.map((item) => (
                <motion.tr
                  key={item.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="border-b border-soc-border/50 hover:bg-soc-surface/50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="font-mono text-sm text-white">{item.ip_address}</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-soc-muted">{item.reason || '-'}</td>
                  <td className="px-4 py-3 text-sm text-soc-muted">{item.added_by_email}</td>
                  <td className="px-4 py-3 text-sm text-soc-muted">
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleRemove(item.id, item.ip_address)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 text-sm transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      Remove
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
