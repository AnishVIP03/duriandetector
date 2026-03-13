/**
 * MITRE ATT&CK API module.
 *
 * Provides endpoints for fetching MITRE ATT&CK heatmap data
 * and individual technique details for the threat intelligence views.
 */
import client from './client';

export const mitreAPI = {
  /** Fetch heatmap data — alert counts grouped by MITRE tactic and technique. */
  getHeatmap: () => client.get('/mitre/heatmap/'),

  /** Fetch details for a specific MITRE technique by ID (e.g. T1059). */
  getTechnique: (id) => client.get(`/mitre/techniques/${id}/`),
};
