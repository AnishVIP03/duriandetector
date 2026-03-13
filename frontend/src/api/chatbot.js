/**
 * DurianBot Chatbot API module.
 *
 * Handles chat session management and message sending for the
 * AI-powered security assistant (DurianBot).
 */
import client from './client';

export const chatbotAPI = {
  /** Fetch all chat sessions for the current user. */
  getSessions: () => client.get('/chatbot/sessions/'),

  /** Fetch a single chat session with full message history. */
  getSession: (id) => client.get(`/chatbot/sessions/${id}/`),

  /** Send a message to DurianBot and receive an AI response. */
  sendMessage: (data) => client.post('/chatbot/send/', data),

  /** Delete a chat session by ID. */
  deleteSession: (id) => client.delete(`/chatbot/sessions/${id}/delete/`),
};
