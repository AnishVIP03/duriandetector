/**
 * Alerts API calls.
 */
import client from './client';

export const alertsAPI = {
  getAll: (params = {}) => client.get('/alerts/', { params }),
  getDetail: (id) => client.get(`/alerts/${id}/`),
  getGeoIP: () => client.get('/alerts/geoip/'),
  getStats: () => client.get('/alerts/stats/'),
  blockIP: (alertId, reason = '') => client.post(`/alerts/${alertId}/block/`, { reason }),
  unblockIP: (alertId) => client.post(`/alerts/${alertId}/unblock/`),
  // Block control list
  getBlockedIPs: (params = {}) => client.get('/alerts/blocked-ips/', { params }),
  unblockIPById: (id) => client.post(`/alerts/blocked-ips/${id}/unblock/`),
  // Whitelist
  getWhitelist: () => client.get('/alerts/whitelist/'),
  addToWhitelist: (data) => client.post('/alerts/whitelist/', data),
  removeFromWhitelist: (id) => client.delete(`/alerts/whitelist/${id}/`),
  // Analytics
  getAnalytics: (params = {}) => client.get('/alerts/analytics/', { params }),
  // Traffic filters
  getTrafficFilters: () => client.get('/alerts/traffic-filters/'),
  createTrafficFilter: (data) => client.post('/alerts/traffic-filters/', data),
  updateTrafficFilter: (id, data) => client.patch(`/alerts/traffic-filters/${id}/`, data),
  deleteTrafficFilter: (id) => client.delete(`/alerts/traffic-filters/${id}/`),
  toggleTrafficFilter: (id) => client.post(`/alerts/traffic-filters/${id}/toggle/`),
  // Log ingestion
  uploadLogFile: (formData) => client.post('/alerts/log-ingestion/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getUploadHistory: () => client.get('/alerts/log-ingestion/history/'),
};

export const captureAPI = {
  start: (data = {}) => client.post('/capture/start/', data),
  stop: () => client.post('/capture/stop/'),
  getStatus: () => client.get('/capture/status/'),
  simulate: (data = {}) => client.post('/capture/simulate/', data),
  stopSimulate: () => client.post('/capture/simulate/stop/'),
};

export const threatsAPI = {
  getAll: (params = {}) => client.get('/threats/', { params }),
  correlate: (ip) => client.get(`/threats/${ip}/correlate/`),
};

export const mlAPI = {
  getConfig: () => client.get('/ml/config/'),
  updateConfig: (data) => client.patch('/ml/config/', data),
  train: () => client.post('/ml/train/'),
  getMetrics: () => client.get('/ml/metrics/'),
};
