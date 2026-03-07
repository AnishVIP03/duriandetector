/**
 * Attack Kill Chain Timeline — Visualization of multi-stage attacks.
 * Shows vertical timeline of attack chains with expandable alert nodes,
 * dynamic risk score gauge, and risk factors breakdown.
 */
import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Shield, Clock, Target, ChevronRight, ChevronDown,
  AlertTriangle, Activity, TrendingUp, RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';
import { attackChainsAPI } from '../../api/attackChains';

// Kill Chain phase color mapping
const PHASE_COLORS = {
  'Reconnaissance':       { bg: 'bg-blue-500/15',    border: 'border-blue-500',    text: 'text-blue-400',     dot: 'bg-blue-500' },
  'Weaponization':        { bg: 'bg-purple-500/15',   border: 'border-purple-500',   text: 'text-purple-400',   dot: 'bg-purple-500' },
  'Delivery':             { bg: 'bg-orange-500/15',   border: 'border-orange-500',   text: 'text-orange-400',   dot: 'bg-orange-500' },
  'Initial Access':       { bg: 'bg-orange-500/15',   border: 'border-orange-500',   text: 'text-orange-400',   dot: 'bg-orange-500' },
  'Exploitation':         { bg: 'bg-red-500/15',      border: 'border-red-500',      text: 'text-red-400',      dot: 'bg-red-500' },
  'Installation':         { bg: 'bg-red-700/15',      border: 'border-red-700',      text: 'text-red-300',      dot: 'bg-red-700' },
  'Credential Access':    { bg: 'bg-yellow-500/15',   border: 'border-yellow-500',   text: 'text-yellow-400',   dot: 'bg-yellow-500' },
  'Command and Control':  { bg: 'bg-yellow-500/15',   border: 'border-yellow-500',   text: 'text-yellow-400',   dot: 'bg-yellow-500' },
  'Impact':               { bg: 'bg-rose-600/15',     border: 'border-rose-600',     text: 'text-rose-400',     dot: 'bg-rose-600' },
};

const DEFAULT_PHASE = { bg: 'bg-soc-surface', border: 'border-soc-border', text: 'text-soc-muted', dot: 'bg-soc-muted' };

const SEVERITY_BADGES = {
  low: 'badge-low',
  medium: 'badge-medium',
  high: 'badge-high',
  critical: 'badge-critical',
};

const CHAIN_TYPE_LABELS = {
  recon_to_exploit: 'Recon to Exploit',
  scan_to_brute: 'Scan to Brute Force',
  dos_campaign: 'DoS Campaign',
  multi_stage: 'Multi-Stage Attack',
  other: 'Other',
};

function getPhase(mitreTactic) {
  if (!mitreTactic) return DEFAULT_PHASE;
  return PHASE_COLORS[mitreTactic] || DEFAULT_PHASE;
}

// ---------------------------------------------------------------------------
// Risk Score Gauge (detailed version)
// ---------------------------------------------------------------------------
function DetailedRiskGauge({ score, factors, loading }) {
  const getColor = (s) => {
    if (s <= 25) return '#10b981';
    if (s <= 50) return '#f59e0b';
    if (s <= 75) return '#f97316';
    return '#ef4444';
  };

  const getLabel = (s) => {
    if (s <= 25) return 'Low';
    if (s <= 50) return 'Moderate';
    if (s <= 75) return 'High';
    return 'Critical';
  };

  const rotation = (score / 100) * 180 - 90;
  const color = getColor(score);

  const factorList = factors ? [
    { label: 'Severity Distribution', score: factors.severity_distribution?.score, max: factors.severity_distribution?.max },
    { label: 'Active Threats', score: factors.active_threats?.score, max: factors.active_threats?.max },
    { label: 'Block Coverage', score: factors.blocked_ip_coverage?.score, max: factors.blocked_ip_coverage?.max },
    { label: 'Alert Velocity', score: factors.alert_velocity?.score, max: factors.alert_velocity?.max },
  ] : [];

  return (
    <div className="soc-card">
      <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
        <Activity className="w-5 h-5 text-soc-accent" />
        Dynamic Risk Score
      </h3>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-6 h-6 text-soc-muted animate-spin" />
        </div>
      ) : (
        <>
          {/* Gauge */}
          <div className="flex flex-col items-center mb-6">
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
            <p className="text-sm text-soc-muted mt-1">{getLabel(score)} Risk</p>
          </div>

          {/* Factor Breakdown */}
          {factorList.length > 0 && (
            <div className="space-y-3">
              <p className="text-xs text-soc-muted uppercase tracking-wider font-semibold">Contributing Factors</p>
              {factorList.map((f) => (
                <div key={f.label} className="flex items-center gap-3">
                  <span className="text-xs text-soc-muted w-36 shrink-0">{f.label}</span>
                  <div className="flex-1 h-2 bg-soc-surface rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${f.max > 0 ? (f.score / f.max) * 100 : 0}%` }}
                      transition={{ duration: 0.8 }}
                      className="h-full rounded-full"
                      style={{ backgroundColor: getColor((f.score / f.max) * 100) }}
                    />
                  </div>
                  <span className="text-xs text-soc-text w-14 text-right">
                    {Math.round(f.score)}/{f.max}
                  </span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Single Alert Node in the timeline
// ---------------------------------------------------------------------------
function AlertNode({ alert, index }) {
  const phase = getPhase(alert.mitre_tactic);

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="flex items-start gap-4 ml-8 relative"
    >
      {/* Timeline connector */}
      <div className="absolute left-0 top-0 bottom-0 w-px bg-soc-border -ml-4" />
      <div className={`absolute -ml-[21px] top-2 w-3 h-3 rounded-full border-2 border-soc-bg ${phase.dot}`} />

      <div className={`flex-1 rounded-lg border ${phase.border} ${phase.bg} p-3`}>
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${SEVERITY_BADGES[alert.severity]}`}>
              {alert.severity}
            </span>
            <span className="text-sm text-soc-text">
              {alert.alert_type?.replace(/_/g, ' ')}
            </span>
          </div>
          <span className="text-xs text-soc-muted">
            {new Date(alert.timestamp).toLocaleTimeString()}
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs text-soc-muted">
          <span className="font-mono">{alert.src_ip}</span>
          <span>{alert.protocol}</span>
          {alert.mitre_technique_id && (
            <span className={`${phase.text} bg-white/5 px-1.5 py-0.5 rounded`}>
              {alert.mitre_technique_id}
            </span>
          )}
          {alert.mitre_tactic && (
            <span className={phase.text}>{alert.mitre_tactic}</span>
          )}
          {alert.country && <span>{alert.country}</span>}
        </div>
      </div>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Single Attack Chain Card
// ---------------------------------------------------------------------------
function AttackChainCard({ chain, onExpand, isExpanded }) {
  const [detail, setDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const handleToggle = async () => {
    if (isExpanded) {
      onExpand(null);
      return;
    }
    onExpand(chain.id);

    if (!detail) {
      setLoadingDetail(true);
      try {
        const { data } = await attackChainsAPI.getDetail(chain.id);
        setDetail(data);
      } catch {
        toast.error('Failed to load chain details');
      } finally {
        setLoadingDetail(false);
      }
    }
  };

  const riskColor = chain.risk_score <= 40
    ? 'text-green-400'
    : chain.risk_score <= 70
    ? 'text-yellow-400'
    : 'text-red-400';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="soc-card !p-0 overflow-hidden"
    >
      {/* Chain header */}
      <button
        onClick={handleToggle}
        className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-soc-surface/50 transition-colors"
      >
        <div className="shrink-0">
          {isExpanded ? (
            <ChevronDown className="w-5 h-5 text-soc-accent" />
          ) : (
            <ChevronRight className="w-5 h-5 text-soc-muted" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <Target className="w-4 h-4 text-soc-accent shrink-0" />
            <h3 className="text-sm font-semibold text-white truncate">
              {CHAIN_TYPE_LABELS[chain.chain_type] || chain.chain_type}
            </h3>
            <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
              chain.status === 'active'
                ? 'bg-red-500/15 text-red-400 border border-red-500/30'
                : 'bg-green-500/15 text-green-400 border border-green-500/30'
            }`}>
              {chain.status}
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs text-soc-muted">
            <span className="font-mono">{chain.src_ip}</span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(chain.started_at).toLocaleString()}
            </span>
            <span>{chain.alert_count} alerts</span>
            {chain.mitre_technique_ids?.length > 0 && (
              <span className="text-soc-accent">
                {chain.mitre_technique_ids.join(', ')}
              </span>
            )}
          </div>
        </div>

        <div className="shrink-0 text-right">
          <p className={`text-lg font-bold ${riskColor}`}>{chain.risk_score}</p>
          <p className="text-xs text-soc-muted">risk</p>
        </div>
      </button>

      {/* Expanded alert timeline */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 pt-2 border-t border-soc-border">
              {loadingDetail ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="w-5 h-5 text-soc-muted animate-spin" />
                </div>
              ) : detail?.alerts?.length > 0 ? (
                <div className="space-y-3 mt-3">
                  <p className="text-xs text-soc-muted uppercase tracking-wider font-semibold mb-4">
                    Alert Timeline
                  </p>
                  {detail.alerts.map((alert, idx) => (
                    <AlertNode key={alert.id} alert={alert} index={idx} />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-soc-muted text-center py-6">
                  No alerts linked to this chain.
                </p>
              )}

              {/* MITRE techniques */}
              {detail?.mitre_techniques?.length > 0 && (
                <div className="mt-4 pt-4 border-t border-soc-border">
                  <p className="text-xs text-soc-muted uppercase tracking-wider font-semibold mb-2">
                    MITRE ATT&CK Techniques
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {detail.mitre_techniques.map((t) => (
                      <span
                        key={t.technique_id}
                        className="text-xs bg-soc-accent/10 text-soc-accent border border-soc-accent/20 px-2 py-1 rounded"
                      >
                        {t.technique_id} - {t.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------
export default function AttackChainPage() {
  const [chains, setChains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [riskData, setRiskData] = useState({ score: 0, factors: null });
  const [riskLoading, setRiskLoading] = useState(true);

  const fetchChains = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await attackChainsAPI.getAll();
      setChains(data.results || data);
    } catch {
      // API may not be available yet
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchRiskScore = useCallback(async () => {
    setRiskLoading(true);
    try {
      const { data } = await attackChainsAPI.getRiskScore();
      setRiskData({ score: data.score, factors: data.factors });
    } catch {
      // API may not be available yet
    } finally {
      setRiskLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchChains();
    fetchRiskScore();
  }, [fetchChains, fetchRiskScore]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Zap className="w-6 h-6 text-soc-accent" />
            Attack Kill Chain
          </h1>
          <p className="text-sm text-soc-muted mt-1">
            Multi-stage attack timeline and risk analysis
          </p>
        </div>
        <button
          onClick={() => { fetchChains(); fetchRiskScore(); }}
          className="soc-btn-ghost !py-2 !px-3"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Risk Score + Stats row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <DetailedRiskGauge
          score={riskData.score}
          factors={riskData.factors}
          loading={riskLoading}
        />

        {/* Quick stats */}
        <div className="lg:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="soc-card text-center">
            <Zap className="w-6 h-6 text-soc-accent mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">{chains.length}</p>
            <p className="text-xs text-soc-muted">Attack Chains</p>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="soc-card text-center">
            <AlertTriangle className="w-6 h-6 text-red-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">
              {chains.filter((c) => c.status === 'active').length}
            </p>
            <p className="text-xs text-soc-muted">Active Chains</p>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="soc-card text-center">
            <Target className="w-6 h-6 text-orange-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">
              {new Set(chains.map((c) => c.src_ip)).size}
            </p>
            <p className="text-xs text-soc-muted">Unique Sources</p>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="soc-card text-center">
            <TrendingUp className="w-6 h-6 text-yellow-400 mx-auto mb-2" />
            <p className="text-2xl font-bold text-white">
              {riskData.factors?.active_threats?.unique_ips || 0}
            </p>
            <p className="text-xs text-soc-muted">Threat IPs (24h)</p>
          </motion.div>
        </div>
      </div>

      {/* Attack Chain Timeline */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-soc-accent" />
          Attack Chains
        </h2>

        {loading ? (
          <div className="soc-card flex items-center justify-center py-16">
            <RefreshCw className="w-6 h-6 text-soc-muted animate-spin" />
          </div>
        ) : chains.length > 0 ? (
          <div className="space-y-4">
            {chains.map((chain) => (
              <AttackChainCard
                key={chain.id}
                chain={chain}
                isExpanded={expandedId === chain.id}
                onExpand={setExpandedId}
              />
            ))}
          </div>
        ) : (
          <div className="soc-card text-center py-16">
            <Shield className="w-16 h-16 mx-auto mb-4 text-soc-muted opacity-20" />
            <p className="text-lg font-medium text-soc-muted">No attack chains detected</p>
            <p className="text-sm text-soc-muted mt-1">
              Attack chains are automatically created when related alerts are correlated.
              Try running a demo simulation to see this in action.
            </p>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="soc-card">
        <h3 className="text-sm font-semibold text-white mb-3">Kill Chain Phase Legend</h3>
        <div className="flex flex-wrap gap-3">
          {Object.entries(PHASE_COLORS).map(([phase, colors]) => (
            <div key={phase} className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${colors.dot}`} />
              <span className={`text-xs ${colors.text}`}>{phase}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
