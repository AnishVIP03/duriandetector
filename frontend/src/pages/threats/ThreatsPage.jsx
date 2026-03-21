/**
 * Threat Intelligence page — US-12.
 * Lists known threat IPs with MITRE ATT&CK mappings.
 */
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  AlertTriangle, Search, Shield, RefreshCw,
  ExternalLink, Database
} from 'lucide-react';
import toast from 'react-hot-toast';
import { threatsAPI } from '../../api/alerts';

const THREAT_TYPE_COLORS = {
  scanner: 'bg-blue-500/20 text-blue-400',
  brute_force: 'bg-red-500/20 text-red-400',
  botnet: 'bg-purple-500/20 text-purple-400',
  malware: 'bg-red-600/20 text-red-500',
  phishing: 'bg-orange-500/20 text-orange-400',
  tor_exit_node: 'bg-yellow-500/20 text-yellow-400',
  proxy: 'bg-cyan-500/20 text-cyan-400',
  spam: 'bg-gray-500/20 text-gray-400',
};

export default function ThreatsPage() {
  const [threats, setThreats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [correlationResult, setCorrelationResult] = useState(null);
  const [correlating, setCorrelating] = useState(false);

  useEffect(() => {
    fetchThreats();
  }, []);

  const fetchThreats = async () => {
    setLoading(true);
    try {
      const { data } = await threatsAPI.getAll();
      setThreats(data.results || data);
    } catch (err) {
      console.error('Failed to fetch threats:', err);
      toast.error('Failed to load threat intelligence data');
    } finally {
      setLoading(false);
    }
  };

  const handleCorrelate = async (ip) => {
    setCorrelating(true);
    try {
      const { data } = await threatsAPI.correlate(ip);
      setCorrelationResult(data);
    } catch {
      toast.error('Correlation failed');
    } finally {
      setCorrelating(false);
    }
  };

  const filteredThreats = threats.filter((t) =>
    t.ip_address?.includes(search) ||
    t.domain?.includes(search) ||
    t.threat_type?.includes(search) ||
    t.description?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-soc-warning" />
            Threat Intelligence
          </h1>
          <p className="text-sm text-soc-muted mt-1">
            Known malicious IPs and threat indicators
          </p>
        </div>
        <button onClick={fetchThreats} className="soc-btn-ghost !py-2 !px-3">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-soc-muted" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="soc-input pl-10"
          placeholder="Search by IP, domain, threat type..."
        />
      </div>

      {/* Correlation result */}
      {correlationResult && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="soc-card soc-glow"
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-semibold text-white">
              Threat Correlation: {correlationResult.ip_address}
            </h3>
            <button
              onClick={() => setCorrelationResult(null)}
              className="text-soc-muted hover:text-white text-sm"
            >
              Close
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
            <div className="bg-soc-surface rounded-lg p-3">
              <p className="text-xs text-soc-muted">Known Threat</p>
              <p className={`text-lg font-bold ${correlationResult.is_known_threat ? 'text-red-400' : 'text-green-400'}`}>
                {correlationResult.is_known_threat ? 'Yes' : 'No'}
              </p>
            </div>
            <div className="bg-soc-surface rounded-lg p-3">
              <p className="text-xs text-soc-muted">Alert Count</p>
              <p className="text-lg font-bold text-white">{correlationResult.alert_count}</p>
            </div>
          </div>
          <div className="p-3 bg-soc-surface rounded-lg">
            <p className="text-sm text-soc-text">{correlationResult.recommendation}</p>
          </div>
        </motion.div>
      )}

      {/* Threats table */}
      <div className="soc-card !p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-soc-border">
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">IP Address</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Type</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Source</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Confidence</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">MITRE</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Description</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-soc-border">
              {loading ? (
                <tr><td colSpan={7} className="text-center py-12 text-soc-muted">Loading...</td></tr>
              ) : filteredThreats.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-soc-muted">
                    <Database className="w-12 h-12 mx-auto mb-3 opacity-20" />
                    <p>No threats found</p>
                  </td>
                </tr>
              ) : (
                filteredThreats.map((threat) => (
                  <tr key={threat.id} className="hover:bg-soc-surface/50 transition-colors">
                    <td className="px-4 py-3 text-sm font-mono text-soc-text">{threat.ip_address}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${THREAT_TYPE_COLORS[threat.threat_type] || 'bg-soc-surface text-soc-muted'}`}>
                        {threat.threat_type?.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-soc-muted">{threat.source}</td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-12 h-1.5 bg-soc-surface rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full bg-soc-accent"
                            style={{ width: `${threat.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-soc-muted">{(threat.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {threat.mitre_technique_id && (
                        <span className="text-xs text-soc-accent bg-soc-accent/10 px-1.5 py-0.5 rounded">
                          {threat.mitre_technique_id}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-soc-muted max-w-[200px] truncate">
                      {threat.description}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleCorrelate(threat.ip_address)}
                        disabled={correlating}
                        className="p-1.5 rounded hover:bg-soc-accent/10 text-soc-muted hover:text-soc-accent transition-colors"
                        title="Correlate with alerts"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
