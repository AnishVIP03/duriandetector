/**
 * Subscriptions API calls.
 */
import client from './client';

export const subscriptionsAPI = {
  getPlans: () => client.get('/subscriptions/plans/'),
  getMySubscription: () => client.get('/subscriptions/my/'),
  upgrade: (planName) => client.post('/subscriptions/upgrade/', { plan_name: planName }),
  manageTeam: (planName) => client.post('/subscriptions/manage/', { plan_name: planName }),
};
