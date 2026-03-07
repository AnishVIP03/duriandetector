/**
 * Incident List page — US-16, US-17.
 * Manage security incidents with status tracking.
 */
import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Crosshair, Plus, Search, Filter, RefreshCw, X,
  ChevronRight, Clock, User
} from 'lucide-react';
import toast from 'react-hot-toast';
import { incidentsAPI } from '../../api/incidents';

const STATUS_COLORS = {
  open: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  in_progress: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  resolved: 'bg-green-500/20 text-green-400 border-green-500/30',
  closed: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};

const SEVERITY_COLORS = {
  low: 'badge-low', medium: 'badge-medium', high: 'badge-high', critical: 'badge-critical',
};

export default function IncidentListPage() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [filters, setFilters] = useState({ severity: '', status: '' });
  const [createForm, setCreateForm] = useState({ title: '', description: '', severity: 'medium' });
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState('');

  const fetchIncidents = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.severity) params.severity = filters.severity;
      if (filters.status) params.status = filters.status;
      const { data } = await incidentsAPI.getAll(params);
      setIncidents(data.results || data);
    } catch { /* API may not be ready */ }
    finally { setLoading(false); }
  }, [filters]);

  useEffect(() => { fetchIncidents(); }, [fetchIncidents]);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await incidentsAPI.create(createForm);
      toast.success('Incident created');
      setShowCreate(false);
      setCreateForm({ title: '', description: '', severity: 'medium' });
      fetchIncidents();
    } catch { toast.error('Failed to create incident'); }
  };

  const handleSelectIncident = async (incident) => {
    setSelectedIncident(incident);
    try {
      const [detailRes, notesRes] = await Promise.all([
        incidentsAPI.getDetail(incident.id),
        incidentsAPI.getNotes(incident.id),
      ]);
      setSelectedIncident(detailRes.data);
      setNotes(notesRes.data?.results || notesRes.data || []);
    } catch { /* fallback to list data */ }
  };

  const handleStatusChange = async (newStatus) => {
    if (!selectedIncident) return;
    try {
      const { data } = await incidentsAPI.update(selectedIncident.id, { status: newStatus });
      setSelectedIncident(data);
      toast.success(`Status changed to ${newStatus.replace('_', ' ')}`);
      fetchIncidents();
    } catch { toast.error('Failed to update status'); }
  };

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!newNote.trim() || !selectedIncident) return;
    try {
      const { data } = await incidentsAPI.addNote(selectedIncident.id, newNote);
      setNotes([...notes, data]);
      setNewNote('');
      toast.success('Note added');
    } catch { toast.error('Failed to add note'); }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Crosshair className="w-6 h-6 text-soc-accent" /> Incidents
          </h1>
          <p className="text-sm text-soc-muted mt-1">Track and manage security incidents</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchIncidents} className="soc-btn-ghost !py-2 !px-3">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button onClick={() => setShowCreate(true)} className="soc-btn-primary !py-2 flex items-center gap-2">
            <Plus className="w-4 h-4" /> New Incident
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })} className="soc-input !w-auto !py-2">
          <option value="">All Status</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
        <select value={filters.severity} onChange={(e) => setFilters({ ...filters, severity: e.target.value })} className="soc-input !w-auto !py-2">
          <option value="">All Severity</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Incident list */}
        <div className="lg:col-span-1 space-y-2">
          {loading ? (
            <div className="text-center py-12 text-soc-muted">Loading...</div>
          ) : incidents.length === 0 ? (
            <div className="soc-card text-center py-12 text-soc-muted">
              <Crosshair className="w-12 h-12 mx-auto mb-3 opacity-20" />
              <p>No incidents</p>
            </div>
          ) : incidents.map((inc) => (
            <motion.div
              key={inc.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              onClick={() => handleSelectIncident(inc)}
              className={`soc-card cursor-pointer hover:soc-glow transition-all !p-4 ${
                selectedIncident?.id === inc.id ? 'soc-glow' : ''
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`px-2 py-0.5 rounded text-xs font-medium border ${STATUS_COLORS[inc.status]}`}>
                  {inc.status?.replace('_', ' ')}
                </span>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${SEVERITY_COLORS[inc.severity]}`}>
                  {inc.severity}
                </span>
              </div>
              <h3 className="text-sm font-semibold text-white truncate">{inc.title}</h3>
              <div className="flex items-center justify-between mt-2 text-xs text-soc-muted">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {new Date(inc.created_at).toLocaleDateString()}
                </span>
                <span>{inc.alert_count || 0} alerts</span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Detail panel */}
        <div className="lg:col-span-2">
          {selectedIncident ? (
            <div className="soc-card space-y-6">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-bold text-white">{selectedIncident.title}</h2>
                  <p className="text-sm text-soc-muted mt-1">{selectedIncident.description}</p>
                </div>
                <button onClick={() => setSelectedIncident(null)} className="text-soc-muted hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Status actions */}
              <div className="flex flex-wrap gap-2">
                {['open', 'in_progress', 'resolved', 'closed'].map((s) => (
                  <button
                    key={s}
                    onClick={() => handleStatusChange(s)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                      selectedIncident.status === s
                        ? STATUS_COLORS[s]
                        : 'bg-soc-surface text-soc-muted border-soc-border hover:text-white'
                    }`}
                  >
                    {s.replace('_', ' ')}
                  </button>
                ))}
              </div>

              {/* Info grid */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-soc-surface rounded-lg p-3">
                  <p className="text-xs text-soc-muted">Created By</p>
                  <p className="text-sm text-white">{selectedIncident.created_by_email || selectedIncident.created_by || '—'}</p>
                </div>
                <div className="bg-soc-surface rounded-lg p-3">
                  <p className="text-xs text-soc-muted">Assigned To</p>
                  <p className="text-sm text-white">{selectedIncident.assigned_to_email || '—'}</p>
                </div>
                <div className="bg-soc-surface rounded-lg p-3">
                  <p className="text-xs text-soc-muted">Linked Alerts</p>
                  <p className="text-sm text-white">{selectedIncident.alerts?.length || 0}</p>
                </div>
                <div className="bg-soc-surface rounded-lg p-3">
                  <p className="text-xs text-soc-muted">Resolved At</p>
                  <p className="text-sm text-white">
                    {selectedIncident.resolved_at ? new Date(selectedIncident.resolved_at).toLocaleString() : '—'}
                  </p>
                </div>
              </div>

              {/* Notes */}
              <div>
                <h3 className="text-base font-semibold text-white mb-3">Notes</h3>
                <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
                  {notes.length === 0 ? (
                    <p className="text-sm text-soc-muted">No notes yet.</p>
                  ) : notes.map((note, i) => (
                    <div key={note.id || i} className="bg-soc-surface rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs text-soc-accent">{note.author_email || note.author || 'User'}</span>
                        <span className="text-xs text-soc-muted">{new Date(note.created_at).toLocaleString()}</span>
                      </div>
                      <p className="text-sm text-soc-text">{note.content}</p>
                    </div>
                  ))}
                </div>
                <form onSubmit={handleAddNote} className="flex gap-2">
                  <input
                    value={newNote}
                    onChange={(e) => setNewNote(e.target.value)}
                    className="soc-input flex-1 !py-2"
                    placeholder="Add a note..."
                  />
                  <button type="submit" className="soc-btn-primary !py-2 !px-4">Add</button>
                </form>
              </div>
            </div>
          ) : (
            <div className="soc-card text-center py-20 text-soc-muted">
              <Crosshair className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-lg">Select an incident to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Create modal */}
      <AnimatePresence>
        {showCreate && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
            onClick={() => setShowCreate(false)}
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              className="soc-card w-full max-w-lg"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-xl font-bold text-white mb-4">Create Incident</h2>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="text-sm text-soc-muted mb-1 block">Title</label>
                  <input
                    value={createForm.title}
                    onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                    className="soc-input"
                    placeholder="Incident title"
                    required
                  />
                </div>
                <div>
                  <label className="text-sm text-soc-muted mb-1 block">Description</label>
                  <textarea
                    value={createForm.description}
                    onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                    className="soc-input resize-none"
                    rows={3}
                    placeholder="Describe the incident..."
                  />
                </div>
                <div>
                  <label className="text-sm text-soc-muted mb-1 block">Severity</label>
                  <select
                    value={createForm.severity}
                    onChange={(e) => setCreateForm({ ...createForm, severity: e.target.value })}
                    className="soc-input"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setShowCreate(false)} className="soc-btn-ghost flex-1">Cancel</button>
                  <button type="submit" className="soc-btn-primary flex-1">Create</button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
