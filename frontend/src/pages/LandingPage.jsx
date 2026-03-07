/**
 * Landing page — US-01.
 * Immersive hero with spinning 3D globe showing simulated attacks,
 * feature showcase, pricing tiers, and auth CTAs.
 */
import { useEffect, useState, useRef, useMemo, lazy, Suspense } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Shield, Zap, Brain, Globe as GlobeIcon, ArrowRight, Check,
  Activity, Lock, Eye, FileText, Users, Network, Star, Crown,
  ChevronDown
} from 'lucide-react';
import { subscriptionsAPI } from '../api/subscriptions';

const GlobeGL = lazy(() => import('react-globe.gl'));

/* ──────────────────── simulated attack arcs ──────────────────── */
const ATTACK_ARCS = [
  { startLat: 55.75, startLng: 37.62, endLat: 1.35, endLng: 103.82, color: '#ef4444' },
  { startLat: 39.90, startLng: 116.41, endLat: 1.35, endLng: 103.82, color: '#f97316' },
  { startLat: 40.71, startLng: -74.01, endLat: 1.35, endLng: 103.82, color: '#eab308' },
  { startLat: -23.55, startLng: -46.63, endLat: 1.35, endLng: 103.82, color: '#ef4444' },
  { startLat: 50.11, startLng: 8.68, endLat: 1.35, endLng: 103.82, color: '#3b82f6' },
  { startLat: 35.68, startLng: 139.65, endLat: 1.35, endLng: 103.82, color: '#f97316' },
  { startLat: 6.52, startLng: 3.38, endLat: 1.35, endLng: 103.82, color: '#ef4444' },
  { startLat: 52.37, startLng: 4.90, endLat: 1.35, endLng: 103.82, color: '#eab308' },
  { startLat: 37.57, startLng: 126.98, endLat: 1.35, endLng: 103.82, color: '#3b82f6' },
  { startLat: 44.43, startLng: 26.10, endLat: 1.35, endLng: 103.82, color: '#ef4444' },
  { startLat: 10.82, startLng: 106.63, endLat: 1.35, endLng: 103.82, color: '#f97316' },
  { startLat: 47.38, startLng: 8.54, endLat: 1.35, endLng: 103.82, color: '#3b82f6' },
  { startLat: 51.51, startLng: -0.13, endLat: 1.35, endLng: 103.82, color: '#eab308' },
  { startLat: 48.86, startLng: 2.35, endLat: 1.35, endLng: 103.82, color: '#ef4444' },
  { startLat: -33.87, startLng: 151.21, endLat: 1.35, endLng: 103.82, color: '#3b82f6' },
];

/* defence ring points around the target */
const RING_DATA = [{ lat: 1.35, lng: 103.82, maxR: 6, propagationSpeed: 2, repeatPeriod: 1200 }];
const POINT_DATA = [
  { lat: 1.35, lng: 103.82, size: 0.6, color: '#22c55e', label: 'YOU' },
  { lat: 55.75, lng: 37.62, size: 0.3, color: '#ef4444' },
  { lat: 39.90, lng: 116.41, size: 0.3, color: '#ef4444' },
  { lat: 40.71, lng: -74.01, size: 0.25, color: '#f97316' },
  { lat: -23.55, lng: -46.63, size: 0.25, color: '#ef4444' },
  { lat: 35.68, lng: 139.65, size: 0.2, color: '#f97316' },
  { lat: 6.52, lng: 3.38, size: 0.2, color: '#ef4444' },
  { lat: 51.51, lng: -0.13, size: 0.2, color: '#eab308' },
];

/* ──────────────────── features ──────────────────── */
const features = [
  { icon: Shield, title: 'Real-Time Detection', desc: 'Live packet capture with Scapy and ML-powered anomaly detection. Alerts delivered via WebSocket in milliseconds.' },
  { icon: Brain, title: 'AI Security Assistant', desc: 'DurianBot — a local LLM chatbot that analyses alerts, explains MITRE techniques, and recommends mitigations.' },
  { icon: GlobeIcon, title: '3D Attack Globe', desc: 'Interactive globe visualising attack origins worldwide with severity-coded arcs and country-level drill-down.' },
  { icon: Activity, title: 'SOC Dashboard', desc: 'Professional Security Operations Center with risk gauges, severity breakdowns, and hourly trend analysis.' },
  { icon: Network, title: 'Kill Chain Timeline', desc: 'Multi-stage attack correlation mapping alerts to Cyber Kill Chain phases with dynamic risk scoring.' },
  { icon: Eye, title: 'MITRE ATT&CK Heatmap', desc: 'Full framework coverage matrix showing technique frequency, alert counts, and detection gaps.' },
];

/* ──────────────────── pricing configs ──────────────────── */
const PLAN_FEATURES = {
  free: [
    'Real-time alert monitoring',
    'Basic SOC dashboard',
    'Up to 100 alerts/day',
    'Community support',
  ],
  premium: [
    'Everything in Free, plus:',
    'ML model configuration',
    'Incident management',
    'PDF report generation',
    'MITRE ATT&CK mapping',
    'Threat correlation',
    'Unlimited alerts',
    'Email notifications',
  ],
  exclusive: [
    'Everything in Premium, plus:',
    'AI chatbot (DurianBot)',
    '3D attack globe',
    'Attack kill chain analysis',
    'Custom alert rules',
    'Team management (up to 25)',
    'Advanced reporting & export',
    'Priority support SLA',
    'Audit logging',
  ],
};

const PLAN_ICONS = { free: Shield, premium: Star, exclusive: Crown };
const PLAN_COLORS = {
  free: { accent: 'text-blue-400', bg: 'bg-blue-500/10', ring: 'ring-blue-500/20', btn: 'bg-soc-surface hover:bg-soc-border text-soc-text border border-soc-border' },
  premium: { accent: 'text-soc-accent', bg: 'bg-soc-accent/10', ring: 'ring-soc-accent/30', btn: 'bg-soc-accent hover:bg-blue-600 text-white' },
  exclusive: { accent: 'text-yellow-400', bg: 'bg-yellow-500/10', ring: 'ring-yellow-500/20', btn: 'bg-yellow-500 hover:bg-yellow-600 text-black' },
};

/* ──────────────────── live stats counter ──────────────────── */
function AnimatedCounter({ end, duration = 2, suffix = '' }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = end / (duration * 60);
    const timer = setInterval(() => {
      start += step;
      if (start >= end) { setVal(end); clearInterval(timer); }
      else setVal(Math.floor(start));
    }, 1000 / 60);
    return () => clearInterval(timer);
  }, [end, duration]);
  return <span>{val.toLocaleString()}{suffix}</span>;
}

/* ──────────────────── component ──────────────────── */
export default function LandingPage() {
  const [plans, setPlans] = useState([]);
  const globeRef = useRef();

  useEffect(() => {
    subscriptionsAPI.getPlans()
      .then((res) => {
        const data = res.data;
        setPlans(Array.isArray(data) ? data : data.results || []);
      })
      .catch(() => {
        setPlans([
          { name: 'free', display_name: 'Free', price: '0.00', billing_cycle: 'forever', description: 'Basic monitoring for individuals.' },
          { name: 'premium', display_name: 'Premium', price: '29.99', billing_cycle: 'monthly', description: 'Advanced detection for professionals.' },
          { name: 'exclusive', display_name: 'Exclusive', price: '99.99', billing_cycle: 'monthly', description: 'Enterprise-grade security platform.' },
        ]);
      });
  }, []);

  /* auto-rotate globe */
  useEffect(() => {
    if (globeRef.current) {
      globeRef.current.controls().autoRotate = true;
      globeRef.current.controls().autoRotateSpeed = 0.8;
      globeRef.current.controls().enableZoom = false;
      globeRef.current.pointOfView({ lat: 15, lng: 80, altitude: 2.2 });
    }
  });

  const arcsData = useMemo(() => ATTACK_ARCS.map((a, i) => ({
    ...a,
    dashLength: 0.6,
    dashGap: 0.3,
    dashAnimateTime: 2000 + i * 300,
    stroke: 0.5,
  })), []);

  return (
    <div className="min-h-screen bg-soc-bg relative overflow-hidden">

      {/* ═══════════ BACKGROUND GLOBE ═══════════ */}
      <div className="absolute inset-0 flex items-center justify-center opacity-40 pointer-events-none select-none">
        <Suspense fallback={null}>
          <GlobeGL
            ref={globeRef}
            width={1000}
            height={1000}
            backgroundColor="rgba(0,0,0,0)"
            globeImageUrl=""
            showAtmosphere={true}
            atmosphereColor="#3b82f6"
            atmosphereAltitude={0.2}
            hexPolygonsData={[]}
            arcsData={arcsData}
            arcColor={'color'}
            arcDashLength={'dashLength'}
            arcDashGap={'dashGap'}
            arcDashAnimateTime={'dashAnimateTime'}
            arcStroke={'stroke'}
            pointsData={POINT_DATA}
            pointAltitude={0.01}
            pointRadius={'size'}
            pointColor={'color'}
            ringsData={RING_DATA}
            ringColor={() => t => `rgba(34,197,94,${1 - t})`}
            ringMaxRadius={'maxR'}
            ringPropagationSpeed={'propagationSpeed'}
            ringRepeatPeriod={'repeatPeriod'}
          />
        </Suspense>
      </div>

      {/* grid overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(59,130,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />
      {/* vignette */}
      <div className="absolute inset-0 bg-gradient-to-b from-soc-bg via-transparent to-soc-bg" />

      {/* ═══════════ NAV ═══════════ */}
      <nav className="relative z-20 max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="w-9 h-9 text-soc-accent" />
          <span className="text-xl font-bold text-white">
            Durian<span className="text-soc-accent">Detector</span>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login" className="text-soc-muted hover:text-white transition-colors text-sm px-4 py-2">
            Sign In
          </Link>
          <Link to="/register" className="soc-btn-primary text-sm !py-2 !px-5 flex items-center gap-2">
            <Shield className="w-4 h-4" /> Get Started Free
          </Link>
        </div>
      </nav>

      {/* ═══════════ HERO ═══════════ */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 pt-16 pb-24 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="inline-flex items-center gap-2 bg-soc-accent/10 border border-soc-accent/20 rounded-full px-4 py-1.5 mb-6">
            <Zap className="w-4 h-4 text-soc-accent" />
            <span className="text-sm text-soc-accent font-medium">FYP-26-S1-08 — ML-Powered Intrusion Detection System</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold text-white leading-tight mb-6">
            Detect &amp; Defend
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-indigo-400">
              Your Network in Real-Time
            </span>
          </h1>

          <p className="text-lg md:text-xl text-soc-muted max-w-3xl mx-auto mb-10 leading-relaxed">
            DurianDetector is a web-based Intrusion Detection System that combines
            <span className="text-white font-medium"> live packet capture</span>,
            <span className="text-white font-medium"> machine learning</span>, and an
            <span className="text-white font-medium"> AI security chatbot</span> to
            monitor, detect, and respond to network threats — all from your browser.
          </p>

          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link to="/register" className="soc-btn-primary flex items-center gap-2 text-lg !py-3 !px-8">
              Start Monitoring Free <ArrowRight className="w-5 h-5" />
            </Link>
            <Link to="/login" className="soc-btn-ghost text-lg !py-3 !px-8 flex items-center gap-2">
              <Lock className="w-4 h-4" /> Sign In
            </Link>
          </div>
        </motion.div>

        {/* Live stats bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="mt-16 flex items-center justify-center gap-8 md:gap-16 flex-wrap"
        >
          {[
            { label: 'Threats Detected', value: 12847, suffix: '+' },
            { label: 'Attacks Blocked', value: 9432, suffix: '+' },
            { label: 'ML Models Active', value: 3, suffix: '' },
            { label: 'Countries Tracked', value: 42, suffix: '' },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <p className="text-2xl md:text-3xl font-bold text-white">
                <AnimatedCounter end={s.value} suffix={s.suffix} />
              </p>
              <p className="text-xs text-soc-muted uppercase tracking-wider mt-1">{s.label}</p>
            </div>
          ))}
        </motion.div>

        {/* scroll hint */}
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ repeat: Infinity, duration: 2 }}
          className="mt-12"
        >
          <ChevronDown className="w-6 h-6 text-soc-muted mx-auto" />
        </motion.div>
      </section>

      {/* ═══════════ WHAT IS DURIAN DETECTOR ═══════════ */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 pb-24">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            What is DurianDetector?
          </h2>
          <p className="text-soc-muted max-w-3xl mx-auto text-lg leading-relaxed">
            A comprehensive web-based Network Intrusion Detection System designed for
            Security Operations Centers. It captures live network traffic using Scapy,
            analyses it with trained ML models (Random Forest, SVM, Isolation Forest),
            maps threats to the MITRE ATT&CK framework, and provides an AI-powered
            chatbot for real-time threat investigation. Built with Django, React, and
            WebSockets for a seamless real-time experience.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              className="soc-card hover:soc-glow transition-all duration-300 group"
            >
              <div className="w-12 h-12 rounded-lg bg-soc-accent/10 flex items-center justify-center mb-4 group-hover:bg-soc-accent/20 transition-colors">
                <f.icon className="w-6 h-6 text-soc-accent" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-sm text-soc-muted leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ═══════════ PRICING ═══════════ */}
      <section id="pricing" className="relative z-10 max-w-7xl mx-auto px-6 pb-32">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Choose Your Security Tier
          </h2>
          <p className="text-soc-muted text-lg">
            Start free. Upgrade anytime to unlock advanced detection capabilities.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {['free', 'premium', 'exclusive'].map((tierName, i) => {
            const plan = plans.find((p) => (p.name || '').toLowerCase() === tierName);
            const Icon = PLAN_ICONS[tierName];
            const colors = PLAN_COLORS[tierName];
            const featureList = PLAN_FEATURES[tierName];
            const isPremium = tierName === 'premium';

            return (
              <motion.div
                key={tierName}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.12 }}
                className={`soc-card relative flex flex-col ${isPremium ? 'ring-1 ring-soc-accent/30 soc-glow scale-[1.02]' : ''}`}
              >
                {isPremium && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-soc-accent text-white text-xs font-bold px-4 py-1 rounded-full">
                    MOST POPULAR
                  </div>
                )}

                <div className="text-center mb-6 pt-2">
                  <div className={`w-14 h-14 rounded-xl mx-auto mb-3 flex items-center justify-center ${colors.bg}`}>
                    <Icon className={`w-7 h-7 ${colors.accent}`} />
                  </div>
                  <h3 className="text-xl font-bold text-white capitalize">{tierName}</h3>
                  <p className="text-3xl font-extrabold text-white mt-2">
                    {plan && Number(plan.price) === 0 ? 'Free' : `$${plan?.price || (tierName === 'premium' ? '29.99' : '99.99')}`}
                    {plan && Number(plan.price) > 0 && (
                      <span className="text-sm text-soc-muted font-normal">/mo</span>
                    )}
                  </p>
                  <p className="text-xs text-soc-muted mt-1">
                    {plan?.description || ''}
                  </p>
                </div>

                <ul className="flex-1 space-y-2.5 mb-8">
                  {featureList.map((feat, j) => (
                    <li key={j} className={`flex items-start gap-2 text-sm ${j === 0 && tierName !== 'free' ? 'font-semibold text-white' : 'text-soc-text'}`}>
                      {j === 0 && tierName !== 'free' ? null : (
                        <Check className={`w-4 h-4 mt-0.5 shrink-0 ${colors.accent}`} />
                      )}
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  to="/register"
                  className={`block text-center py-3 rounded-lg font-semibold transition-all ${colors.btn}`}
                >
                  {tierName === 'free' ? 'Get Started Free' : `Upgrade to ${tierName.charAt(0).toUpperCase() + tierName.slice(1)}`}
                </Link>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* ═══════════ CTA ═══════════ */}
      <section className="relative z-10 max-w-4xl mx-auto px-6 pb-24 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="soc-card soc-glow !p-12"
        >
          <Shield className="w-12 h-12 text-soc-accent mx-auto mb-4" />
          <h2 className="text-3xl font-bold text-white mb-3">Ready to Secure Your Network?</h2>
          <p className="text-soc-muted mb-8 max-w-lg mx-auto">
            Create your free account in seconds. No credit card required.
            Start monitoring your network immediately.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link to="/register" className="soc-btn-primary flex items-center gap-2 text-lg !py-3 !px-8">
              Create Free Account <ArrowRight className="w-5 h-5" />
            </Link>
            <Link to="/login" className="soc-btn-ghost text-lg !py-3 !px-6">
              Sign In
            </Link>
          </div>
        </motion.div>
      </section>

      {/* ═══════════ FOOTER ═══════════ */}
      <footer className="relative z-10 border-t border-soc-border py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-soc-accent" />
            <span className="text-sm text-soc-muted">
              DurianDetector IDS — FYP-26-S1-08 &copy; 2026
            </span>
          </div>
          <p className="text-xs text-soc-muted">
            Built with Django &bull; React &bull; Scapy &bull; scikit-learn &bull; Ollama &bull; WebSockets
          </p>
        </div>
      </footer>
    </div>
  );
}
