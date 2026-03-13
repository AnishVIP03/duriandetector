/**
 * Login page — US-05.
 *
 * Provides email/password authentication form. On successful login,
 * stores JWT tokens and user data in the auth store (Zustand) and
 * redirects to the main dashboard. Displays server-side validation
 * errors via toast notifications.
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LogIn, Mail, Lock, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { authAPI } from '../../api/auth';
import { useAuthStore } from '../../store/authStore';

export default function LoginPage() {
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();  // Zustand action to persist user + tokens
  const navigate = useNavigate();

  /** Update form state as user types in email/password fields. */
  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  /** Submit login credentials to the API, store tokens on success. */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await authAPI.login(form);
      login(data.user, data.tokens);  // Persist auth state
      toast.success('Welcome back!');
      navigate('/dashboard');
    } catch (err) {
      // Extract the most specific error message from the API response
      const msg = err.response?.data?.non_field_errors?.[0]
        || err.response?.data?.detail
        || 'Login failed. Check your credentials.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <h2 className="text-2xl font-bold text-white mb-1">Welcome Back</h2>
      <p className="text-soc-muted text-sm mb-6">Sign in to your IDS dashboard</p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-soc-muted mb-1.5">Email</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-soc-muted" />
            <input
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              className="soc-input pl-10"
              placeholder="you@example.com"
              required
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-sm text-soc-muted">Password</label>
            <Link to="/forgot-password" className="text-xs text-soc-accent hover:underline">
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-soc-muted" />
            <input
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              className="soc-input pl-10"
              placeholder="Enter your password"
              required
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="soc-btn-primary w-full flex items-center justify-center gap-2"
        >
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>
              <LogIn className="w-5 h-5" />
              Sign In
            </>
          )}
        </button>
      </form>

      <p className="text-sm text-soc-muted text-center mt-6">
        Don&apos;t have an account?{' '}
        <Link to="/register" className="text-soc-accent hover:underline">
          Create one
        </Link>
      </p>
    </motion.div>
  );
}
