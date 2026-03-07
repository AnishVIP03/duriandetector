/**
 * Reports page — US-22, US-23.
 * Generate and export security reports.
 */
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText, Plus, Download, RefreshCw, Eye, Calendar,
  BarChart3, Loader2
} from 'lucide-react';
import toast from 'react-hot-toast';
import { reportsAPI } from '../../api/incidents';

const REPORT_TYPES = {
  summary: { label: 'Summary Report', desc: 'High-level overview of alerts and incidents' },
  detailed: { label: 'Detailed Report', desc: 'Comprehensive analysis with all data points' },
  incident: { label: 'Incident Report', desc: 'Focus on incidents and their resolutions' },
  threat: { label: 'Threat Report', desc: 'Threat intelligence analysis and correlations' },
};

export default function ReportsPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showGenerate, setShowGenerate] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [form, setForm] = useState({
    title: '',
    report_type: 'summary',
    date_from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
    date_to: new Date().toISOString().slice(0, 16),
  });

  useEffect(() => { fetchReports(); }, []);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const { data } = await reportsAPI.getAll();
      setReports(data.results || data);
    } catch { /* API may not be ready */ }
    finally { setLoading(false); }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    setGenerating(true);
    try {
      const { data } = await reportsAPI.generate(form);
      toast.success('Report generated!');
      setShowGenerate(false);
      fetchReports();
      setSelectedReport(data);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const handleExportPDF = async (reportId) => {
    try {
      const response = await reportsAPI.exportPDF(reportId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${reportId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('PDF downloaded');
    } catch {
      toast.error('PDF export failed. Is WeasyPrint installed?');
    }
  };

  const handleViewReport = async (report) => {
    try {
      const { data } = await reportsAPI.getDetail(report.id);
      setSelectedReport(data);
    } catch {
      setSelectedReport(report);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FileText className="w-6 h-6 text-soc-accent" /> Reports
          </h1>
          <p className="text-sm text-soc-muted mt-1">Generate and export security analysis reports</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchReports} className="soc-btn-ghost !py-2 !px-3">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button onClick={() => setShowGenerate(true)} className="soc-btn-primary !py-2 flex items-center gap-2">
            <Plus className="w-4 h-4" /> Generate Report
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Report list */}
        <div className="space-y-3">
          {loading ? (
            <div className="text-center py-12 text-soc-muted">Loading...</div>
          ) : reports.length === 0 ? (
            <div className="soc-card text-center py-12 text-soc-muted">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-20" />
              <p>No reports generated yet</p>
            </div>
          ) : reports.map((report) => (
            <motion.div
              key={report.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className={`soc-card !p-4 cursor-pointer hover:soc-glow transition-all ${
                selectedReport?.id === report.id ? 'soc-glow' : ''
              }`}
              onClick={() => handleViewReport(report)}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-soc-accent bg-soc-accent/10 px-2 py-0.5 rounded">
                  {report.report_type}
                </span>
                {report.has_pdf && (
                  <button
                    onClick={(e) => { e.stopPropagation(); handleExportPDF(report.id); }}
                    className="text-soc-muted hover:text-soc-accent"
                    title="Download PDF"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                )}
              </div>
              <h3 className="text-sm font-semibold text-white truncate">{report.title}</h3>
              <p className="text-xs text-soc-muted mt-1 flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {new Date(report.created_at).toLocaleDateString()}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Report detail */}
        <div className="lg:col-span-2">
          {selectedReport ? (
            <div className="soc-card space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-white">{selectedReport.title}</h2>
                  <p className="text-sm text-soc-muted">
                    {REPORT_TYPES[selectedReport.report_type]?.label} |{' '}
                    {new Date(selectedReport.created_at).toLocaleString()}
                  </p>
                </div>
                <button
                  onClick={() => handleExportPDF(selectedReport.id)}
                  className="soc-btn-primary !py-2 flex items-center gap-2"
                >
                  <Download className="w-4 h-4" /> Export PDF
                </button>
              </div>

              {/* Report content */}
              {selectedReport.content && (
                <div className="space-y-4">
                  {/* Stats cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      { label: 'Total Alerts', value: selectedReport.content.total_alerts },
                      { label: 'Critical', value: selectedReport.content.severity_breakdown?.critical },
                      { label: 'Blocked IPs', value: selectedReport.content.blocked_ips },
                      { label: 'Top Source', value: selectedReport.content.top_source_ips?.[0]?.src_ip },
                    ].map((stat) => (
                      <div key={stat.label} className="bg-soc-surface rounded-lg p-3">
                        <p className="text-xs text-soc-muted">{stat.label}</p>
                        <p className="text-lg font-bold text-white">{stat.value ?? '—'}</p>
                      </div>
                    ))}
                  </div>

                  {/* Severity breakdown */}
                  {selectedReport.content.severity_breakdown && (
                    <div className="bg-soc-surface rounded-lg p-4">
                      <h3 className="text-sm font-semibold text-white mb-3">Severity Breakdown</h3>
                      <div className="space-y-2">
                        {Object.entries(selectedReport.content.severity_breakdown).map(([sev, count]) => (
                          <div key={sev} className="flex items-center gap-3">
                            <span className="text-xs text-soc-muted w-16 capitalize">{sev}</span>
                            <div className="flex-1 h-2 bg-soc-bg rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  sev === 'critical' ? 'bg-red-500' :
                                  sev === 'high' ? 'bg-orange-500' :
                                  sev === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
                                }`}
                                style={{ width: `${(count / Math.max(selectedReport.content.total_alerts, 1)) * 100}%` }}
                              />
                            </div>
                            <span className="text-xs text-soc-text w-8 text-right">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Top IPs */}
                  {selectedReport.content.top_source_ips?.length > 0 && (
                    <div className="bg-soc-surface rounded-lg p-4">
                      <h3 className="text-sm font-semibold text-white mb-3">Top Source IPs</h3>
                      <div className="space-y-2">
                        {selectedReport.content.top_source_ips.map((ip) => (
                          <div key={ip.src_ip} className="flex items-center justify-between">
                            <span className="text-sm font-mono text-soc-text">{ip.src_ip}</span>
                            <span className="text-sm text-soc-accent">{ip.count} alerts</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="soc-card text-center py-20 text-soc-muted">
              <BarChart3 className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-lg">Select a report to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Generate modal */}
      <AnimatePresence>
        {showGenerate && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
            onClick={() => setShowGenerate(false)}
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              className="soc-card w-full max-w-lg"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-xl font-bold text-white mb-4">Generate Report</h2>
              <form onSubmit={handleGenerate} className="space-y-4">
                <div>
                  <label className="text-sm text-soc-muted mb-1 block">Title</label>
                  <input
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    className="soc-input"
                    placeholder="Weekly Security Report"
                    required
                  />
                </div>
                <div>
                  <label className="text-sm text-soc-muted mb-1 block">Report Type</label>
                  <select value={form.report_type} onChange={(e) => setForm({ ...form, report_type: e.target.value })} className="soc-input">
                    {Object.entries(REPORT_TYPES).map(([k, v]) => (
                      <option key={k} value={k}>{v.label}</option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-sm text-soc-muted mb-1 block">From</label>
                    <input type="datetime-local" value={form.date_from} onChange={(e) => setForm({ ...form, date_from: e.target.value })} className="soc-input" />
                  </div>
                  <div>
                    <label className="text-sm text-soc-muted mb-1 block">To</label>
                    <input type="datetime-local" value={form.date_to} onChange={(e) => setForm({ ...form, date_to: e.target.value })} className="soc-input" />
                  </div>
                </div>
                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setShowGenerate(false)} className="soc-btn-ghost flex-1">Cancel</button>
                  <button type="submit" disabled={generating} className="soc-btn-primary flex-1 flex items-center justify-center gap-2">
                    {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                    {generating ? 'Generating...' : 'Generate'}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
