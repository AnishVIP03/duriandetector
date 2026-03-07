/**
 * Team Management page — US-04.
 * Manage environment members, invite new users, and view team details.
 */
import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Users, UserPlus, Copy, RefreshCw, Shield,
  Trash2, ChevronDown, Mail, Check
} from 'lucide-react';
import toast from 'react-hot-toast';
import { environmentsAPI } from '../../api/environments';
import { useAuthStore } from '../../store/authStore';
import { useEnvironmentStore } from '../../store/environmentStore';

const ROLE_BADGES = {
  team_leader: 'bg-blue-500/15 text-blue-400 border border-blue-500/30',
  security_analyst: 'bg-orange-500/15 text-orange-400 border border-orange-500/30',
  member: 'bg-gray-500/15 text-gray-400 border border-gray-500/30',
};

const ROLE_LABELS = {
  team_leader: 'Team Leader',
  security_analyst: 'Security Analyst',
  member: 'Member',
};

export default function TeamPage() {
  const { user } = useAuthStore();
  const { currentEnvironment } = useEnvironmentStore();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [inviteForm, setInviteForm] = useState({ email: '', role: 'member' });
  const [inviteLoading, setInviteLoading] = useState(false);
  const [copiedField, setCopiedField] = useState(null);
  const [regenerating, setRegenerating] = useState(false);
  const [envData, setEnvData] = useState(null);

  const envId = currentEnvironment?.id;

  const fetchMembers = useCallback(async () => {
    if (!envId) return;
    setLoading(true);
    try {
      const { data } = await environmentsAPI.getMembers(envId);
      setMembers(data.results || data);
    } catch (err) {
      console.error('Failed to fetch members:', err);
    } finally {
      setLoading(false);
    }
  }, [envId]);

  const fetchEnvironment = useCallback(async () => {
    if (!envId) return;
    try {
      const { data } = await environmentsAPI.getDetail(envId);
      setEnvData(data);
    } catch (err) {
      console.error('Failed to fetch environment details:', err);
    }
  }, [envId]);

  useEffect(() => {
    fetchMembers();
    fetchEnvironment();
  }, [fetchMembers, fetchEnvironment]);

  const handleCopy = async (text, field) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      toast.success('Copied to clipboard');
      setTimeout(() => setCopiedField(null), 2000);
    } catch {
      toast.error('Failed to copy');
    }
  };

  const handleRegenerateInvite = async () => {
    if (!envId) return;
    setRegenerating(true);
    try {
      const { data } = await environmentsAPI.regenerateInvite(envId);
      setEnvData((prev) => ({ ...prev, ...data }));
      toast.success('Invitation code regenerated');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to regenerate invite');
    } finally {
      setRegenerating(false);
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!envId) return;
    setInviteLoading(true);
    try {
      await environmentsAPI.inviteMember(envId, {
        email: inviteForm.email,
        role: inviteForm.role,
      });
      toast.success(`Invitation sent to ${inviteForm.email}`);
      setInviteForm({ email: '', role: 'member' });
      fetchMembers();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send invitation');
    } finally {
      setInviteLoading(false);
    }
  };

  const handleRemoveMember = async (memberId, memberName) => {
    if (!envId) return;
    const confirmed = window.confirm(
      `Are you sure you want to remove ${memberName} from this environment?`
    );
    if (!confirmed) return;
    try {
      await environmentsAPI.removeMember(envId, memberId);
      toast.success(`${memberName} has been removed`);
      fetchMembers();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to remove member');
    }
  };

  // Empty state — no environment selected
  if (!currentEnvironment) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="soc-card text-center max-w-md"
        >
          <Users className="w-16 h-16 text-soc-muted mx-auto mb-4 opacity-30" />
          <h2 className="text-xl font-bold text-white mb-2">No Environment Selected</h2>
          <p className="text-soc-muted text-sm mb-6">
            Create or join an environment first to manage your team.
          </p>
          <div className="flex gap-3 justify-center">
            <Link to="/setup/create" className="soc-btn-primary">
              Create Environment
            </Link>
            <Link to="/setup/join" className="soc-btn-ghost">
              Join Environment
            </Link>
          </div>
        </motion.div>
      </div>
    );
  }

  const env = envData || currentEnvironment;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Users className="w-6 h-6 text-soc-accent" />
            Team Management
          </h1>
          <p className="text-sm text-soc-muted mt-1">
            Manage members and invitations for your environment
          </p>
        </div>
        <button
          onClick={() => { fetchMembers(); fetchEnvironment(); }}
          className="soc-btn-ghost !py-2 !px-3"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Environment Info Card */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="soc-card"
      >
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-soc-accent" />
          <h2 className="text-lg font-semibold text-white">Environment Details</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Name */}
          <div>
            <label className="text-xs text-soc-muted uppercase tracking-wider block mb-1">
              Name
            </label>
            <p className="text-sm text-white font-medium">{env.name}</p>
          </div>

          {/* Network Interface */}
          <div>
            <label className="text-xs text-soc-muted uppercase tracking-wider block mb-1">
              Network Interface
            </label>
            <p className="text-sm text-soc-text font-mono">{env.network_interface || 'eth0'}</p>
          </div>

          {/* PIN */}
          <div>
            <label className="text-xs text-soc-muted uppercase tracking-wider block mb-1">
              Environment PIN
            </label>
            <div className="flex items-center gap-2">
              <code className="text-sm text-soc-accent font-mono bg-soc-surface px-2 py-1 rounded">
                {env.pin || '------'}
              </code>
              <button
                onClick={() => handleCopy(env.pin, 'pin')}
                className="p-1 rounded hover:bg-soc-surface text-soc-muted hover:text-soc-accent transition-colors"
                title="Copy PIN"
              >
                {copiedField === 'pin' ? (
                  <Check className="w-4 h-4 text-green-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* Invitation Code */}
          <div>
            <label className="text-xs text-soc-muted uppercase tracking-wider block mb-1">
              Invitation Code
            </label>
            <div className="flex items-center gap-2">
              <code className="text-sm text-soc-accent font-mono bg-soc-surface px-2 py-1 rounded truncate max-w-[160px]">
                {env.invitation_code || env.invite_code || '------'}
              </code>
              <button
                onClick={() => handleCopy(env.invitation_code || env.invite_code, 'invite')}
                className="p-1 rounded hover:bg-soc-surface text-soc-muted hover:text-soc-accent transition-colors"
                title="Copy Invitation Code"
              >
                {copiedField === 'invite' ? (
                  <Check className="w-4 h-4 text-green-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
              <button
                onClick={handleRegenerateInvite}
                disabled={regenerating}
                className="p-1 rounded hover:bg-soc-surface text-soc-muted hover:text-yellow-400 transition-colors"
                title="Regenerate Invitation Code"
              >
                <RefreshCw className={`w-4 h-4 ${regenerating ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Invite Member Form */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="soc-card"
      >
        <div className="flex items-center gap-2 mb-4">
          <UserPlus className="w-5 h-5 text-soc-accent" />
          <h2 className="text-lg font-semibold text-white">Invite Member</h2>
        </div>

        <form onSubmit={handleInvite} className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-soc-muted" />
            <input
              type="email"
              value={inviteForm.email}
              onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
              className="soc-input pl-10"
              placeholder="colleague@company.com"
              required
            />
          </div>

          <div className="relative sm:w-52">
            <select
              value={inviteForm.role}
              onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
              className="soc-input appearance-none pr-10"
            >
              <option value="member">Member</option>
              <option value="security_analyst">Security Analyst</option>
              <option value="team_leader">Team Leader</option>
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-soc-muted pointer-events-none" />
          </div>

          <button
            type="submit"
            disabled={inviteLoading}
            className="soc-btn-primary flex items-center justify-center gap-2 whitespace-nowrap"
          >
            {inviteLoading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <UserPlus className="w-4 h-4" />
            )}
            Send Invite
          </button>
        </form>
      </motion.div>

      {/* Members Table */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="soc-card overflow-hidden !p-0"
      >
        <div className="px-4 py-3 border-b border-soc-border flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-soc-accent" />
            Members
            {members.length > 0 && (
              <span className="text-xs text-soc-muted font-normal ml-1">
                ({members.length})
              </span>
            )}
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-soc-border">
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">
                  Name / Email
                </th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">
                  Role
                </th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">
                  Joined
                </th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-soc-border">
              {loading && members.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-12 text-soc-muted">
                    <RefreshCw className="w-6 h-6 mx-auto mb-2 animate-spin opacity-40" />
                    Loading members...
                  </td>
                </tr>
              ) : members.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-12 text-soc-muted">
                    <Users className="w-12 h-12 mx-auto mb-3 opacity-20" />
                    <p>No members yet</p>
                    <p className="text-xs mt-1">Invite team members to get started</p>
                  </td>
                </tr>
              ) : (
                members.map((member) => {
                  const isCurrentUser =
                    member.user?.id === user?.id || member.id === user?.id;
                  const displayName =
                    member.user?.full_name ||
                    member.user?.username ||
                    member.full_name ||
                    member.username ||
                    member.email ||
                    'Unknown';
                  const displayEmail =
                    member.user?.email || member.email || '';
                  const memberRole =
                    member.role || member.user?.role || 'member';
                  const joinedDate = member.joined_at || member.date_joined || member.created_at;

                  return (
                    <motion.tr
                      key={member.id || member.user?.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`hover:bg-soc-surface/50 transition-colors ${
                        isCurrentUser ? 'bg-soc-accent/5' : ''
                      }`}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-soc-surface flex items-center justify-center text-sm font-medium text-soc-accent">
                            {displayName.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="text-sm text-white font-medium">
                              {displayName}
                              {isCurrentUser && (
                                <span className="ml-2 text-xs text-soc-accent">(You)</span>
                              )}
                            </p>
                            {displayEmail && (
                              <p className="text-xs text-soc-muted">{displayEmail}</p>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            ROLE_BADGES[memberRole] || ROLE_BADGES.member
                          }`}
                        >
                          {ROLE_LABELS[memberRole] || memberRole}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-soc-muted">
                        {joinedDate
                          ? new Date(joinedDate).toLocaleDateString()
                          : '--'}
                      </td>
                      <td className="px-4 py-3">
                        {!isCurrentUser ? (
                          <button
                            onClick={() =>
                              handleRemoveMember(
                                member.user?.id || member.id,
                                displayName
                              )
                            }
                            className="p-1.5 rounded hover:bg-red-500/10 text-soc-muted hover:text-red-400 transition-colors"
                            title="Remove member"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        ) : (
                          <span className="text-xs text-soc-muted">--</span>
                        )}
                      </td>
                    </motion.tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}
