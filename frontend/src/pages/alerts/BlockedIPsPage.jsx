/**
 * Block Control List — view and manage blocked IPs.
 */
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, ShieldOff, Search, RefreshCw } from 'lucide-react';
import { alertsAPI } from '../../api/alerts';
import toast from 'react-hot-toast';

export default function BlockedIPsPage() {
  const [blockedIPs, setBlockedIPs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAll, setShowAll] = useState(false);
  const [search, setSearch] = useState('');

  const fetchBlockedIPs = async () => {
    setLoading(true);
    try {
      const params = {};
      if (!showAll) params.is_active = 'true';
      if (search) params.search = search;
      const res = await alertsAPI.getBlockedIPs(params);
      setBlockedIPs(res.data?.results || res.data || []);
    } catch {
      toast.error('Failed to load blocked IPs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchBlockedIPs(); }, [showAll, search]);

  const handleUnblock = async (id, ip) => {
    if (!confirm(`Unblock IP ${ip}?`)) return;
    try {
      await alertsAPI.unblockIPById(id);
      toast.success(`Unblocked ${ip}`);
      fetchBlockedIPs();
    } catch {
      toast.error('Failed to unblock IP');
    }
  };

  const activeCount = blockedIPs.filter(b => b.is_active).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Shield className="w-7 h-7 text-red-400" />
            Block Control List
          </h1>
          <p className="text-soc-muted mt-1">Manage blocked IP addresses</p>
        </div>
        <button onClick={fetchBlockedIPs} className="p-2 rounded-lg bg-soc-surface text-soc-muted hover:text-white transition-colors">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-soc-card border border-soc-border rounded-xl p-4">
          <p className="text-soc-muted text-sm">Total Blocked</p>
          <p className="text-2xl font-bold text-white">{blockedIPs.length}</p>
        </div>
        <div className="bg-soc-card border border-soc-border rounded-xl p-4">
          <p className="text-soc-muted text-sm">Currently Active</p>
          <p className="text-2xl font-bold text-red-400">{activeCount}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-soc-muted" />
          <input
            type="text"
            placeholder="Search by IP address..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-soc-surface border border-soc-border rounded-lg text-white placeholder:text-soc-muted focus:outline-none focus:border-soc-accent"
          />
        </div>
        <button
          onClick={() => setShowAll(!showAll)}
          className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            showAll ? 'bg-soc-accent/20 text-soc-accent border border-soc-accent/30' : 'bg-soc-surface text-soc-muted border border-soc-border hover:text-white'
          }`}
        >
          {showAll ? 'Show All' : 'Active Only'}
        </button>
      </div>

      {/* Table */}
      <div className="bg-soc-card border border-soc-border rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-soc-border">
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">IP Address</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Reason</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Blocked By</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Blocked At</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Status</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="6" className="px-4 py-8 text-center text-soc-muted">Loading...</td></tr>
            ) : blockedIPs.length === 0 ? (
              <tr><td colSpan="6" className="px-4 py-8 text-center text-soc-muted">No blocked IPs found</td></tr>
            ) : (
              blockedIPs.map((item) => (
                <motion.tr
                  key={item.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="border-b border-soc-border/50 hover:bg-soc-surface/50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="font-mono text-sm text-white">{item.ip_address}</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-soc-muted max-w-[200px] truncate">{item.reason || '-'}</td>
                  <td className="px-4 py-3 text-sm text-soc-muted">{item.blocked_by_email}</td>
                  <td className="px-4 py-3 text-sm text-soc-muted">
                    {new Date(item.blocked_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      item.is_active ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
                    }`}>
                      {item.is_active ? 'Blocked' : 'Unblocked'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {item.is_active && (
                      <button
                        onClick={() => handleUnblock(item.id, item.ip_address)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-500/10 text-green-400 hover:bg-green-500/20 text-sm transition-colors"
                      >
                        <ShieldOff className="w-3.5 h-3.5" />
                        Unblock
                      </button>
                    )}
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
