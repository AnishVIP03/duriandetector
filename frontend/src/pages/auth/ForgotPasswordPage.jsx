/**
 * Forgot password page — US-06.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, Loader2, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { authAPI } from '../../api/auth';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authAPI.requestPasswordReset(email);
      setSent(true);
      toast.success('Reset link sent! Check your email.');
    } catch {
      toast.error('Something went wrong. Try again.');
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-4"
      >
        <CheckCircle className="w-16 h-16 text-soc-success mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Check Your Email</h2>
        <p className="text-soc-muted text-sm mb-6">
          If an account exists for <strong className="text-white">{email}</strong>,
          we&apos;ve sent a password reset link.
        </p>
        <Link to="/login" className="text-soc-accent hover:underline text-sm flex items-center justify-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Back to login
        </Link>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <h2 className="text-2xl font-bold text-white mb-1">Reset Password</h2>
      <p className="text-soc-muted text-sm mb-6">
        Enter your email and we&apos;ll send you a reset link.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-soc-muted mb-1.5">Email</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-soc-muted" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="soc-input pl-10"
              placeholder="you@example.com"
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
            'Send Reset Link'
          )}
        </button>
      </form>

      <p className="text-sm text-soc-muted text-center mt-6">
        <Link to="/login" className="text-soc-accent hover:underline flex items-center justify-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Back to login
        </Link>
      </p>
    </motion.div>
  );
}
