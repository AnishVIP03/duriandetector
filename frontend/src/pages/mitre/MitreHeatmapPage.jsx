/**
 * MITRE ATT&CK Heatmap Page.
 * Visualises tactics as columns and techniques as rows,
 * coloured by alert-count intensity. Clicking a technique
 * opens a detail panel with description, detection hints,
 * and recent alerts.
 */
import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Shield, Target, Info, X, RefreshCw, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';
import { mitreAPI } from '../../api/mitre';

/* ------------------------------------------------------------------ */
/*  Colour helpers                                                     */
/* ------------------------------------------------------------------ */
function intensityColor(count, maxCount) {
  if (count === 0) return 'rgba(30, 41, 59, 0.5)';          // dark / transparent
  const ratio = Math.min(count / Math.max(maxCount, 1), 1);
  if (ratio <= 0.25) return 'rgba(59, 130, 246, 0.6)';       // blue (low)
  if (ratio <= 0.50) return 'rgba(234, 179, 8, 0.7)';        // yellow (medium)
  if (ratio <= 0.75) return 'rgba(249, 115, 22, 0.8)';       // orange (high)
  return 'rgba(239, 68, 68, 0.9)';                            // red (critical)
}

function intensityBorder(count, maxCount) {
  if (count === 0) return 'border-soc-border/30';
  const ratio = Math.min(count / Math.max(maxCount, 1), 1);
  if (ratio <= 0.25) return 'border-blue-500/40';
  if (ratio <= 0.50) return 'border-yellow-500/40';
  if (ratio <= 0.75) return 'border-orange-500/40';
  return 'border-red-500/60';
}

/* ------------------------------------------------------------------ */
/*  Legend component                                                    */
/* ------------------------------------------------------------------ */
function Legend() {
  const items = [
    { label: 'None', color: 'rgba(30, 41, 59, 0.5)' },
    { label: 'Low', color: 'rgba(59, 130, 246, 0.6)' },
    { label: 'Medium', color: 'rgba(234, 179, 8, 0.7)' },
    { label: 'High', color: 'rgba(249, 115, 22, 0.8)' },
    { label: 'Critical', color: 'rgba(239, 68, 68, 0.9)' },
  ];

  return (
    <div className="flex items-center gap-4">
      <span className="text-xs text-soc-muted">Alert Intensity:</span>
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5">
          <div
            className="w-4 h-4 rounded-sm border border-white/10"
            style={{ backgroundColor: item.color }}
          />
          <span className="text-xs text-soc-muted">{item.label}</span>
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Technique detail panel                                             */
/* ------------------------------------------------------------------ */
function TechniqueDetailPanel({ techniqueId, onClose }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!techniqueId) return;
    setLoading(true);
    mitreAPI
      .getTechnique(techniqueId)
      .then(({ data }) => setDetail(data))
      .catch(() => toast.error('Failed to load technique details'))
      .finally(() => setLoading(false));
  }, [techniqueId]);

  if (!techniqueId) return null;

  return (
    <motion.div
      initial={{ opacity: 0, x: 40 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 40 }}
      className="fixed inset-y-0 right-0 w-full max-w-lg bg-soc-card border-l border-soc-border shadow-2xl z-50 overflow-y-auto"
    >
      {/* Close button */}
      <div className="sticky top-0 bg-soc-card border-b border-soc-border p-4 flex items-center justify-between z-10">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Target className="w-5 h-5 text-soc-accent" />
          Technique Details
        </h2>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-soc-surface text-soc-muted hover:text-white transition"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {loading ? (
        <div className="p-6 text-center text-soc-muted">Loading...</div>
      ) : detail ? (
        <div className="p-6 space-y-6">
          {/* Header */}
          <div>
            <span className="inline-block text-xs font-mono bg-soc-accent/10 text-soc-accent px-2 py-0.5 rounded mb-2">
              {detail.technique_id}
            </span>
            <h3 className="text-xl font-bold text-white">{detail.name}</h3>
            <p className="text-sm text-soc-muted mt-1">
              Tactic: {detail.tactic?.name}
            </p>
          </div>

          {/* Alert count */}
          <div className="bg-soc-surface rounded-lg p-4 flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-soc-accent/10 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-soc-accent" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{detail.alert_count}</p>
              <p className="text-xs text-soc-muted">Matching alerts</p>
            </div>
          </div>

          {/* Description */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-1.5">
              <BookOpen className="w-4 h-4 text-soc-accent" />
              Description
            </h4>
            <p className="text-sm text-soc-text leading-relaxed">
              {detail.description}
            </p>
          </div>

          {/* Detection hint */}
          {detail.detection_hint && (
            <div>
              <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-1.5">
                <Info className="w-4 h-4 text-yellow-400" />
                Detection Guidance
              </h4>
              <p className="text-sm text-soc-text leading-relaxed">
                {detail.detection_hint}
              </p>
            </div>
          )}

          {/* Mitigation */}
          {detail.mitigation && (
            <div>
              <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-1.5">
                <Shield className="w-4 h-4 text-green-400" />
                Recommendation
              </h4>
              <p className="text-sm text-soc-text leading-relaxed">
                {detail.mitigation}
              </p>
            </div>
          )}

          {/* Recent alerts */}
          {detail.recent_alerts && detail.recent_alerts.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-white mb-3">
                Recent Alerts ({detail.recent_alerts.length})
              </h4>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {detail.recent_alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="bg-soc-surface rounded-lg p-3 flex items-center gap-3"
                  >
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                        alert.severity === 'critical'
                          ? 'badge-critical'
                          : alert.severity === 'high'
                          ? 'badge-high'
                          : alert.severity === 'medium'
                          ? 'badge-medium'
                          : 'badge-low'
                      }`}
                    >
                      {alert.severity}
                    </span>
                    <span className="text-sm text-soc-text flex-1 truncate">
                      {alert.alert_type?.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs font-mono text-soc-muted">
                      {alert.src_ip}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="p-6 text-center text-soc-muted">
          No data available.
        </div>
      )}
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main page                                                          */
/* ------------------------------------------------------------------ */
export default function MitreHeatmapPage() {
  const [tactics, setTactics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTechnique, setSelectedTechnique] = useState(null);
  const [hoveredTechnique, setHoveredTechnique] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await mitreAPI.getHeatmap();
      setTactics(data);
    } catch {
      toast.error('Failed to load MITRE ATT&CK data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Compute global max alert count for colour normalisation
  const maxCount = tactics.reduce((max, tactic) => {
    const tacticMax = (tactic.techniques || []).reduce(
      (m, t) => Math.max(m, t.alert_count || 0),
      0
    );
    return Math.max(max, tacticMax);
  }, 1);

  // Compute the maximum number of techniques across all tactics (for row alignment)
  const maxTechniques = tactics.reduce(
    (m, t) => Math.max(m, (t.techniques || []).length),
    0
  );

  /* ---- Empty state ---- */
  if (!loading && tactics.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield className="w-6 h-6 text-soc-accent" />
            MITRE ATT&CK Coverage
          </h1>
          <p className="text-sm text-soc-muted mt-1">
            Framework-based threat coverage analysis
          </p>
        </div>
        <div className="soc-card flex flex-col items-center justify-center py-20">
          <Shield className="w-16 h-16 text-soc-muted/30 mb-4" />
          <p className="text-lg font-medium text-soc-muted">No MITRE data available</p>
          <p className="text-sm text-soc-muted/70 mt-1">
            Run <code className="bg-soc-surface px-1.5 py-0.5 rounded text-soc-accent text-xs font-mono">python manage.py seed_mitre</code> to populate the MITRE ATT&CK framework data.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield className="w-6 h-6 text-soc-accent" />
            MITRE ATT&CK Coverage
          </h1>
          <p className="text-sm text-soc-muted mt-1">
            Heatmap showing alert counts mapped to the MITRE ATT&CK framework
          </p>
        </div>
        <button
          onClick={fetchData}
          className="soc-btn-ghost !py-2 !px-3"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Legend */}
      <div className="soc-card !py-3 !px-4">
        <Legend />
      </div>

      {/* Heatmap matrix */}
      <div className="soc-card !p-0 overflow-x-auto">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-soc-muted">
            <RefreshCw className="w-5 h-5 animate-spin mr-2" />
            Loading MITRE ATT&CK data...
          </div>
        ) : (
          <div className="inline-flex min-w-full">
            {tactics.map((tactic) => (
              <div key={tactic.id} className="flex-shrink-0 w-48 border-r border-soc-border last:border-r-0">
                {/* Tactic header */}
                <div className="bg-soc-surface/50 border-b border-soc-border px-3 py-3 text-center sticky top-0 z-10">
                  <p className="text-xs font-mono text-soc-accent mb-1">{tactic.tactic_id}</p>
                  <p className="text-sm font-semibold text-white leading-tight">{tactic.name}</p>
                </div>

                {/* Technique cells */}
                <div className="p-2 space-y-2">
                  {(tactic.techniques || []).map((technique) => {
                    const count = technique.alert_count || 0;
                    const isHovered =
                      hoveredTechnique === technique.technique_id;

                    return (
                      <motion.button
                        key={technique.id}
                        whileHover={{ scale: 1.03 }}
                        whileTap={{ scale: 0.97 }}
                        onClick={() => setSelectedTechnique(technique.technique_id)}
                        onMouseEnter={() => setHoveredTechnique(technique.technique_id)}
                        onMouseLeave={() => setHoveredTechnique(null)}
                        className={`relative w-full text-left rounded-lg border p-2.5 transition-all cursor-pointer ${intensityBorder(count, maxCount)} ${
                          isHovered ? 'ring-1 ring-soc-accent/40' : ''
                        }`}
                        style={{ backgroundColor: intensityColor(count, maxCount) }}
                      >
                        <p className="text-[10px] font-mono text-white/70 mb-0.5">
                          {technique.technique_id}
                        </p>
                        <p className="text-xs font-medium text-white leading-tight truncate">
                          {technique.name}
                        </p>
                        {count > 0 && (
                          <span className="absolute top-1.5 right-1.5 text-[10px] font-bold text-white bg-black/30 rounded px-1">
                            {count}
                          </span>
                        )}

                        {/* Tooltip on hover */}
                        <AnimatePresence>
                          {isHovered && (
                            <motion.div
                              initial={{ opacity: 0, y: 6 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: 6 }}
                              className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-52 bg-soc-bg border border-soc-border rounded-lg p-2.5 shadow-xl z-30 pointer-events-none"
                            >
                              <p className="text-xs font-semibold text-white">{technique.name}</p>
                              <p className="text-[10px] font-mono text-soc-accent mt-0.5">
                                {technique.technique_id}
                              </p>
                              <p className="text-[10px] text-soc-muted mt-1">
                                Alert count: <span className="text-white font-medium">{count}</span>
                              </p>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </motion.button>
                    );
                  })}

                  {/* Empty rows for alignment */}
                  {Array.from({
                    length: maxTechniques - (tactic.techniques || []).length,
                  }).map((_, i) => (
                    <div key={`empty-${i}`} className="h-[58px]" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail panel */}
      <AnimatePresence>
        {selectedTechnique && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedTechnique(null)}
              className="fixed inset-0 bg-black/50 z-40"
            />
            <TechniqueDetailPanel
              techniqueId={selectedTechnique}
              onClose={() => setSelectedTechnique(null)}
            />
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
