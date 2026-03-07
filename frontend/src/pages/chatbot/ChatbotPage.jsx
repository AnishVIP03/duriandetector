/**
 * AI Chatbot Page — DurianBot, the Ollama-powered security assistant.
 * Full-featured chat interface with SOC dark theme, session management,
 * suggested prompts, and message animations.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare, Send, Plus, Trash2, Bot, User,
  Sparkles, ChevronLeft, ChevronRight, Loader2, AlertTriangle
} from 'lucide-react';
import toast from 'react-hot-toast';
import { chatbotAPI } from '../../api/chatbot';

const SUGGESTED_PROMPTS = [
  'What are the latest critical alerts?',
  'Explain the top threat sources',
  'How do I investigate a port scan?',
  'What MITRE techniques should I watch for?',
];

function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 max-w-[80%]">
      <div className="w-8 h-8 rounded-full bg-soc-accent/20 flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4 text-soc-accent" />
      </div>
      <div className="bg-soc-surface border border-soc-border rounded-2xl rounded-tl-sm px-4 py-3">
        <div className="flex items-center gap-1.5">
          <motion.div
            className="w-2 h-2 rounded-full bg-soc-muted"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.2, repeat: Infinity, delay: 0 }}
          />
          <motion.div
            className="w-2 h-2 rounded-full bg-soc-muted"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.2, repeat: Infinity, delay: 0.2 }}
          />
          <motion.div
            className="w-2 h-2 rounded-full bg-soc-muted"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.2, repeat: Infinity, delay: 0.4 }}
          />
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message, index }) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: index * 0.03 }}
      className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser ? 'bg-soc-accent/20' : 'bg-soc-accent/20'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-soc-accent" />
        ) : (
          <Bot className="w-4 h-4 text-soc-accent" />
        )}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-soc-accent text-white rounded-tr-sm'
            : 'bg-soc-surface border border-soc-border text-soc-text rounded-tl-sm'
        }`}
      >
        {message.content}
      </div>
    </motion.div>
  );
}

function SessionItem({ session, isActive, onClick, onDelete }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className={`group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-all text-sm ${
        isActive
          ? 'bg-soc-accent/10 text-soc-accent border border-soc-accent/20'
          : 'text-soc-muted hover:bg-soc-surface hover:text-soc-text'
      }`}
      onClick={onClick}
    >
      <MessageSquare className="w-4 h-4 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="truncate font-medium">{session.title}</p>
        <p className="text-xs opacity-60 truncate mt-0.5">
          {session.message_count} message{session.message_count !== 1 ? 's' : ''}
        </p>
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete(session.id);
        }}
        className="opacity-0 group-hover:opacity-100 text-soc-muted hover:text-soc-danger transition-all p-1"
        title="Delete session"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </motion.div>
  );
}

export default function ChatbotPage() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sessionsLoading, setSessionsLoading] = useState(true);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to latest message
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, scrollToBottom]);

  // Load sessions on mount
  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      setSessionsLoading(true);
      const res = await chatbotAPI.getSessions();
      setSessions(res.data);
    } catch (err) {
      toast.error('Failed to load chat sessions');
    } finally {
      setSessionsLoading(false);
    }
  };

  const loadSession = async (sessionId) => {
    try {
      setActiveSessionId(sessionId);
      const res = await chatbotAPI.getSession(sessionId);
      setMessages(res.data.messages || []);
    } catch (err) {
      toast.error('Failed to load chat session');
    }
  };

  const handleNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    setInput('');
    inputRef.current?.focus();
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await chatbotAPI.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
      }
      toast.success('Chat session deleted');
    } catch (err) {
      toast.error('Failed to delete session');
    }
  };

  const handleSend = async (messageText) => {
    const text = (messageText || input).trim();
    if (!text || isLoading) return;

    // Optimistically add user message
    const tempUserMsg = { id: Date.now(), role: 'user', content: text, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, tempUserMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const payload = { message: text };
      if (activeSessionId) {
        payload.session_id = activeSessionId;
      }

      const res = await chatbotAPI.sendMessage(payload);
      const { session_id, assistant_message, user_message } = res.data;

      // Replace temp user message with real one, add assistant message
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempUserMsg.id),
        user_message,
        assistant_message,
      ]);

      // Update active session
      if (!activeSessionId) {
        setActiveSessionId(session_id);
      }

      // Refresh sessions list
      fetchSessions();
    } catch (err) {
      toast.error('Failed to send message. Please try again.');
      // Remove the optimistic user message on failure
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id));
      setInput(text);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isEmpty = messages.length === 0 && !isLoading;

  return (
    <div className="flex h-[calc(100vh-8rem)] -m-6 overflow-hidden">
      {/* Sidebar */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="bg-soc-card border-r border-soc-border flex flex-col flex-shrink-0 overflow-hidden"
          >
            {/* Sidebar header */}
            <div className="p-4 border-b border-soc-border">
              <button
                onClick={handleNewChat}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-soc-accent hover:bg-soc-accent/90 text-white text-sm font-medium transition-colors"
              >
                <Plus className="w-4 h-4" />
                New Chat
              </button>
            </div>

            {/* Session list */}
            <div className="flex-1 overflow-y-auto p-3 space-y-1">
              {sessionsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-5 h-5 text-soc-muted animate-spin" />
                </div>
              ) : sessions.length === 0 ? (
                <div className="text-center py-8 px-4">
                  <MessageSquare className="w-8 h-8 text-soc-muted/50 mx-auto mb-2" />
                  <p className="text-xs text-soc-muted">No conversations yet</p>
                </div>
              ) : (
                sessions.map((session) => (
                  <SessionItem
                    key={session.id}
                    session={session}
                    isActive={session.id === activeSessionId}
                    onClick={() => loadSession(session.id)}
                    onDelete={handleDeleteSession}
                  />
                ))
              )}
            </div>

            {/* Sidebar footer */}
            <div className="p-3 border-t border-soc-border">
              <div className="flex items-center gap-2 text-xs text-soc-muted">
                <Bot className="w-4 h-4 text-soc-accent" />
                <span>DurianBot AI Assistant</span>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-soc-border bg-soc-card/50">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-soc-muted hover:text-white transition-colors"
          >
            {sidebarOpen ? (
              <ChevronLeft className="w-5 h-5" />
            ) : (
              <ChevronRight className="w-5 h-5" />
            )}
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-soc-accent/20 flex items-center justify-center">
              <Bot className="w-4 h-4 text-soc-accent" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">DurianBot</h2>
              <p className="text-xs text-soc-muted">AI Security Assistant</p>
            </div>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <div className="status-dot status-dot-active" />
            <span className="text-xs text-soc-muted">Online</span>
          </div>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {isEmpty ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4 }}
              >
                <div className="w-16 h-16 rounded-2xl bg-soc-accent/10 flex items-center justify-center mb-4 mx-auto">
                  <Sparkles className="w-8 h-8 text-soc-accent" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  Ask DurianBot
                </h3>
                <p className="text-sm text-soc-muted max-w-md mb-8">
                  Ask DurianBot about your security alerts, threats, or network activity
                </p>

                {/* Suggested prompts */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto">
                  {SUGGESTED_PROMPTS.map((prompt, i) => (
                    <motion.button
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 + i * 0.08 }}
                      onClick={() => handleSend(prompt)}
                      className="text-left px-4 py-3 rounded-xl border border-soc-border bg-soc-surface hover:bg-soc-card hover:border-soc-accent/30 text-sm text-soc-text transition-all group"
                    >
                      <div className="flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-soc-accent mt-0.5 flex-shrink-0" />
                        <span className="group-hover:text-white transition-colors">
                          {prompt}
                        </span>
                      </div>
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <MessageBubble key={msg.id || i} message={msg} index={i} />
              ))}
              {isLoading && <TypingIndicator />}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="px-4 py-3 border-t border-soc-border bg-soc-card/50">
          <div className="flex items-end gap-3 max-w-4xl mx-auto">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask DurianBot about alerts, threats, or security..."
                rows={1}
                className="w-full resize-none bg-soc-surface border border-soc-border rounded-xl px-4 py-3 pr-12 text-sm text-soc-text placeholder-soc-muted focus:outline-none focus:border-soc-accent/50 focus:ring-1 focus:ring-soc-accent/20 transition-all"
                style={{ minHeight: '44px', maxHeight: '120px' }}
                onInput={(e) => {
                  e.target.style.height = 'auto';
                  e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
                }}
                disabled={isLoading}
              />
            </div>
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
              className="flex items-center justify-center w-11 h-11 rounded-xl bg-soc-accent hover:bg-soc-accent/90 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-all flex-shrink-0"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
          <p className="text-center text-xs text-soc-muted/50 mt-2">
            DurianBot may provide general guidance. Always verify with your security team.
          </p>
        </div>
      </div>
    </div>
  );
}
