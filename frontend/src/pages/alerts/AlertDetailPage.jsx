/**
 * Alert Detail page — US-08.
 * Shows full alert information including raw payload, GeoIP, MITRE mapping.
 */
import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft, Shield, MapPin, Ban, Unlock,
  Clock, Server, Globe, AlertTriangle, BookOpen
} from 'lucide-react';
import toast from 'react-hot-toast';
import { alertsAPI } from '../../api/alerts';

const SEVERITY_COLORS = {
  low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
};

function InfoRow({ label, value, mono = false }) {
  return (
    <div className="flex items-start justify-between py-2.5 border-b border-soc-border last:border-0">
      <span className="text-sm text-soc-muted">{label}</span>
      <span className={`text-sm text-soc-text text-right ${mono ? 'font-mono' : ''}`}>
        {value || '—'}
      </span>
    </div>
  );
}

export default function AlertDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [alert, setAlert] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAlert = async () => {
      try {
        const { data } = await alertsAPI.getDetail(id);
        setAlert(data);
      } catch {
        toast.error('Alert not found');
        navigate('/alerts');
      } finally {
        setLoading(false);
      }
    };
    fetchAlert();
  }, [id, navigate]);

  const handleBlock = async () => {
    try {
      await alertsAPI.blockIP(alert.id, 'Blocked from alert detail view');
      toast.success(`IP ${alert.src_ip} blocked`);
      setAlert({ ...alert, is_blocked: true });
    } catch {
      toast.error('Failed to block IP');
    }
  };

  const handleUnblock = async () => {
    try {
      await alertsAPI.unblockIP(alert.id);
      toast.success(`IP ${alert.src_ip} unblocked`);
      setAlert({ ...alert, is_blocked: false });
    } catch {
      toast.error('Failed to unblock IP');
    }
  };

  if (loading) {
    return (
      <div className="text-center py-20 text-soc-muted">Loading alert details...</div>
    );
  }

  if (!alert) return null;

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Back link */}
      <Link to="/alerts" className="inline-flex items-center gap-1 text-sm text-soc-muted hover:text-soc-accent">
        <ArrowLeft className="w-4 h-4" /> Back to alerts
      </Link>

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-start justify-between"
      >
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className={`px-3 py-1 rounded-lg text-sm font-medium border ${SEVERITY_COLORS[alert.severity]}`}>
              {alert.severity.toUpperCase()}
            </span>
            <h1 className="text-2xl font-bold text-white">
              {alert.alert_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
            </h1>
          </div>
          <p className="text-sm text-soc-muted flex items-center gap-2">
            <Clock className="w-4 h-4" />
            {new Date(alert.timestamp).toLocaleString()}
          </p>
        </div>

        <div className="flex gap-2">
          {alert.is_blocked ? (
            <button onClick={handleUnblock} className="soc-btn-ghost !py-2 flex items-center gap-2">
              <Unlock className="w-4 h-4" /> Unblock IP
            </button>
          ) : (
            <button onClick={handleBlock} className="soc-btn-danger !py-2 flex items-center gap-2">
              <Ban className="w-4 h-4" /> Block IP
            </button>
          )}
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Network Info */}
        <div className="soc-card">
          <h3 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
            <Server className="w-4 h-4 text-soc-accent" />
            Network Information
          </h3>
          <InfoRow label="Source IP" value={alert.src_ip} mono />
          <InfoRow label="Destination IP" value={alert.dst_ip} mono />
          <InfoRow label="Source Port" value={alert.src_port} mono />
          <InfoRow label="Destination Port" value={alert.dst_port} mono />
          <InfoRow label="Protocol" value={alert.protocol} />
          <InfoRow label="ML Model" value={alert.ml_model_used} />
          <InfoRow label="Confidence" value={`${(alert.confidence_score * 100).toFixed(1)}%`} />
        </div>

        {/* GeoIP Info */}
        <div className="soc-card">
          <h3 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
            <Globe className="w-4 h-4 text-soc-accent" />
            Geographic Information
          </h3>
          <InfoRow label="Country" value={alert.country} />
          <InfoRow label="City" value={alert.city} />
          <InfoRow label="Latitude" value={alert.latitude?.toFixed(4)} mono />
          <InfoRow label="Longitude" value={alert.longitude?.toFixed(4)} mono />
          <InfoRow label="Blocked" value={alert.is_blocked ? 'Yes' : 'No'} />
          {alert.blocked_by_email && (
            <InfoRow label="Blocked By" value={alert.blocked_by_email} />
          )}
        </div>

        {/* MITRE ATT&CK */}
        {(alert.mitre_tactic || alert.mitre_technique_id) && (
          <div className="soc-card">
            <h3 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-soc-accent" />
              MITRE ATT&CK Mapping
            </h3>
            <InfoRow label="Tactic" value={alert.mitre_tactic} />
            <InfoRow label="Technique ID" value={alert.mitre_technique_id} />
            <div className="mt-3 p-3 bg-soc-accent/5 border border-soc-accent/20 rounded-lg">
              <p className="text-xs text-soc-accent">
                This alert maps to the MITRE ATT&CK framework.
                View the full technique reference for detection and mitigation guidance.
              </p>
            </div>
          </div>
        )}

        {/* Raw Payload */}
        {alert.raw_payload && (
          <div className="soc-card lg:col-span-2">
            <h3 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-soc-warning" />
              Raw Payload
            </h3>
            <pre className="bg-soc-bg border border-soc-border rounded-lg p-4 text-xs font-mono text-soc-muted overflow-x-auto whitespace-pre-wrap break-all">
              {alert.raw_payload}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
