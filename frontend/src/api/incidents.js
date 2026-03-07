/**
 * Incidents, Reports, ML, and System API calls.
 */
import client from './client';

export const incidentsAPI = {
  getAll: (params = {}) => client.get('/incidents/', { params }),
  create: (data) => client.post('/incidents/', data),
  getDetail: (id) => client.get(`/incidents/${id}/`),
  update: (id, data) => client.patch(`/incidents/${id}/`, data),
  getNotes: (id) => client.get(`/incidents/${id}/notes/`),
  addNote: (id, content) => client.post(`/incidents/${id}/notes/create/`, { content }),
};

export const reportsAPI = {
  getAll: (params = {}) => client.get('/reports/', { params }),
  generate: (data) => client.post('/reports/generate/', data),
  getDetail: (id) => client.get(`/reports/${id}/`),
  exportPDF: (id) => client.get(`/reports/${id}/export/`, { responseType: 'blob' }),
};

export const systemAPI = {
  getHealth: () => client.get('/admin-panel/system-health/'),
  getCaptureStatus: () => client.get('/admin-panel/capture-status/'),
  getAuditLogs: (params = {}) => client.get('/admin-panel/audit-logs/', { params }),
};
