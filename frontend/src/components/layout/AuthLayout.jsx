/**
 * Auth layout — wraps login, register, forgot password pages.
 * Centered card with animated background.
 */
import { Outlet, Link } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { motion } from 'framer-motion';

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-soc-bg flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background grid effect */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(59,130,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />

      {/* Glow orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md relative z-10"
      >
        {/* Logo */}
        <Link to="/" className="flex items-center justify-center gap-3 mb-8">
          <Shield className="w-10 h-10 text-soc-accent" />
          <span className="text-2xl font-bold text-white">
            Durian<span className="text-soc-accent">Detector</span>
          </span>
        </Link>

        {/* Card */}
        <div className="soc-card">
          <Outlet />
        </div>
      </motion.div>
    </div>
  );
}
