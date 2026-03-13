/**
 * Admin Teams Page — view all environments/teams across the system.
 */
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Search, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';
import { environmentsAPI } from '../../api/environments';
import toast from 'react-hot-toast';

export default function AdminTeamsPage() {
  const [environments, setEnvironments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [expandedId, setExpandedId] = useState(null);
  const [memberData, setMemberData] = useState({});

  const fetchEnvironments = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      const res = await environmentsAPI.adminListAll(params);
      setEnvironments(res.data?.results || res.data || []);
    } catch {
      toast.error('Failed to load environments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchEnvironments(); }, [search]);

  const toggleExpand = async (envId) => {
    if (expandedId === envId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(envId);
    if (!memberData[envId]) {
      try {
        const res = await environmentsAPI.adminGetDetail(envId);
        setMemberData(prev => ({ ...prev, [envId]: res.data.members || [] }));
      } catch {
        toast.error('Failed to load members');
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Users className="w-7 h-7 text-blue-400" />
            All Teams / Environments
          </h1>
          <p className="text-soc-muted mt-1">Admin overview of all environments across the system</p>
        </div>
        <button onClick={fetchEnvironments} className="p-2 rounded-lg bg-soc-surface text-soc-muted hover:text-white transition-colors">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-soc-muted" />
        <input
          type="text"
          placeholder="Search by name or organisation..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-soc-surface border border-soc-border rounded-lg text-white placeholder:text-soc-muted focus:outline-none focus:border-soc-accent"
        />
      </div>

      {/* Stats */}
      <div className="bg-soc-card border border-soc-border rounded-xl p-4">
        <p className="text-soc-muted text-sm">Total Environments</p>
        <p className="text-2xl font-bold text-white">{environments.length}</p>
      </div>

      {/* Environments List */}
      <div className="space-y-3">
        {loading ? (
          <div className="text-center text-soc-muted py-8">Loading...</div>
        ) : environments.length === 0 ? (
          <div className="text-center text-soc-muted py-8">No environments found</div>
        ) : (
          environments.map((env) => (
            <motion.div
              key={env.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-soc-card border border-soc-border rounded-xl overflow-hidden"
            >
              <button
                onClick={() => toggleExpand(env.id)}
                className="w-full px-4 py-4 flex items-center justify-between hover:bg-soc-surface/50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                    <Users className="w-5 h-5 text-blue-400" />
                  </div>
                  <div className="text-left">
                    <h3 className="font-medium text-white">{env.name}</h3>
                    <p className="text-sm text-soc-muted">{env.organisation || 'No organisation'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-sm text-white">{env.member_count} members</p>
                    <p className="text-xs text-soc-muted">{env.alert_count} alerts</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-soc-muted">Owner: {env.owner_email}</p>
                    <p className="text-xs text-soc-muted">{new Date(env.created_at).toLocaleDateString()}</p>
                  </div>
                  {expandedId === env.id ? (
                    <ChevronUp className="w-4 h-4 text-soc-muted" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-soc-muted" />
                  )}
                </div>
              </button>

              <AnimatePresence>
                {expandedId === env.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden border-t border-soc-border"
                  >
                    <div className="p-4">
                      <h4 className="text-sm font-medium text-soc-muted mb-3">Members</h4>
                      {memberData[env.id] ? (
                        <div className="space-y-2">
                          {memberData[env.id].map((member) => (
                            <div key={member.id} className="flex items-center justify-between bg-soc-surface/50 rounded-lg px-3 py-2">
                              <div>
                                <p className="text-sm text-white">
                                  {member.user?.first_name} {member.user?.last_name}
                                </p>
                                <p className="text-xs text-soc-muted">{member.user?.email}</p>
                              </div>
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                member.role === 'team_leader' ? 'bg-yellow-500/20 text-yellow-400' :
                                member.role === 'security_analyst' ? 'bg-blue-500/20 text-blue-400' :
                                'bg-soc-surface text-soc-muted'
                              }`}>
                                {member.role}
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-soc-muted">Loading members...</p>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
