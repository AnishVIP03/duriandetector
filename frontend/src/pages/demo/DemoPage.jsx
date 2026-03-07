/**
 * Demo/Simulation Control Page.
 * Allows users to generate simulated network attack data for demonstration,
 * view simulation status, and clear demo data.
 */
import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play, Trash2, AlertTriangle, ExternalLink, Zap,
  CheckCircle, XCircle, RefreshCw, Shield, BarChart3,
  Globe, Activity
} from 'lucide-react';
import toast from 'react-hot-toast';
import { demoAPI } from '../../api/attackChains';

const SEVERITY_COLORS = {
  low: 'bg-blue-500',
  medium: 'bg-yellow-500',
  high: 'bg-orange-500',
  critical: 'bg-red-500',
};

// ---------------------------------------------------------------------------
// Summary Card after demo runs
// ---------------------------------------------------------------------------
function DemoSummary({ summary }) {
  if (!summary) return null;

  const totalAlerts = summary.total_alerts;
  const severityEntries = Object.entries(summary.severity_summary || {});
  const typeEntries = Object.entries(summary.type_summary || {});

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="soc-card"
    >
      <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
        <BarChart3 className="w-5 h-5 text-soc-accent" />
        Simulation Summary
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Total alerts */}
        <div className="text-center p-6 bg-soc-surface rounded-xl">
          <p className="text-4xl font-bold text-soc-accent">{totalAlerts}</p>
          <p className="text-sm text-soc-muted mt-1">Alerts Created</p>
        </div>

        {/* Severity breakdown */}
        <div>
          <p className="text-xs text-soc-muted uppercase tracking-wider font-semibold mb-3">
            Severity Breakdown
          </p>
          <div className="space-y-2">
            {severityEntries.map(([sev, count]) => (
              <div key={sev} className="flex items-center gap-3">
                <span className="text-xs text-soc-muted w-16 capitalize">{sev}</span>
                <div className="flex-1 h-2 bg-soc-surface rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${totalAlerts > 0 ? (count / totalAlerts) * 100 : 0}%` }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className={`h-full rounded-full ${SEVERITY_COLORS[sev] || 'bg-soc-muted'}`}
                  />
                </div>
                <span className="text-xs text-soc-text w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Alert types */}
      {typeEntries.length > 0 && (
        <div className="mt-6 pt-4 border-t border-soc-border">
          <p className="text-xs text-soc-muted uppercase tracking-wider font-semibold mb-3">
            Attack Types Generated
          </p>
          <div className="flex flex-wrap gap-2">
            {typeEntries.map(([type, count]) => (
              <span
                key={type}
                className="text-xs bg-soc-accent/10 text-soc-accent border border-soc-accent/20 px-2.5 py-1 rounded-full"
              >
                {type.replace(/_/g, ' ')} ({count})
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Navigation links */}
      <div className="mt-6 pt-4 border-t border-soc-border">
        <p className="text-xs text-soc-muted uppercase tracking-wider font-semibold mb-3">
          Explore Demo Data
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Link
            to="/dashboard"
            className="flex items-center gap-2 bg-soc-surface rounded-lg px-4 py-3 text-sm text-soc-text hover:text-white hover:bg-soc-accent/10 transition-colors"
          >
            <Activity className="w-4 h-4 text-soc-accent" />
            Dashboard
            <ExternalLink className="w-3 h-3 ml-auto text-soc-muted" />
          </Link>
          <Link
            to="/alerts"
            className="flex items-center gap-2 bg-soc-surface rounded-lg px-4 py-3 text-sm text-soc-text hover:text-white hover:bg-soc-accent/10 transition-colors"
          >
            <AlertTriangle className="w-4 h-4 text-orange-400" />
            Alerts
            <ExternalLink className="w-3 h-3 ml-auto text-soc-muted" />
          </Link>
          <Link
            to="/geoip"
            className="flex items-center gap-2 bg-soc-surface rounded-lg px-4 py-3 text-sm text-soc-text hover:text-white hover:bg-soc-accent/10 transition-colors"
          >
            <Globe className="w-4 h-4 text-cyan-400" />
            GeoIP Map
            <ExternalLink className="w-3 h-3 ml-auto text-soc-muted" />
          </Link>
          <Link
            to="/attack-chains"
            className="flex items-center gap-2 bg-soc-surface rounded-lg px-4 py-3 text-sm text-soc-text hover:text-white hover:bg-soc-accent/10 transition-colors"
          >
            <Zap className="w-4 h-4 text-yellow-400" />
            Kill Chain
            <ExternalLink className="w-3 h-3 ml-auto text-soc-muted" />
          </Link>
        </div>
      </div>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------
export default function DemoPage() {
  const [demoStatus, setDemoStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [summary, setSummary] = useState(null);
  const [confirmClear, setConfirmClear] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const { data } = await demoAPI.status();
      setDemoStatus(data);
    } catch {
      // API may not be available
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleStartDemo = async () => {
    setRunning(true);
    setSummary(null);
    try {
      const { data } = await demoAPI.start();
      setSummary(data);
      toast.success(`Demo started! ${data.total_alerts} alerts created.`);
      fetchStatus();
    } catch (err) {
      const msg = err.response?.data?.error || 'Failed to start demo';
      toast.error(msg);
    } finally {
      setRunning(false);
    }
  };

  const handleClearDemo = async () => {
    setClearing(true);
    try {
      const { data } = await demoAPI.clear();
      toast.success(data.message);
      setSummary(null);
      setConfirmClear(false);
      fetchStatus();
    } catch {
      toast.error('Failed to clear demo data');
    } finally {
      setClearing(false);
    }
  };

  const hasDemo = demoStatus?.has_demo_data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Zap className="w-6 h-6 text-soc-accent" />
            Demo Simulation
          </h1>
          <p className="text-sm text-soc-muted mt-1">
            Generate simulated network attack data for demonstration
          </p>
        </div>
      </div>

      {/* Warning banner */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-start gap-3 bg-yellow-500/10 border border-yellow-500/30 rounded-xl px-4 py-3"
      >
        <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0 mt-0.5" />
        <div>
          <p className="text-sm text-yellow-200 font-medium">Simulation Mode</p>
          <p className="text-xs text-yellow-200/70 mt-0.5">
            This creates simulated attack data in your environment for demonstration purposes.
            All generated alerts are tagged and can be safely removed at any time.
          </p>
        </div>
      </motion.div>

      {/* Status indicator */}
      <div className="soc-card flex items-center gap-4">
        <div className={`w-3 h-3 rounded-full ${
          loading ? 'bg-soc-muted animate-pulse' :
          hasDemo ? 'bg-green-500' :
          'bg-soc-muted'
        }`} />
        <div className="flex-1">
          <p className="text-sm text-white font-medium">
            {loading ? 'Checking status...' :
              hasDemo ? 'Demo data present' :
              'No demo data'
            }
          </p>
          {hasDemo && demoStatus && (
            <p className="text-xs text-soc-muted mt-0.5">
              {demoStatus.alert_count} alerts, {demoStatus.chain_count} attack chains
            </p>
          )}
        </div>
        {hasDemo && (
          <span className="flex items-center gap-1.5 text-xs text-green-400 bg-green-500/10 border border-green-500/20 px-2.5 py-1 rounded-full">
            <CheckCircle className="w-3.5 h-3.5" />
            Active
          </span>
        )}
      </div>

      {/* Main action area */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Start Demo */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="soc-card flex flex-col items-center justify-center py-12"
        >
          <div className="relative mb-6">
            <motion.div
              animate={running ? { scale: [1, 1.2, 1], opacity: [0.5, 1, 0.5] } : {}}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="absolute inset-0 bg-soc-accent/20 rounded-full blur-xl"
            />
            <button
              onClick={handleStartDemo}
              disabled={running || hasDemo}
              className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-all ${
                running
                  ? 'bg-soc-accent/30 cursor-wait'
                  : hasDemo
                  ? 'bg-soc-surface cursor-not-allowed opacity-50'
                  : 'bg-soc-accent/20 hover:bg-soc-accent/30 hover:scale-105 cursor-pointer'
              }`}
            >
              {running ? (
                <RefreshCw className="w-10 h-10 text-soc-accent animate-spin" />
              ) : (
                <Play className="w-10 h-10 text-soc-accent ml-1" />
              )}
            </button>
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">
            {running ? 'Generating Simulation...' : 'Start Demo'}
          </h3>
          <p className="text-sm text-soc-muted text-center max-w-sm">
            {hasDemo
              ? 'Demo data already exists. Clear it before running a new simulation.'
              : 'Generate 30-50 realistic network security alerts with GeoIP data, MITRE mappings, and attack chains spread across the last 24 hours.'
            }
          </p>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {['Port Scan', 'Brute Force', 'DoS', 'SQL Injection', 'XSS', 'DNS Tunneling'].map((type) => (
              <span key={type} className="text-xs bg-soc-surface text-soc-muted px-2 py-1 rounded">
                {type}
              </span>
            ))}
          </div>
        </motion.div>

        {/* Clear Demo */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="soc-card flex flex-col items-center justify-center py-12"
        >
          <div className="mb-6">
            <div className={`w-24 h-24 rounded-full flex items-center justify-center ${
              hasDemo
                ? 'bg-red-500/10 hover:bg-red-500/20 cursor-pointer transition-all'
                : 'bg-soc-surface opacity-50'
            }`}>
              <Trash2 className={`w-10 h-10 ${hasDemo ? 'text-red-400' : 'text-soc-muted'}`} />
            </div>
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Clear Demo Data</h3>
          <p className="text-sm text-soc-muted text-center max-w-sm mb-4">
            {hasDemo
              ? 'Remove all simulated alerts and attack chains from your environment.'
              : 'No demo data to clear. Start a simulation first.'
            }
          </p>

          <AnimatePresence>
            {confirmClear ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="flex items-center gap-3"
              >
                <p className="text-xs text-red-400">Are you sure?</p>
                <button
                  onClick={handleClearDemo}
                  disabled={clearing}
                  className="soc-btn-danger !py-1.5 !px-4 text-xs flex items-center gap-1.5"
                >
                  {clearing ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Trash2 className="w-3.5 h-3.5" />
                  )}
                  Confirm Delete
                </button>
                <button
                  onClick={() => setConfirmClear(false)}
                  className="soc-btn-ghost !py-1.5 !px-4 text-xs flex items-center gap-1.5"
                >
                  <XCircle className="w-3.5 h-3.5" />
                  Cancel
                </button>
              </motion.div>
            ) : (
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onClick={() => setConfirmClear(true)}
                disabled={!hasDemo}
                className="soc-btn-danger !py-2 !px-6 flex items-center gap-2 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <Trash2 className="w-4 h-4" />
                Clear All Demo Data
              </motion.button>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Demo summary (shown after simulation runs) */}
      {summary && <DemoSummary summary={summary} />}

      {/* What the demo creates */}
      <div className="soc-card">
        <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-soc-accent" />
          What Does the Demo Simulate?
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            {
              title: 'Network Attacks',
              desc: 'Port scans, brute force attempts, DoS attacks, SQL injections, and protocol anomalies.',
              icon: AlertTriangle,
              color: 'text-red-400',
            },
            {
              title: 'GeoIP Data',
              desc: 'Realistic source IPs from 12+ countries with latitude/longitude coordinates for map visualization.',
              icon: Globe,
              color: 'text-cyan-400',
            },
            {
              title: 'MITRE ATT&CK',
              desc: 'Each alert is mapped to MITRE ATT&CK tactics and techniques for threat classification.',
              icon: Shield,
              color: 'text-purple-400',
            },
            {
              title: 'Attack Chains',
              desc: 'Multi-stage attack sequences showing how alerts correlate into kill chain patterns.',
              icon: Zap,
              color: 'text-yellow-400',
            },
            {
              title: 'Severity Levels',
              desc: 'Alerts across all severity levels (low, medium, high, critical) with confidence scores.',
              icon: BarChart3,
              color: 'text-orange-400',
            },
            {
              title: 'ML Model Tags',
              desc: 'Simulated ML model attributions showing which detection models flagged each alert.',
              icon: Activity,
              color: 'text-green-400',
            },
          ].map((item) => (
            <div key={item.title} className="bg-soc-surface rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <item.icon className={`w-4 h-4 ${item.color}`} />
                <h4 className="text-sm font-medium text-white">{item.title}</h4>
              </div>
              <p className="text-xs text-soc-muted leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
