/**
 * Admin Users Management page.
 * Lists all users with search, filter, and admin actions (suspend, reset password, change subscription).
 */
import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  UserCog, Search, Shield, Ban, Unlock, RefreshCw, Key, ChevronDown,
  ChevronLeft, ChevronRight
} from 'lucide-react';
import toast from 'react-hot-toast';
import { adminAPI } from '../../api/admin';

const ROLE_COLORS = {
  admin: 'badge-critical',
  exclusive: 'badge-high',
  premium: 'badge-medium',
  free: 'badge-low',
};

const SUBSCRIPTION_OPTIONS = ['free', 'premium', 'exclusive'];

export default function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [openDropdown, setOpenDropdown] = useState(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page };
      if (search) params.search = search;
      if (roleFilter) params.role = roleFilter;

      const { data } = await adminAPI.getUsers(params);
      setUsers(data.results || data);
      setTotalCount(data.count || (data.results ? data.results.length : data.length));
      if (data.count) {
        setTotalPages(Math.ceil(data.count / 25));
      }
    } catch (err) {
      console.error('Failed to fetch users:', err);
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  }, [page, search, roleFilter]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const handleSuspend = async (user) => {
    const action = user.is_active ? 'suspend' : 'unsuspend';
    const confirmed = window.confirm(
      `Are you sure you want to ${action} user "${user.email}"?`
    );
    if (!confirmed) return;

    try {
      if (user.is_active) {
        await adminAPI.suspendUser(user.id);
        toast.success(`User ${user.email} suspended`);
      } else {
        await adminAPI.unsuspendUser(user.id);
        toast.success(`User ${user.email} unsuspended`);
      }
      fetchUsers();
    } catch {
      toast.error(`Failed to ${action} user`);
    }
  };

  const handleResetPassword = async (user) => {
    const confirmed = window.confirm(
      `Send a password reset email to "${user.email}"?`
    );
    if (!confirmed) return;

    try {
      await adminAPI.resetPassword(user.id);
      toast.success(`Password reset email sent to ${user.email}`);
    } catch {
      toast.error('Failed to reset password');
    }
  };

  const handleSubscriptionChange = async (user, newRole) => {
    const confirmed = window.confirm(
      `Change subscription for "${user.email}" from "${user.role}" to "${newRole}"?`
    );
    if (!confirmed) {
      setOpenDropdown(null);
      return;
    }

    try {
      await adminAPI.updateSubscription(user.id, { role: newRole });
      toast.success(`Subscription updated to ${newRole}`);
      setOpenDropdown(null);
      fetchUsers();
    } catch {
      toast.error('Failed to update subscription');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <UserCog className="w-6 h-6 text-soc-accent" />
            User Management
          </h1>
          <p className="text-sm text-soc-muted mt-1">
            {totalCount} total users
          </p>
        </div>
        <button onClick={fetchUsers} className="soc-btn-ghost !py-2 !px-3">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-soc-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="soc-input pl-10"
            placeholder="Search by email or name..."
          />
        </div>
        <select
          value={roleFilter}
          onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }}
          className="soc-input !py-2 w-full sm:w-48"
        >
          <option value="">All Roles</option>
          <option value="free">Free</option>
          <option value="premium">Premium</option>
          <option value="exclusive">Exclusive</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      {/* Users Table */}
      <div className="soc-card overflow-hidden !p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-soc-border">
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Email</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Name</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Role</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Team Role</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Status</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Joined</th>
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-soc-border">
              {loading && users.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-soc-muted">
                    Loading users...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-soc-muted">
                    <Shield className="w-12 h-12 mx-auto mb-3 opacity-20" />
                    <p>No users found</p>
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr
                    key={user.id}
                    className={`hover:bg-soc-surface/50 transition-colors ${
                      !user.is_active ? 'bg-red-500/5' : ''
                    }`}
                  >
                    <td className="px-4 py-3 text-sm text-soc-text font-mono">{user.email}</td>
                    <td className="px-4 py-3 text-sm text-soc-text">
                      {user.first_name || user.last_name
                        ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
                        : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${ROLE_COLORS[user.role] || 'badge-low'}`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-soc-muted">
                      {user.team_role || '—'}
                    </td>
                    <td className="px-4 py-3">
                      {user.is_active ? (
                        <span className="text-xs text-green-400 bg-green-500/10 px-2 py-0.5 rounded">
                          Active
                        </span>
                      ) : (
                        <span className="text-xs text-red-400 bg-red-500/10 px-2 py-0.5 rounded">
                          Suspended
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-soc-muted">
                      {new Date(user.date_joined).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        {/* Suspend / Unsuspend */}
                        <button
                          onClick={() => handleSuspend(user)}
                          className={`p-1.5 rounded transition-colors ${
                            user.is_active
                              ? 'hover:bg-red-500/10 text-soc-muted hover:text-red-400'
                              : 'hover:bg-green-500/10 text-soc-muted hover:text-green-400'
                          }`}
                          title={user.is_active ? 'Suspend user' : 'Unsuspend user'}
                        >
                          {user.is_active ? <Ban className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
                        </button>

                        {/* Reset Password */}
                        <button
                          onClick={() => handleResetPassword(user)}
                          className="p-1.5 rounded hover:bg-soc-accent/10 text-soc-muted hover:text-soc-accent transition-colors"
                          title="Reset password"
                        >
                          <Key className="w-4 h-4" />
                        </button>

                        {/* Change Subscription */}
                        <div className="relative">
                          <button
                            onClick={() => setOpenDropdown(openDropdown === user.id ? null : user.id)}
                            className="p-1.5 rounded hover:bg-soc-accent/10 text-soc-muted hover:text-soc-accent transition-colors flex items-center gap-0.5"
                            title="Change subscription"
                          >
                            <ChevronDown className="w-4 h-4" />
                          </button>
                          {openDropdown === user.id && (
                            <div className="absolute right-0 top-full mt-1 w-36 bg-soc-card border border-soc-border rounded-lg shadow-lg z-10 py-1">
                              {SUBSCRIPTION_OPTIONS.map((opt) => (
                                <button
                                  key={opt}
                                  onClick={() => handleSubscriptionChange(user, opt)}
                                  className={`w-full text-left px-3 py-1.5 text-sm hover:bg-soc-surface transition-colors ${
                                    user.role === opt ? 'text-soc-accent' : 'text-soc-text'
                                  }`}
                                >
                                  {opt.charAt(0).toUpperCase() + opt.slice(1)}
                                  {user.role === opt && ' (current)'}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-soc-border">
            <span className="text-sm text-soc-muted">Page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="soc-btn-ghost !py-1.5 !px-3 disabled:opacity-30"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="soc-btn-ghost !py-1.5 !px-3 disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}
