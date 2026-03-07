import client from './client';

export const chatbotAPI = {
  getSessions: () => client.get('/chatbot/sessions/'),
  getSession: (id) => client.get(`/chatbot/sessions/${id}/`),
  sendMessage: (data) => client.post('/chatbot/send/', data),
  deleteSession: (id) => client.delete(`/chatbot/sessions/${id}/delete/`),
};
