/**
 * GeoIP Map page — US-11.
 * Leaflet map showing alert source locations.
 */
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Globe, MapPin, AlertTriangle, RefreshCw } from 'lucide-react';
import { alertsAPI } from '../../api/alerts';

export default function GeoIPMapPage() {
  const [geoData, setGeoData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [MapComponent, setMapComponent] = useState(null);

  useEffect(() => {
    // Dynamic import for Leaflet (SSR-safe)
    const loadMap = async () => {
      try {
        const L = await import('leaflet');
        const { MapContainer, TileLayer, CircleMarker, Popup } = await import('react-leaflet');

        // Fix default icon issue
        delete L.Icon.Default.prototype._getIconUrl;
        L.Icon.Default.mergeOptions({
          iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
          iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
          shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
        });

        setMapComponent(() => {
          return function Map({ alerts }) {
            const severityColors = {
              low: '#3b82f6',
              medium: '#f59e0b',
              high: '#f97316',
              critical: '#ef4444',
            };

            return (
              <MapContainer
                center={[20, 0]}
                zoom={2}
                style={{ height: '500px', width: '100%', borderRadius: '12px' }}
                className="z-0"
              >
                <TileLayer
                  url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                  attribution='&copy; CartoDB'
                />
                {alerts.map((alert) => (
                  <CircleMarker
                    key={alert.id}
                    center={[alert.latitude, alert.longitude]}
                    radius={alert.severity === 'critical' ? 10 : alert.severity === 'high' ? 8 : 6}
                    fillColor={severityColors[alert.severity] || '#3b82f6'}
                    color={severityColors[alert.severity] || '#3b82f6'}
                    weight={1}
                    opacity={0.8}
                    fillOpacity={0.5}
                  >
                    <Popup>
                      <div className="text-xs">
                        <strong className="text-sm">{alert.alert_type.replace(/_/g, ' ')}</strong><br />
                        IP: {alert.src_ip}<br />
                        Severity: {alert.severity}<br />
                        Location: {alert.city}, {alert.country}<br />
                        Confidence: {(alert.confidence_score * 100).toFixed(0)}%<br />
                        Time: {new Date(alert.timestamp).toLocaleString()}
                      </div>
                    </Popup>
                  </CircleMarker>
                ))}
              </MapContainer>
            );
          };
        });
      } catch (err) {
        console.error('Failed to load map:', err);
      }
    };

    loadMap();
  }, []);

  useEffect(() => {
    fetchGeoData();
  }, []);

  const fetchGeoData = async () => {
    setLoading(true);
    try {
      const { data } = await alertsAPI.getGeoIP();
      setGeoData(data);
    } catch {
      console.error('Failed to fetch GeoIP data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Globe className="w-6 h-6 text-soc-accent" />
            GeoIP Attack Map
          </h1>
          <p className="text-sm text-soc-muted mt-1">
            Geographic visualization of alert sources
          </p>
        </div>
        <button onClick={fetchGeoData} className="soc-btn-ghost !py-2 !px-3">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Map */}
      <div className="soc-card !p-0 overflow-hidden">
        {/* Import Leaflet CSS */}
        <link
          rel="stylesheet"
          href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"
        />
        {MapComponent && geoData ? (
          <MapComponent alerts={geoData.alerts} />
        ) : (
          <div className="h-[500px] flex items-center justify-center text-soc-muted">
            {loading ? 'Loading map data...' : 'No geographic data available'}
          </div>
        )}
      </div>

      {/* Country statistics */}
      {geoData?.country_stats && geoData.country_stats.length > 0 && (
        <div className="soc-card">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-soc-accent" />
            Top Attack Origins
          </h3>
          <div className="space-y-3">
            {geoData.country_stats.map((stat) => (
              <div key={stat.country} className="flex items-center gap-4">
                <span className="text-sm text-soc-text w-40 truncate">{stat.country}</span>
                <div className="flex-1 h-2 bg-soc-surface rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{
                      width: `${(stat.count / geoData.country_stats[0].count) * 100}%`,
                    }}
                    className="h-full bg-soc-accent rounded-full"
                  />
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <span className="text-soc-text font-medium w-12 text-right">{stat.count}</span>
                  {stat.critical > 0 && (
                    <span className="text-red-400 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      {stat.critical}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
