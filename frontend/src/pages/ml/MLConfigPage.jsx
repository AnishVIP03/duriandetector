/**
 * ML Configuration page — US-18, US-19, US-20.
 * Configure ML model type, sensitivity, and view performance metrics.
 */
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Brain, Settings, Activity, RefreshCw, Loader2, BarChart3 } from 'lucide-react';
import toast from 'react-hot-toast';
import { mlAPI } from '../../api/alerts';

const MODEL_TYPES = [
  { value: 'random_forest', label: 'Random Forest', desc: 'Best general accuracy, interpretable feature importance' },
  { value: 'svm', label: 'Support Vector Machine', desc: 'Good for high-dimensional data, strong decision boundaries' },
  { value: 'isolation_forest', label: 'Isolation Forest', desc: 'Anomaly detection, no labels needed (unsupervised)' },
];

const SENSITIVITY_LEVELS = [
  { value: 'low', label: 'Low', desc: 'Threshold: 0.3 — Fewer alerts, may miss subtle attacks', color: 'text-green-400' },
  { value: 'medium', label: 'Medium', desc: 'Threshold: 0.5 — Balanced detection and false positive rate', color: 'text-yellow-400' },
  { value: 'high', label: 'High', desc: 'Threshold: 0.7 — More alerts, catches subtle anomalies', color: 'text-red-400' },
];

export default function MLConfigPage() {
  const [config, setConfig] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [training, setTraining] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [configRes, metricsRes] = await Promise.all([
        mlAPI.getConfig(),
        mlAPI.getMetrics(),
      ]);
      setConfig(configRes.data);
      setMetrics(metricsRes.data);
    } catch {
      // Config may not exist yet
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (field, value) => {
    setSaving(true);
    try {
      const { data } = await mlAPI.updateConfig({ [field]: value });
      setConfig(data);
      toast.success(`${field.replace('_', ' ')} updated`);
    } catch {
      toast.error('Failed to update config');
    } finally {
      setSaving(false);
    }
  };

  const handleTrain = async () => {
    setTraining(true);
    try {
      const { data } = await mlAPI.train();
      toast.success('Model training complete!');
      fetchData(); // Refresh metrics
    } catch {
      toast.error('Training failed');
    } finally {
      setTraining(false);
    }
  };

  if (loading) {
    return <div className="text-center py-20 text-soc-muted">Loading ML configuration...</div>;
  }

  const latestMetrics = metrics?.metrics?.[0] || metrics?.latest || null;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Brain className="w-6 h-6 text-soc-accent" /> ML Configuration
          </h1>
          <p className="text-sm text-soc-muted mt-1">Configure machine learning detection models</p>
        </div>
        <button
          onClick={handleTrain}
          disabled={training}
          className="soc-btn-primary !py-2 flex items-center gap-2"
        >
          {training ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          {training ? 'Training...' : 'Retrain Model'}
        </button>
      </div>

      {/* Model Selection — US-18 */}
      <div className="soc-card">
        <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <Settings className="w-4 h-4 text-soc-accent" /> Model Type
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {MODEL_TYPES.map((model) => (
            <button
              key={model.value}
              onClick={() => handleSave('model_type', model.value)}
              disabled={saving}
              className={`p-4 rounded-lg border text-left transition-all ${
                config?.model_type === model.value
                  ? 'bg-soc-accent/10 border-soc-accent/30 text-soc-accent'
                  : 'bg-soc-surface border-soc-border text-soc-muted hover:border-soc-accent/20'
              }`}
            >
              <p className="text-sm font-medium text-white mb-1">{model.label}</p>
              <p className="text-xs text-soc-muted">{model.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Sensitivity — US-19 */}
      <div className="soc-card">
        <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-soc-accent" /> Detection Sensitivity
        </h3>
        <div className="space-y-3">
          {SENSITIVITY_LEVELS.map((level) => (
            <button
              key={level.value}
              onClick={() => handleSave('sensitivity', level.value)}
              disabled={saving}
              className={`w-full p-4 rounded-lg border text-left transition-all flex items-center gap-4 ${
                config?.sensitivity === level.value
                  ? 'bg-soc-accent/10 border-soc-accent/30'
                  : 'bg-soc-surface border-soc-border hover:border-soc-accent/20'
              }`}
            >
              <div className={`w-3 h-3 rounded-full ${
                config?.sensitivity === level.value ? 'bg-soc-accent' : 'bg-soc-border'
              }`} />
              <div className="flex-1">
                <p className={`text-sm font-medium ${level.color}`}>{level.label}</p>
                <p className="text-xs text-soc-muted">{level.desc}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Metrics — US-20 */}
      <div className="soc-card">
        <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-soc-accent" /> Model Performance
        </h3>
        {latestMetrics ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Accuracy', value: latestMetrics.accuracy, color: 'text-green-400' },
              { label: 'Precision', value: latestMetrics.precision, color: 'text-blue-400' },
              { label: 'Recall', value: latestMetrics.recall, color: 'text-yellow-400' },
              { label: 'F1 Score', value: latestMetrics.f1_score, color: 'text-purple-400' },
            ].map((m) => (
              <motion.div
                key={m.label}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-soc-surface rounded-lg p-4 text-center"
              >
                <p className="text-xs text-soc-muted mb-2">{m.label}</p>
                <p className={`text-3xl font-bold ${m.color}`}>
                  {m.value != null ? (m.value * 100).toFixed(1) : '—'}%
                </p>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-soc-muted">
            <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-20" />
            <p>No metrics yet. Train the model to see performance data.</p>
          </div>
        )}
        {latestMetrics?.training_samples && (
          <p className="text-xs text-soc-muted mt-4">
            Trained on {latestMetrics.training_samples} samples
            {config?.trained_at && ` | Last trained: ${new Date(config.trained_at).toLocaleString()}`}
          </p>
        )}
      </div>

      {/* Feature Importance */}
      {metrics?.feature_importance && Object.keys(metrics.feature_importance).length > 0 && (
        <div className="soc-card">
          <h3 className="text-base font-semibold text-white mb-4">Feature Importance</h3>
          <div className="space-y-2">
            {Object.entries(metrics.feature_importance)
              .sort(([, a], [, b]) => b - a)
              .map(([feature, importance]) => (
                <div key={feature} className="flex items-center gap-3">
                  <span className="text-xs text-soc-muted w-36 truncate font-mono">{feature}</span>
                  <div className="flex-1 h-2 bg-soc-surface rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${importance * 100}%` }}
                      className="h-full bg-soc-accent rounded-full"
                    />
                  </div>
                  <span className="text-xs text-soc-text w-12 text-right">
                    {(importance * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
