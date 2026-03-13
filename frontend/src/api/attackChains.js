/**
 * Attack Chains & Demo API module.
 *
 * Attack Chains: Fetches correlated multi-stage attack sequences
 * and overall risk scores for the kill-chain visualization.
 *
 * Demo: Controls the live demo simulation (start/stop/clear)
 * that generates sample alerts for demonstration purposes.
 */
import client from './client';

export const attackChainsAPI = {
  /** Fetch all attack chains, with optional query params for filtering. */
  getAll: (params = {}) => client.get('/attack-chains/', { params }),

  /** Fetch details of a specific attack chain by ID. */
  getDetail: (id) => client.get(`/attack-chains/${id}/`),

  /** Fetch the overall environment risk score based on active attack chains. */
  getRiskScore: () => client.get('/attack-chains/risk-score/'),
};

export const demoAPI = {
  /** Start the demo simulation — generates sample alerts in the background. */
  start: () => client.post('/demo/start/'),

  /** Check current demo simulation status (running/stopped). */
  status: () => client.get('/demo/status/'),

  /** Clear all demo-generated data from the environment. */
  clear: () => client.post('/demo/clear/'),
};
