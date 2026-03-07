/**
 * Admin API calls.
 */
import client from './client';

export const adminAPI = {
  // Users
  getUsers: (params) => client.get('/auth/admin/users/', { params }),
  suspendUser: (userId) => client.post(`/auth/admin/users/${userId}/suspend/`),
  unsuspendUser: (userId) => client.post(`/auth/admin/users/${userId}/unsuspend/`),
  resetPassword: (userId) => client.post(`/auth/admin/users/${userId}/reset-password/`),
  updateSubscription: (userId, data) => client.post(`/auth/admin/users/${userId}/update-subscription/`, data),

  // Audit
  getAuditLogs: (params) => client.get('/admin-panel/audit-logs/', { params }),

  // System
  getSystemHealth: () => client.get('/admin-panel/system-health/'),
};
