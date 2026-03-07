/**
 * Registration page — US-02.
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus, Mail, Lock, User, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { authAPI } from '../../api/auth';
import { useAuthStore } from '../../store/authStore';

export default function RegisterPage() {
  const [form, setForm] = useState({
    email: '',
    username: '',
    first_name: '',
    last_name: '',
    password: '',
    password_confirm: '',
  });
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.password_confirm) {
      toast.error('Passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      const { data } = await authAPI.register(form);
      login(data.user, data.tokens);
      toast.success('Account created! Set up your environment.');
      navigate('/setup/create');
    } catch (err) {
      const errors = err.response?.data;
      if (errors) {
        const firstError = Object.values(errors).flat()[0];
        toast.error(typeof firstError === 'string' ? firstError : 'Registration failed.');
      } else {
        toast.error('Registration failed. Try again.');
      }
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
      <h2 className="text-2xl font-bold text-white mb-1">Create Account</h2>
      <p className="text-soc-muted text-sm mb-6">Start monitoring your network for threats</p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm text-soc-muted mb-1.5">First Name</label>
            <input
              name="first_name"
              value={form.first_name}
              onChange={handleChange}
              className="soc-input"
              placeholder="John"
            />
          </div>
          <div>
            <label className="block text-sm text-soc-muted mb-1.5">Last Name</label>
            <input
              name="last_name"
              value={form.last_name}
              onChange={handleChange}
              className="soc-input"
              placeholder="Doe"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm text-soc-muted mb-1.5">Username</label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-soc-muted" />
            <input
              name="username"
              value={form.username}
              onChange={handleChange}
              className="soc-input pl-10"
              placeholder="johndoe"
              required
            />
          </div>
        </div>

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
          <label className="block text-sm text-soc-muted mb-1.5">Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-soc-muted" />
            <input
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              className="soc-input pl-10"
              placeholder="Min. 8 characters"
              required
              minLength={8}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm text-soc-muted mb-1.5">Confirm Password</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-soc-muted" />
            <input
              name="password_confirm"
              type="password"
              value={form.password_confirm}
              onChange={handleChange}
              className="soc-input pl-10"
              placeholder="Repeat your password"
              required
              minLength={8}
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
              <UserPlus className="w-5 h-5" />
              Create Account
            </>
          )}
        </button>
      </form>

      <p className="text-sm text-soc-muted text-center mt-6">
        Already have an account?{' '}
        <Link to="/login" className="text-soc-accent hover:underline">
          Sign in
        </Link>
      </p>
    </motion.div>
  );
}
