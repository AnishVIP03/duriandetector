/**
 * Create Environment page — US-03.
 * After registration, users create or join an environment.
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, Plus, Users, Loader2, Wifi } from 'lucide-react';
import toast from 'react-hot-toast';
import { environmentsAPI } from '../../api/environments';
import { useEnvironmentStore } from '../../store/environmentStore';

export default function CreateEnvironmentPage() {
  const [form, setForm] = useState({
    name: '',
    description: '',
    organisation: '',
    network_interface: 'eth0',
  });
  const [loading, setLoading] = useState(false);
  const { setEnvironment } = useEnvironmentStore();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await environmentsAPI.create(form);
      setEnvironment(data);
      toast.success(`Environment "${data.name}" created! PIN: ${data.pin}`);
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create environment.');
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
        className="w-full max-w-lg relative z-10"
      >
        <div className="flex items-center justify-center gap-3 mb-8">
          <Shield className="w-10 h-10 text-soc-accent" />
          <span className="text-2xl font-bold text-white">
            Durian<span className="text-soc-accent">Detector</span>
          </span>
        </div>

        <div className="soc-card">
          <h2 className="text-2xl font-bold text-white mb-1">Create Environment</h2>
          <p className="text-soc-muted text-sm mb-6">
            Set up a workspace for your team to monitor network traffic.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-soc-muted mb-1.5">Environment Name</label>
              <input
                name="name"
                value={form.name}
                onChange={handleChange}
                className="soc-input"
                placeholder="e.g. Production Network"
                required
              />
            </div>

            <div>
              <label className="block text-sm text-soc-muted mb-1.5">Organisation</label>
              <input
                name="organisation"
                value={form.organisation}
                onChange={handleChange}
                className="soc-input"
                placeholder="e.g. Acme Corp"
              />
            </div>

            <div>
              <label className="block text-sm text-soc-muted mb-1.5">Description</label>
              <textarea
                name="description"
                value={form.description}
                onChange={handleChange}
                className="soc-input resize-none"
                rows={3}
                placeholder="What does this environment monitor?"
              />
            </div>

            <div>
              <label className="block text-sm text-soc-muted mb-1.5">
                <Wifi className="w-4 h-4 inline mr-1" />
                Network Interface
              </label>
              <select
                name="network_interface"
                value={form.network_interface}
                onChange={handleChange}
                className="soc-input"
              >
                <option value="eth0">eth0 (Ethernet)</option>
                <option value="en0">en0 (macOS Ethernet/Wi-Fi)</option>
                <option value="wlan0">wlan0 (Wi-Fi)</option>
                <option value="lo">lo (Loopback)</option>
              </select>
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
                  <Plus className="w-5 h-5" />
                  Create Environment
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-soc-border text-center">
            <p className="text-sm text-soc-muted mb-3">Already have an environment?</p>
            <Link
              to="/setup/join"
              className="soc-btn-ghost w-full flex items-center justify-center gap-2"
            >
              <Users className="w-5 h-5" />
              Join Existing Environment
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
