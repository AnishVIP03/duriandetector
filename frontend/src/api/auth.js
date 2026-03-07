/**
 * Auth API calls.
 */
import client from './client';

export const authAPI = {
  register: (data) => client.post('/auth/register/', data),
  login: (data) => client.post('/auth/login/', data),
  logout: (refreshToken) => client.post('/auth/logout/', { refresh: refreshToken }),
  getProfile: () => client.get('/auth/profile/'),
  updateProfile: (data) => client.patch('/auth/profile/', data),
  requestPasswordReset: (email) => client.post('/auth/password-reset/', { email }),
  confirmPasswordReset: (data) => client.post('/auth/password-reset/confirm/', data),
};
