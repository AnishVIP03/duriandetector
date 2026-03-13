/**
 * Custom Visualization / Analytics Page — Recharts-powered configurable charts.
 */
import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, RefreshCw } from 'lucide-react';
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar, AreaChart, Area,
  PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts';
import { alertsAPI } from '../../api/alerts';
import toast from 'react-hot-toast';

const CHART_TYPES = ['Line', 'Bar', 'Area', 'Pie'];
const GROUP_OPTIONS = [
  { value: 'hour', label: 'Hourly' },
  { value: 'day', label: 'Daily' },
  { value: 'week', label: 'Weekly' },
];
const BREAKDOWN_OPTIONS = [
  { value: '', label: 'None' },
  { value: 'severity', label: 'Severity' },
  { value: 'alert_type', label: 'Alert Type' },
  { value: 'protocol', label: 'Protocol' },
  { value: 'country', label: 'Country' },
];
const COLORS = ['#f97316', '#3b82f6', '#ef4444', '#22c55e', '#a855f7', '#eab308', '#06b6d4', '#ec4899'];
const PRESETS = [
  { label: 'Alerts by Severity (7d)', group_by: 'day', breakdown_by: 'severity', days: 7 },
  { label: 'Hourly Trend (24h)', group_by: 'hour', breakdown_by: '', days: 1 },
  { label: 'Top Protocols (30d)', group_by: 'day', breakdown_by: 'protocol', days: 30 },
  { label: 'Alert Types (7d)', group_by: 'day', breakdown_by: 'alert_type', days: 7 },
];

export default function CustomVisualizationPage() {
  const [chartType, setChartType] = useState('Bar');
  const [groupBy, setGroupBy] = useState('day');
  const [breakdownBy, setBreakdownBy] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const params = { group_by: groupBy };
      if (breakdownBy) params.breakdown_by = breakdownBy;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await alertsAPI.getAnalytics(params);

      const rawData = res.data?.data || [];

      if (breakdownBy) {
        // Pivot breakdown data into {period, value1: count, value2: count, ...}
        const grouped = {};
        rawData.forEach(row => {
          const key = row.period;
          if (!grouped[key]) grouped[key] = { period: formatPeriod(key, groupBy) };
          grouped[key][row[breakdownBy] || 'Unknown'] = row.count;
        });
        setData(Object.values(grouped));
      } else {
        setData(rawData.map(row => ({
          period: formatPeriod(row.period, groupBy),
          count: row.count,
          avg_confidence: row.avg_confidence,
        })));
      }
    } catch {
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }, [groupBy, breakdownBy, dateFrom, dateTo]);

  useEffect(() => { fetchAnalytics(); }, [fetchAnalytics]);

  const formatPeriod = (isoStr, grp) => {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    if (grp === 'hour') return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    if (grp === 'week') return `Wk ${d.toLocaleDateString([], { month: 'short', day: 'numeric' })}`;
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  const applyPreset = (preset) => {
    setGroupBy(preset.group_by);
    setBreakdownBy(preset.breakdown_by);
    const now = new Date();
    const from = new Date(now);
    from.setDate(from.getDate() - preset.days);
    setDateFrom(from.toISOString().split('T')[0]);
    setDateTo(now.toISOString().split('T')[0]);
  };

  // Get unique breakdown keys for multi-line/multi-bar charts
  const breakdownKeys = breakdownBy
    ? [...new Set(data.flatMap(d => Object.keys(d).filter(k => k !== 'period')))]
    : ['count'];

  const renderChart = () => {
    if (data.length === 0) {
      return (
        <div className="flex items-center justify-center h-[400px] text-soc-muted">
          {loading ? 'Loading...' : 'No data available for selected filters'}
        </div>
      );
    }

    if (chartType === 'Pie') {
      // For pie, aggregate total counts per breakdown key
      const pieData = breakdownKeys.map((key, i) => ({
        name: key,
        value: data.reduce((sum, d) => sum + (d[key] || 0), 0),
        fill: COLORS[i % COLORS.length],
      })).filter(d => d.value > 0);

      return (
        <ResponsiveContainer width="100%" height={400}>
          <PieChart>
            <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={150} label>
              {pieData.map((entry, i) => (
                <Cell key={`cell-${i}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ background: '#1a1f2e', border: '1px solid #2a3040', color: '#fff' }} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      );
    }

    const ChartComponent = chartType === 'Line' ? LineChart : chartType === 'Area' ? AreaChart : BarChart;
    const DataComponent = chartType === 'Line' ? Line : chartType === 'Area' ? Area : Bar;

    return (
      <ResponsiveContainer width="100%" height={400}>
        <ChartComponent data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a3040" />
          <XAxis dataKey="period" stroke="#6b7280" tick={{ fontSize: 11 }} />
          <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} />
          <Tooltip contentStyle={{ background: '#1a1f2e', border: '1px solid #2a3040', color: '#fff' }} />
          <Legend />
          {breakdownKeys.map((key, i) => (
            <DataComponent
              key={key}
              type="monotone"
              dataKey={key}
              stroke={COLORS[i % COLORS.length]}
              fill={COLORS[i % COLORS.length]}
              fillOpacity={chartType === 'Area' ? 0.3 : 0.8}
              name={key}
            />
          ))}
        </ChartComponent>
      </ResponsiveContainer>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <BarChart3 className="w-7 h-7 text-purple-400" />
            Custom Visualization
          </h1>
          <p className="text-soc-muted mt-1">Configurable analytics and charts</p>
        </div>
        <button onClick={fetchAnalytics} className="p-2 rounded-lg bg-soc-surface text-soc-muted hover:text-white transition-colors">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Presets */}
      <div className="flex flex-wrap gap-2">
        {PRESETS.map((preset) => (
          <button
            key={preset.label}
            onClick={() => applyPreset(preset)}
            className="px-3 py-1.5 rounded-lg bg-soc-surface border border-soc-border text-sm text-soc-muted hover:text-white hover:border-purple-400/50 transition-colors"
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Config Panel */}
      <div className="bg-soc-card border border-soc-border rounded-xl p-4">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <label className="text-xs text-soc-muted mb-1 block">Chart Type</label>
            <select
              value={chartType}
              onChange={(e) => setChartType(e.target.value)}
              className="w-full px-3 py-2 bg-soc-surface border border-soc-border rounded-lg text-white text-sm focus:outline-none focus:border-purple-400"
            >
              {CHART_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-soc-muted mb-1 block">Group By</label>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value)}
              className="w-full px-3 py-2 bg-soc-surface border border-soc-border rounded-lg text-white text-sm focus:outline-none focus:border-purple-400"
            >
              {GROUP_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-soc-muted mb-1 block">Breakdown</label>
            <select
              value={breakdownBy}
              onChange={(e) => setBreakdownBy(e.target.value)}
              className="w-full px-3 py-2 bg-soc-surface border border-soc-border rounded-lg text-white text-sm focus:outline-none focus:border-purple-400"
            >
              {BREAKDOWN_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-soc-muted mb-1 block">From</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-3 py-2 bg-soc-surface border border-soc-border rounded-lg text-white text-sm focus:outline-none focus:border-purple-400"
            />
          </div>
          <div>
            <label className="text-xs text-soc-muted mb-1 block">To</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-3 py-2 bg-soc-surface border border-soc-border rounded-lg text-white text-sm focus:outline-none focus:border-purple-400"
            />
          </div>
        </div>
      </div>

      {/* Chart */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="bg-soc-card border border-soc-border rounded-xl p-6"
      >
        {renderChart()}
      </motion.div>
    </div>
  );
}
