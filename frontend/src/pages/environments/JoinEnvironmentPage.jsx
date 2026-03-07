/**
 * Join Environment page — US-04.
 * Join via PIN or invitation code.
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, Users, KeyRound, Link2, Loader2, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';
import { environmentsAPI } from '../../api/environments';
import { useEnvironmentStore } from '../../store/environmentStore';

export default function JoinEnvironmentPage() {
  const [method, setMethod] = useState('pin'); // 'pin' or 'code'
  const [pin, setPin] = useState('');
  const [invitationCode, setInvitationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const { setEnvironment } = useEnvironmentStore();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = method === 'pin' ? { pin } : { invitation_code: invitationCode };
      const { data } = await environmentsAPI.join(payload);
      setEnvironment(data.environment);
      toast.success(data.message);
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to join environment.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-soc-bg flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(59,130,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative z-10"
      >
        <div className="flex items-center justify-center gap-3 mb-8">
          <Shield className="w-10 h-10 text-soc-accent" />
          <span className="text-2xl font-bold text-white">
            Durian<span className="text-soc-accent">Detector</span>
          </span>
        </div>

        <div className="soc-card">
          <h2 className="text-2xl font-bold text-white mb-1">Join Environment</h2>
          <p className="text-soc-muted text-sm mb-6">
            Enter a PIN or invitation code to join your team.
          </p>

          {/* Method toggle */}
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setMethod('pin')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                method === 'pin'
                  ? 'bg-soc-accent/10 text-soc-accent border border-soc-accent/30'
                  : 'bg-soc-surface text-soc-muted border border-soc-border hover:text-white'
              }`}
            >
              <KeyRound className="w-4 h-4" />
              PIN Code
            </button>
            <button
              onClick={() => setMethod('code')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
                method === 'code'
                  ? 'bg-soc-accent/10 text-soc-accent border border-soc-accent/30'
                  : 'bg-soc-surface text-soc-muted border border-soc-border hover:text-white'
              }`}
            >
              <Link2 className="w-4 h-4" />
              Invite Code
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {method === 'pin' ? (
              <div>
                <label className="block text-sm text-soc-muted mb-1.5">6-Digit PIN</label>
                <input
                  type="text"
                  value={pin}
                  onChange={(e) => setPin(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="soc-input text-center text-2xl tracking-[0.5em] font-mono"
                  placeholder="000000"
                  maxLength={6}
                  required
                />
              </div>
            ) : (
              <div>
                <label className="block text-sm text-soc-muted mb-1.5">Invitation Code</label>
                <input
                  type="text"
                  value={invitationCode}
                  onChange={(e) => setInvitationCode(e.target.value)}
                  className="soc-input font-mono text-sm"
                  placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                  required
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="soc-btn-primary w-full flex items-center justify-center gap-2"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Users className="w-5 h-5" />
                  Join Environment
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-soc-border text-center">
            <Link
              to="/setup/create"
              className="text-soc-accent hover:underline text-sm flex items-center justify-center gap-1"
            >
              <ArrowLeft className="w-4 h-4" /> Create a new environment instead
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
