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
};

export const captureAPI = {
  start: (data = {}) => client.post('/capture/start/', data),
  stop: () => client.post('/capture/stop/'),
  getStatus: () => client.get('/capture/status/'),
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
