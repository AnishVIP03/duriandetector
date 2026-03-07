/**
 * 3D Interactive Globe Page.
 * Renders attack origins on a three.js globe using react-globe.gl.
 * Points are sized by alert count and coloured by severity.
 * Arcs connect attack sources to a central destination point.
 */
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Globe as GlobeIcon, MapPin, Activity, RefreshCw, Shield } from 'lucide-react';
import toast from 'react-hot-toast';
import { alertsAPI } from '../../api/alerts';

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */
const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#f59e0b',
  low: '#3b82f6',
};

const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low'];

/** Group alerts by rounded lat/lng for point aggregation. */
function aggregatePoints(alerts) {
  const map = {};
  alerts.forEach((a) => {
    // Round to 1 decimal for grouping nearby points
    const key = `${Math.round(a.latitude * 10) / 10}_${Math.round(a.longitude * 10) / 10}`;
    if (!map[key]) {
      map[key] = {
        lat: a.latitude,
        lng: a.longitude,
        country: a.country || 'Unknown',
        city: a.city || '',
        count: 0,
        ips: new Set(),
        severities: { critical: 0, high: 0, medium: 0, low: 0 },
      };
    }
    map[key].count += 1;
    map[key].ips.add(a.src_ip);
    const sev = a.severity || 'low';
    map[key].severities[sev] = (map[key].severities[sev] || 0) + 1;
  });

  return Object.values(map).map((p) => {
    // Dominant severity for colouring
    const dominant = SEVERITY_ORDER.find((s) => p.severities[s] > 0) || 'low';
    return {
      ...p,
      ips: Array.from(p.ips),
      dominantSeverity: dominant,
      color: SEVERITY_COLORS[dominant],
    };
  });
}

/* ------------------------------------------------------------------ */
/*  Stats panel                                                        */
/* ------------------------------------------------------------------ */
function StatsPanel({ points, countryStats }) {
  const totalAttacks = points.reduce((s, p) => s + p.count, 0);

  const severityBreakdown = useMemo(() => {
    const counts = { critical: 0, high: 0, medium: 0, low: 0 };
    points.forEach((p) => {
      Object.entries(p.severities).forEach(([sev, c]) => {
        counts[sev] = (counts[sev] || 0) + c;
      });
    });
    return counts;
  }, [points]);

  const topCountries = useMemo(() => {
    return (countryStats || []).slice(0, 5);
  }, [countryStats]);

  return (
    <div className="space-y-4">
      {/* Total attacks */}
      <div className="soc-card !p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-soc-accent/10 flex items-center justify-center">
            <Activity className="w-5 h-5 text-soc-accent" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">{totalAttacks}</p>
            <p className="text-xs text-soc-muted">Total geo-located attacks</p>
          </div>
        </div>
      </div>

      {/* Severity breakdown */}
      <div className="soc-card !p-4">
        <h4 className="text-sm font-semibold text-white mb-3">Severity Breakdown</h4>
        <div className="space-y-2">
          {SEVERITY_ORDER.map((sev) => (
            <div key={sev} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: SEVERITY_COLORS[sev] }}
                />
                <span className="text-xs text-soc-text capitalize">{sev}</span>
              </div>
              <span className="text-xs font-medium text-white">
                {severityBreakdown[sev] || 0}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Top countries */}
      {topCountries.length > 0 && (
        <div className="soc-card !p-4">
          <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-1.5">
            <MapPin className="w-4 h-4 text-soc-accent" />
            Top 5 Countries
          </h4>
          <div className="space-y-2">
            {topCountries.map((c, idx) => (
              <div key={c.country} className="flex items-center gap-2">
                <span className="text-xs text-soc-muted w-4">{idx + 1}.</span>
                <span className="text-xs text-soc-text flex-1 truncate">{c.country}</span>
                <span className="text-xs font-medium text-white">{c.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Point popup                                                        */
/* ------------------------------------------------------------------ */
function PointPopup({ point, onClose }) {
  if (!point) return null;
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="absolute top-4 left-4 bg-soc-card border border-soc-border rounded-xl p-4 shadow-2xl z-20 w-72"
    >
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-bold text-white">{point.country}</h4>
        <button onClick={onClose} className="text-soc-muted hover:text-white text-xs">
          Close
        </button>
      </div>
      {point.city && (
        <p className="text-xs text-soc-muted mb-2">City: {point.city}</p>
      )}
      <div className="space-y-1.5 text-xs">
        <div className="flex justify-between">
          <span className="text-soc-muted">Alert count</span>
          <span className="text-white font-medium">{point.count}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-soc-muted">Unique IPs</span>
          <span className="text-white font-medium">{point.ips.length}</span>
        </div>
        {point.ips.slice(0, 5).map((ip) => (
          <p key={ip} className="font-mono text-soc-accent text-[11px]">{ip}</p>
        ))}
        {point.ips.length > 5 && (
          <p className="text-soc-muted">+{point.ips.length - 5} more</p>
        )}
      </div>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main page                                                          */
/* ------------------------------------------------------------------ */
export default function GlobePage() {
  const [geoData, setGeoData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [GlobeComponent, setGlobeComponent] = useState(null);
  const globeRef = useRef();

  // Dynamically import react-globe.gl (heavy three.js dependency)
  useEffect(() => {
    let cancelled = false;
    import('react-globe.gl')
      .then((mod) => {
        if (!cancelled) {
          setGlobeComponent(() => mod.default);
        }
      })
      .catch((err) => {
        console.error('Failed to load Globe:', err);
        toast.error('Failed to load 3D globe library');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const fetchGeoData = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await alertsAPI.getGeoIP();
      setGeoData(data);
    } catch {
      toast.error('Failed to fetch GeoIP data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGeoData();
  }, [fetchGeoData]);

  // Auto-rotate
  useEffect(() => {
    if (globeRef.current) {
      globeRef.current.controls().autoRotate = true;
      globeRef.current.controls().autoRotateSpeed = 0.5;
    }
  }, [GlobeComponent, geoData]);

  // Aggregate points
  const points = useMemo(() => {
    if (!geoData?.alerts) return [];
    return aggregatePoints(geoData.alerts);
  }, [geoData]);

  // Arcs from attack origins to a central destination (0, 0 as default)
  // Use the average destination or a neutral point
  const arcs = useMemo(() => {
    if (points.length === 0) return [];
    // Use the point with the highest count as the "target" (or a default)
    const targetLat = 1.3521; // Singapore (as a default destination)
    const targetLng = 103.8198;
    return points
      .filter((p) => p.count >= 2) // Only show arcs for points with 2+ alerts
      .map((p) => ({
        startLat: p.lat,
        startLng: p.lng,
        endLat: targetLat,
        endLng: targetLng,
        color: p.color,
        stroke: Math.min(p.count / 5, 3),
      }));
  }, [points]);

  /* ---- Empty state ---- */
  if (!loading && (!geoData || geoData.alerts?.length === 0)) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <GlobeIcon className="w-6 h-6 text-soc-accent" />
            3D Attack Globe
          </h1>
          <p className="text-sm text-soc-muted mt-1">
            Interactive globe visualising attack origins
          </p>
        </div>
        <div className="soc-card flex flex-col items-center justify-center py-20">
          <Shield className="w-16 h-16 text-soc-muted/30 mb-4" />
          <p className="text-lg font-medium text-soc-muted">No geographic data available</p>
          <p className="text-sm text-soc-muted/70 mt-1">
            Start a packet capture to generate alerts with geolocation data.
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
            <GlobeIcon className="w-6 h-6 text-soc-accent" />
            3D Attack Globe
          </h1>
          <p className="text-sm text-soc-muted mt-1">
            Interactive globe visualising attack source locations worldwide
          </p>
        </div>
        <button
          onClick={fetchGeoData}
          className="soc-btn-ghost !py-2 !px-3"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Globe + Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Globe container */}
        <div className="lg:col-span-3 soc-card !p-0 overflow-hidden relative" style={{ minHeight: 520 }}>
          {loading || !GlobeComponent ? (
            <div className="flex items-center justify-center h-[520px] text-soc-muted">
              <RefreshCw className="w-5 h-5 animate-spin mr-2" />
              {loading ? 'Loading geo data...' : 'Loading 3D globe...'}
            </div>
          ) : (
            <>
              <GlobeComponent
                ref={globeRef}
                width={typeof window !== 'undefined' ? Math.min(window.innerWidth * 0.72, 1000) : 800}
                height={520}
                globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
                backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
                /* Points */
                pointsData={points}
                pointLat="lat"
                pointLng="lng"
                pointColor="color"
                pointAltitude={(d) => Math.min(d.count / 50, 0.3)}
                pointRadius={(d) => Math.max(0.3, Math.min(d.count / 10, 2))}
                pointLabel={(d) =>
                  `<div style="background:#111827;border:1px solid #1e293b;border-radius:8px;padding:8px 12px;font-size:12px;color:#e2e8f0;">
                    <strong>${d.country}</strong>${d.city ? ` - ${d.city}` : ''}<br/>
                    Alerts: <strong style="color:#3b82f6">${d.count}</strong><br/>
                    IPs: ${d.ips.length}
                  </div>`
                }
                onPointClick={(point) => setSelectedPoint(point)}
                /* Arcs */
                arcsData={arcs}
                arcStartLat="startLat"
                arcStartLng="startLng"
                arcEndLat="endLat"
                arcEndLng="endLng"
                arcColor="color"
                arcStroke="stroke"
                arcDashLength={0.4}
                arcDashGap={0.2}
                arcDashAnimateTime={1500}
                arcAltitudeAutoScale={0.3}
                /* Atmosphere */
                atmosphereColor="#3b82f6"
                atmosphereAltitude={0.2}
              />
              {/* Point popup */}
              {selectedPoint && (
                <PointPopup
                  point={selectedPoint}
                  onClose={() => setSelectedPoint(null)}
                />
              )}
            </>
          )}
        </div>

        {/* Stats sidebar */}
        <div className="lg:col-span-1">
          <StatsPanel points={points} countryStats={geoData?.country_stats} />
        </div>
      </div>
    </div>
  );
}
