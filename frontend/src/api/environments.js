/**
 * Environments API calls.
 */
import client from './client';

export const environmentsAPI = {
  create: (data) => client.post('/environments/', data),
  join: (data) => client.post('/environments/join/', data),
  getDetail: (id) => client.get(`/environments/${id}/`),
  update: (id, data) => client.patch(`/environments/${id}/`, data),
  getMembers: (envId) => client.get(`/environments/${envId}/members/`),
  inviteMember: (envId, data) => client.post(`/environments/${envId}/invite/`, data),
  removeMember: (envId, userId) => client.delete(`/environments/${envId}/members/${userId}/`),
  regenerateInvite: (envId) => client.post(`/environments/${envId}/regenerate-invite/`),
};
