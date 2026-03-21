/**
 * Packet Inspector Page — Real-time network packet viewer.
 * WebSocket-driven live packet stream with protocol filtering,
 * detailed packet inspection, and capture controls.
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Network, Play, Square, Filter, Search, Wifi,
  ChevronDown, ChevronRight, X, RefreshCw, ArrowRight
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useWebSocket } from '../../hooks/useWebSocket';
import { captureAPI } from '../../api/alerts';

const MAX_PACKETS = 200;

const PROTOCOL_COLORS = {
  TCP: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
  UDP: 'text-green-400 bg-green-500/10 border-green-500/30',
  ICMP: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
  HTTP: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
  DNS: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
  SSH: 'text-orange-400 bg-orange-500/10 border-orange-500/30',
  FTP: 'text-pink-400 bg-pink-500/10 border-pink-500/30',
  OTHER: 'text-soc-muted bg-soc-surface border-soc-border',
};

function getProtocolColor(protocol) {
  return PROTOCOL_COLORS[protocol?.toUpperCase()] || PROTOCOL_COLORS.OTHER;
}

// ---------------------------------------------------------------------------
// Packet Detail Panel
// ---------------------------------------------------------------------------
function PacketDetail({ packet, onClose }) {
  if (!packet) return null;

  const fields = [
    { label: 'Timestamp', value: new Date(packet.timestamp).toLocaleString() },
    { label: 'Source IP', value: packet.src_ip },
    { label: 'Source Port', value: packet.src_port ?? 'N/A' },
    { label: 'Destination IP', value: packet.dst_ip },
    { label: 'Destination Port', value: packet.dst_port ?? 'N/A' },
    { label: 'Protocol', value: packet.protocol },
    { label: 'Length', value: packet.length ? `${packet.length} bytes` : 'N/A' },
    { label: 'Flags', value: packet.flags || 'N/A' },
    { label: 'TTL', value: packet.ttl ?? 'N/A' },
    { label: 'Window Size', value: packet.window_size ?? 'N/A' },
    { label: 'Checksum', value: packet.checksum || 'N/A' },
    { label: 'Sequence #', value: packet.seq_num ?? 'N/A' },
    { label: 'Ack #', value: packet.ack_num ?? 'N/A' },
  ];

  // Include any extra features from the ML pipeline
  const extraFeatures = Object.entries(packet).filter(
    ([key]) => !['id', 'timestamp', 'src_ip', 'src_port', 'dst_ip', 'dst_port',
      'protocol', 'length', 'flags', 'ttl', 'window_size', 'checksum',
      'seq_num', 'ack_num', 'raw_payload', 'type'].includes(key)
  );

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="soc-card sticky top-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Search className="w-4 h-4 text-soc-accent" />
          Packet Details
        </h3>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-soc-surface text-soc-muted hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-2">
        {fields.map(({ label, value }) => (
          <div key={label} className="flex items-center justify-between py-1.5 border-b border-soc-border/50">
            <span className="text-xs text-soc-muted">{label}</span>
            <span className="text-xs font-mono text-soc-text">{value}</span>
          </div>
        ))}
      </div>

      {/* Extra extracted features */}
      {extraFeatures.length > 0 && (
        <div className="mt-4 pt-4 border-t border-soc-border">
          <p className="text-xs text-soc-muted uppercase tracking-wider font-semibold mb-2">
            Extracted Features
          </p>
          <div className="space-y-1.5">
            {extraFeatures.map(([key, value]) => (
              <div key={key} className="flex items-center justify-between py-1">
                <span className="text-xs text-soc-muted">{key}</span>
                <span className="text-xs font-mono text-soc-text max-w-[200px] truncate">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Raw payload preview */}
      {packet.raw_payload && (
        <div className="mt-4 pt-4 border-t border-soc-border">
          <p className="text-xs text-soc-muted uppercase tracking-wider font-semibold mb-2">
            Raw Payload
          </p>
          <pre className="text-xs font-mono text-soc-muted bg-soc-surface rounded-lg p-3 overflow-x-auto max-h-32 overflow-y-auto">
            {packet.raw_payload}
          </pre>
        </div>
      )}
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------
export default function PacketInspectorPage() {
  const [packets, setPackets] = useState([]);
  const [selectedPacket, setSelectedPacket] = useState(null);
  const [capturing, setCapturing] = useState(false);
  const [filters, setFilters] = useState({ protocol: '', src_ip: '', dst_ip: '' });
  const [showFilters, setShowFilters] = useState(false);
  const [packetRate, setPacketRate] = useState(0);
  const packetCountRef = useRef(0);
  const listRef = useRef(null);

  // Track packet rate (packets per second)
  useEffect(() => {
    const interval = setInterval(() => {
      setPacketRate(packetCountRef.current);
      packetCountRef.current = 0;
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const handlePacketMessage = useCallback((data) => {
    packetCountRef.current += 1;
    setPackets((prev) => {
      const updated = [data, ...prev];
      if (updated.length > MAX_PACKETS) {
        return updated.slice(0, MAX_PACKETS);
      }
      return updated;
    });
  }, []);

  const { isConnected, connect, disconnect } = useWebSocket('ws/packets/', {
    onMessage: handlePacketMessage,
    autoConnect: false,
  });

  const [simulating, setSimulating] = useState(false);

  const handleStartCapture = async () => {
    try {
      await captureAPI.start({ duration: 300 });
      connect();
      setCapturing(true);
      toast.success('Packet capture started');
    } catch (err) {
      // If real capture fails (Celery not running, permissions, etc.),
      // fall back to simulation mode automatically.
      try {
        await captureAPI.simulate({ duration: 120, rate: 5 });
        connect();
        setCapturing(true);
        setSimulating(true);
        toast.success('Packet simulation started (demo mode)');
      } catch (simErr) {
        toast.error(simErr.response?.data?.error || 'Failed to start capture');
      }
    }
  };

  const handleStopCapture = async () => {
    try {
      if (simulating) {
        await captureAPI.stopSimulate();
      } else {
        await captureAPI.stop();
      }
      disconnect();
      setCapturing(false);
      setSimulating(false);
      toast.success('Capture stopped');
    } catch {
      // Force-disconnect even if the stop request fails
      disconnect();
      setCapturing(false);
      setSimulating(false);
      toast.error('Failed to stop capture');
    }
  };

  const handleStartSimulation = async () => {
    try {
      await captureAPI.simulate({ duration: 120, rate: 5 });
      connect();
      setCapturing(true);
      setSimulating(true);
      toast.success('Packet simulation started');
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to start simulation');
    }
  };

  const clearPackets = () => {
    setPackets([]);
    setSelectedPacket(null);
  };

  // Filter packets
  const filteredPackets = packets.filter((pkt) => {
    if (filters.protocol && pkt.protocol?.toUpperCase() !== filters.protocol.toUpperCase()) {
      return false;
    }
    if (filters.src_ip && !pkt.src_ip?.includes(filters.src_ip)) {
      return false;
    }
    if (filters.dst_ip && !pkt.dst_ip?.includes(filters.dst_ip)) {
      return false;
    }
    return true;
  });

  const hasActiveFilters = Object.values(filters).some(Boolean);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Network className="w-6 h-6 text-soc-accent" />
            Packet Inspector
          </h1>
          <p className="text-sm text-soc-muted mt-1">
            Real-time network packet capture and analysis
          </p>
        </div>
        <div className="flex items-center gap-2">
          {capturing ? (
            <button onClick={handleStopCapture} className="soc-btn-danger !py-2 flex items-center gap-2">
              <Square className="w-4 h-4" /> {simulating ? 'Stop Simulation' : 'Stop Capture'}
            </button>
          ) : (
            <>
              <button onClick={handleStartCapture} className="soc-btn-primary !py-2 flex items-center gap-2">
                <Play className="w-4 h-4" /> Start Capture
              </button>
              <button onClick={handleStartSimulation} className="soc-btn-ghost !py-2 flex items-center gap-2 border-soc-accent text-soc-accent">
                <Wifi className="w-4 h-4" /> Simulate
              </button>
            </>
          )}
        </div>
      </div>

      {/* Status bar */}
      <div className="flex items-center gap-6 bg-soc-card border border-soc-border rounded-xl px-4 py-3">
        <div className="flex items-center gap-2">
          <div className={`status-dot ${isConnected ? 'status-dot-active' : 'bg-soc-muted'}`} />
          <span className="text-xs text-soc-muted uppercase tracking-wider font-semibold">
            {isConnected ? (simulating ? 'Simulating' : 'Connected') : 'Disconnected'}
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm text-soc-muted">
          <Wifi className="w-4 h-4" />
          <span className="font-mono text-soc-text">{packetRate}</span>
          <span className="text-xs">pkt/s</span>
        </div>
        <div className="text-sm text-soc-muted">
          <span className="font-mono text-soc-text">{packets.length}</span>
          <span className="text-xs ml-1">packets in buffer</span>
        </div>
        <div className="flex-1" />
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`soc-btn-ghost !py-1.5 !px-3 flex items-center gap-2 text-xs ${
            showFilters ? 'border-soc-accent text-soc-accent' : ''
          }`}
        >
          <Filter className="w-3.5 h-3.5" />
          Filters
          {hasActiveFilters && <span className="w-2 h-2 rounded-full bg-soc-accent" />}
        </button>
        <button onClick={clearPackets} className="soc-btn-ghost !py-1.5 !px-3 text-xs flex items-center gap-2">
          <RefreshCw className="w-3.5 h-3.5" />
          Clear
        </button>
      </div>

      {/* Filters */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="soc-card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-white">Filter Packets</h3>
                {hasActiveFilters && (
                  <button
                    onClick={() => setFilters({ protocol: '', src_ip: '', dst_ip: '' })}
                    className="text-xs text-soc-accent flex items-center gap-1"
                  >
                    <X className="w-3 h-3" /> Clear all
                  </button>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-xs text-soc-muted mb-1 block">Protocol</label>
                  <select
                    value={filters.protocol}
                    onChange={(e) => setFilters({ ...filters, protocol: e.target.value })}
                    className="soc-input !py-2"
                  >
                    <option value="">All Protocols</option>
                    <option value="TCP">TCP</option>
                    <option value="UDP">UDP</option>
                    <option value="ICMP">ICMP</option>
                    <option value="HTTP">HTTP</option>
                    <option value="DNS">DNS</option>
                    <option value="SSH">SSH</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-soc-muted mb-1 block">Source IP</label>
                  <input
                    type="text"
                    value={filters.src_ip}
                    onChange={(e) => setFilters({ ...filters, src_ip: e.target.value })}
                    className="soc-input !py-2"
                    placeholder="e.g. 192.168.1"
                  />
                </div>
                <div>
                  <label className="text-xs text-soc-muted mb-1 block">Destination IP</label>
                  <input
                    type="text"
                    value={filters.dst_ip}
                    onChange={(e) => setFilters({ ...filters, dst_ip: e.target.value })}
                    className="soc-input !py-2"
                    placeholder="e.g. 10.0.1"
                  />
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main content: packet list + detail */}
      <div className={`grid gap-6 ${selectedPacket ? 'grid-cols-1 lg:grid-cols-3' : 'grid-cols-1'}`}>
        {/* Packet list */}
        <div className={selectedPacket ? 'lg:col-span-2' : ''}>
          <div className="soc-card overflow-hidden !p-0">
            <div className="overflow-x-auto" ref={listRef}>
              <table className="w-full">
                <thead>
                  <tr className="border-b border-soc-border">
                    <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Time</th>
                    <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Source</th>
                    <th className="text-center text-xs font-medium text-soc-muted uppercase tracking-wider px-2 py-3"></th>
                    <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Destination</th>
                    <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Protocol</th>
                    <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Length</th>
                    <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">Flags</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-soc-border">
                  {filteredPackets.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-16 text-soc-muted">
                        <Network className="w-12 h-12 mx-auto mb-3 opacity-20" />
                        <p className="text-lg font-medium">No packets captured</p>
                        <p className="text-sm mt-1">
                          {capturing
                            ? 'Waiting for network traffic...'
                            : 'Start a capture session to begin inspecting packets.'
                          }
                        </p>
                      </td>
                    </tr>
                  ) : (
                    filteredPackets.map((pkt, idx) => {
                      const protoColor = getProtocolColor(pkt.protocol);
                      const isSelected = selectedPacket === pkt;

                      return (
                        <motion.tr
                          key={pkt.id || idx}
                          initial={{ opacity: 0, x: -5 }}
                          animate={{ opacity: 1, x: 0 }}
                          className={`cursor-pointer transition-colors ${
                            isSelected
                              ? 'bg-soc-accent/10'
                              : 'hover:bg-soc-surface/50'
                          }`}
                          onClick={() => setSelectedPacket(isSelected ? null : pkt)}
                        >
                          <td className="px-4 py-2.5 text-xs text-soc-muted font-mono whitespace-nowrap">
                            {pkt.timestamp
                              ? new Date(pkt.timestamp).toLocaleTimeString([], {
                                  hour: '2-digit',
                                  minute: '2-digit',
                                  second: '2-digit',
                                  fractionalSecondDigits: 3,
                                })
                              : '--:--:--'
                            }
                          </td>
                          <td className="px-4 py-2.5 text-xs font-mono text-soc-text whitespace-nowrap">
                            {pkt.src_ip}{pkt.src_port ? `:${pkt.src_port}` : ''}
                          </td>
                          <td className="px-2 py-2.5 text-center">
                            <ArrowRight className="w-3 h-3 text-soc-muted inline-block" />
                          </td>
                          <td className="px-4 py-2.5 text-xs font-mono text-soc-text whitespace-nowrap">
                            {pkt.dst_ip}{pkt.dst_port ? `:${pkt.dst_port}` : ''}
                          </td>
                          <td className="px-4 py-2.5">
                            <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium border ${protoColor}`}>
                              {pkt.protocol || 'N/A'}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-xs text-soc-muted">
                            {pkt.length ? `${pkt.length}B` : '--'}
                          </td>
                          <td className="px-4 py-2.5 text-xs text-soc-muted font-mono">
                            {pkt.flags || '--'}
                          </td>
                        </motion.tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Packet detail panel */}
        <AnimatePresence>
          {selectedPacket && (
            <PacketDetail
              packet={selectedPacket}
              onClose={() => setSelectedPacket(null)}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
