/**
 * Attack Chains & Demo API calls.
 */
import client from './client';

export const attackChainsAPI = {
  getAll: (params = {}) => client.get('/attack-chains/', { params }),
  getDetail: (id) => client.get(`/attack-chains/${id}/`),
  getRiskScore: () => client.get('/attack-chains/risk-score/'),
};

export const demoAPI = {
  start: () => client.post('/demo/start/'),
  status: () => client.get('/demo/status/'),
  clear: () => client.post('/demo/clear/'),
};
