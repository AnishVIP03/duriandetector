import client from './client';

export const mitreAPI = {
  getHeatmap: () => client.get('/mitre/heatmap/'),
  getTechnique: (id) => client.get(`/mitre/techniques/${id}/`),
};
