/**
 * Log Ingestion Page — upload CSV/JSON files to create alerts.
 */
import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText, CheckCircle, XCircle, RefreshCw, Download } from 'lucide-react';
import { alertsAPI } from '../../api/alerts';
import toast from 'react-hot-toast';

const SAMPLE_CSV = `src_ip,dst_ip,src_port,dst_port,protocol,alert_type,severity,confidence_score,country
192.168.1.100,10.0.0.1,54321,80,TCP,port_scan,high,0.85,United States
203.0.113.50,10.0.0.2,12345,22,SSH,brute_force,critical,0.95,China
198.51.100.10,10.0.0.3,9999,443,HTTP,sql_injection,medium,0.72,Russia`;

const SAMPLE_JSON = JSON.stringify({
  records: [
    { src_ip: "192.168.1.100", dst_ip: "10.0.0.1", src_port: 54321, dst_port: 80, protocol: "TCP", alert_type: "port_scan", severity: "high", confidence_score: 0.85, country: "United States" },
    { src_ip: "203.0.113.50", dst_ip: "10.0.0.2", src_port: 12345, dst_port: 22, protocol: "SSH", alert_type: "brute_force", severity: "critical", confidence_score: 0.95, country: "China" },
  ]
}, null, 2);

export default function LogIngestionPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await alertsAPI.getUploadHistory();
      setHistory(res.data?.results || res.data || []);
    } catch {
      toast.error('Failed to load upload history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchHistory(); }, []);

  const handleUpload = async (file) => {
    if (!file) return;
    if (!file.name.endsWith('.csv') && !file.name.endsWith('.json')) {
      return toast.error('Only CSV and JSON files are supported');
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await alertsAPI.uploadLogFile(formData);
      const upload = res.data?.upload;
      toast.success(`Imported ${upload?.records_imported || 0} of ${upload?.records_total || 0} records`);
      fetchHistory();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    handleUpload(file);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    handleUpload(file);
    e.target.value = '';
  };

  const downloadSample = (content, filename) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Upload className="w-7 h-7 text-amber-400" />
            Log Ingestion
          </h1>
          <p className="text-soc-muted mt-1">Upload CSV or JSON log files to import alerts</p>
        </div>
        <button onClick={fetchHistory} className="p-2 rounded-lg bg-soc-surface text-soc-muted hover:text-white transition-colors">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Dropzone */}
      <motion.div
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
          dragActive
            ? 'border-amber-400 bg-amber-400/10'
            : 'border-soc-border hover:border-soc-muted bg-soc-card'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.json"
          onChange={handleFileSelect}
          className="hidden"
        />
        {uploading ? (
          <div className="space-y-3">
            <RefreshCw className="w-10 h-10 text-amber-400 mx-auto animate-spin" />
            <p className="text-white font-medium">Uploading and processing...</p>
          </div>
        ) : (
          <div className="space-y-3">
            <Upload className="w-10 h-10 text-soc-muted mx-auto" />
            <p className="text-white font-medium">
              {dragActive ? 'Drop your file here' : 'Drag & drop or click to upload'}
            </p>
            <div className="flex items-center justify-center gap-2">
              <span className="px-2 py-1 rounded bg-green-500/20 text-green-400 text-xs font-medium">CSV</span>
              <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 text-xs font-medium">JSON</span>
            </div>
            <p className="text-xs text-soc-muted">
              Required columns: src_ip, dst_ip, protocol, alert_type, severity, confidence_score
            </p>
          </div>
        )}
      </motion.div>

      {/* Sample Templates */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-soc-muted">Download templates:</span>
        <button
          onClick={() => downloadSample(SAMPLE_CSV, 'sample_alerts.csv')}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-500/10 text-green-400 hover:bg-green-500/20 text-sm transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          Sample CSV
        </button>
        <button
          onClick={() => downloadSample(SAMPLE_JSON, 'sample_alerts.json')}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 text-sm transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          Sample JSON
        </button>
      </div>

      {/* Upload History */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3">Upload History</h2>
        <div className="bg-soc-card border border-soc-border rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-soc-border">
                <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">File</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Format</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Records</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Status</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Uploaded By</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-soc-muted">Date</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="6" className="px-4 py-8 text-center text-soc-muted">Loading...</td></tr>
              ) : history.length === 0 ? (
                <tr><td colSpan="6" className="px-4 py-8 text-center text-soc-muted">No uploads yet. Upload a file above.</td></tr>
              ) : (
                history.map((upload) => (
                  <motion.tr
                    key={upload.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="border-b border-soc-border/50 hover:bg-soc-surface/50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-soc-muted" />
                        <span className="text-sm text-white">{upload.file_name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        upload.file_format === 'csv' ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'
                      }`}>
                        {upload.file_format?.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className="text-green-400">{upload.records_imported}</span>
                      <span className="text-soc-muted"> / {upload.records_total}</span>
                      {upload.records_failed > 0 && (
                        <span className="text-red-400 ml-1">({upload.records_failed} failed)</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`flex items-center gap-1 text-xs font-medium ${
                        upload.status === 'completed' ? 'text-green-400' :
                        upload.status === 'failed' ? 'text-red-400' :
                        'text-yellow-400'
                      }`}>
                        {upload.status === 'completed' ? <CheckCircle className="w-3.5 h-3.5" /> :
                         upload.status === 'failed' ? <XCircle className="w-3.5 h-3.5" /> : null}
                        {upload.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-soc-muted">{upload.uploaded_by_email}</td>
                    <td className="px-4 py-3 text-sm text-soc-muted">
                      {new Date(upload.uploaded_at).toLocaleString()}
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
