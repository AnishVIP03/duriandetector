/**
 * Subscription Management page — US-05.
 * View current plan, compare pricing tiers, and upgrade subscriptions.
 */
import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  CreditCard, Star, Check, Zap, Crown,
  ArrowRight, Shield, X, Lock
} from 'lucide-react';
import toast from 'react-hot-toast';
import { subscriptionsAPI } from '../../api/subscriptions';
import { useAuthStore } from '../../store/authStore';

const PLAN_CONFIG = {
  free: {
    icon: Shield,
    color: 'text-blue-400',
    borderColor: 'border-blue-500/30',
    bgAccent: 'bg-blue-500/10',
    badgeBg: 'bg-blue-500/15 text-blue-400',
    btnClass: 'soc-btn-ghost',
  },
  premium: {
    icon: Star,
    color: 'text-soc-accent',
    borderColor: 'border-soc-accent/30',
    bgAccent: 'bg-soc-accent/10',
    badgeBg: 'bg-soc-accent/15 text-soc-accent',
    btnClass: 'soc-btn-primary',
    popular: true,
  },
  exclusive: {
    icon: Crown,
    color: 'text-yellow-400',
    borderColor: 'border-yellow-500/30',
    bgAccent: 'bg-yellow-500/10',
    badgeBg: 'bg-yellow-500/15 text-yellow-400',
    btnClass: 'soc-btn-primary',
  },
};

const TIER_ORDER = ['free', 'premium', 'exclusive'];

/** Feature comparison rows for the bottom table */
const FEATURE_COMPARISON = [
  { label: 'Real-time Alerts', free: true, premium: true, exclusive: true },
  { label: 'Basic Dashboard', free: true, premium: true, exclusive: true },
  { label: 'Packet Analysis', free: false, premium: true, exclusive: true },
  { label: 'ML-based Detection', free: false, premium: true, exclusive: true },
  { label: 'MITRE ATT&CK Mapping', free: false, premium: true, exclusive: true },
  { label: 'Custom Alert Rules', free: false, premium: false, exclusive: true },
  { label: 'Attack Chain Analysis', free: false, premium: false, exclusive: true },
  { label: 'Advanced Reporting', free: false, premium: false, exclusive: true },
  { label: 'AI Chat Assistant', free: false, premium: false, exclusive: true },
  { label: 'Priority Support', free: false, premium: false, exclusive: true },
];

export default function SubscriptionPage() {
  const { user, updateUser } = useAuthStore();
  const [subscription, setSubscription] = useState(null);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(null);
  const [checkoutPlan, setCheckoutPlan] = useState(null);
  const [cardNumber, setCardNumber] = useState('');
  const [cardExpiry, setCardExpiry] = useState('');
  const [cardCvc, setCardCvc] = useState('');
  const [cardName, setCardName] = useState('');
  const [processing, setProcessing] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [subRes, plansRes] = await Promise.all([
        subscriptionsAPI.getMySubscription(),
        subscriptionsAPI.getPlans(),
      ]);
      setSubscription(subRes.data);
      setPlans(plansRes.data.results || plansRes.data);
    } catch (err) {
      console.error('Failed to fetch subscription data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const currentPlanName = (
    subscription?.plan?.name ||
    subscription?.plan_name ||
    'free'
  ).toLowerCase();

  const currentTierIndex = TIER_ORDER.indexOf(currentPlanName);

  const openCheckout = (planName) => {
    setCheckoutPlan(planName);
    setCardNumber('');
    setCardExpiry('');
    setCardCvc('');
    setCardName('');
  };

  const formatCardNumber = (val) => {
    const digits = val.replace(/\D/g, '').slice(0, 16);
    return digits.replace(/(.{4})/g, '$1 ').trim();
  };

  const formatExpiry = (val) => {
    const digits = val.replace(/\D/g, '').slice(0, 4);
    if (digits.length >= 3) return digits.slice(0, 2) + '/' + digits.slice(2);
    return digits;
  };

  const handleCheckoutSubmit = async (e) => {
    e.preventDefault();
    if (!checkoutPlan) return;

    setProcessing(true);

    // Simulate payment processing delay (1.5s)
    await new Promise((r) => setTimeout(r, 1500));

    try {
      await subscriptionsAPI.upgrade(checkoutPlan);
      toast.success(`Payment successful! Upgraded to ${checkoutPlan.charAt(0).toUpperCase() + checkoutPlan.slice(1)}!`);
      updateUser({ subscription_plan: checkoutPlan, role: checkoutPlan });
      setCheckoutPlan(null);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Payment failed. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  const isActive =
    subscription?.is_active ?? subscription?.status === 'active' ?? true;

  const formatDate = (dateStr) => {
    if (!dateStr) return '--';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <CreditCard className="w-6 h-6 text-soc-accent" />
          Subscription
        </h1>
        <p className="text-sm text-soc-muted mt-1">
          Manage your plan and access premium security features
        </p>
      </div>

      {/* Current Plan Card */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="soc-card"
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              PLAN_CONFIG[currentPlanName]?.bgAccent || 'bg-soc-surface'
            }`}>
              {(() => {
                const Icon = PLAN_CONFIG[currentPlanName]?.icon || Shield;
                return (
                  <Icon className={`w-6 h-6 ${
                    PLAN_CONFIG[currentPlanName]?.color || 'text-soc-accent'
                  }`} />
                );
              })()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold text-white">
                  {currentPlanName.charAt(0).toUpperCase() + currentPlanName.slice(1)} Plan
                </h2>
                {isActive && (
                  <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/15 text-green-400 border border-green-500/30">
                    Active
                  </span>
                )}
              </div>
              <p className="text-sm text-soc-muted mt-0.5">
                {subscription?.plan?.description || 'Your current subscription tier'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-sm">
            <div>
              <span className="text-soc-muted block text-xs uppercase tracking-wider">Start Date</span>
              <span className="text-soc-text">
                {formatDate(subscription?.start_date || subscription?.created_at)}
              </span>
            </div>
            <div>
              <span className="text-soc-muted block text-xs uppercase tracking-wider">Expiry Date</span>
              <span className="text-soc-text">
                {formatDate(subscription?.end_date || subscription?.expires_at)}
              </span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Pricing Plans Grid */}
      {loading ? (
        <div className="text-center py-12 text-soc-muted">
          <Zap className="w-8 h-8 mx-auto mb-3 animate-pulse opacity-30" />
          Loading plans...
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {TIER_ORDER.map((tierName, index) => {
            const plan = plans.find(
              (p) => (p.name || '').toLowerCase() === tierName
            );
            const config = PLAN_CONFIG[tierName];
            const Icon = config?.icon || Shield;
            const isCurrent = tierName === currentPlanName;
            const tierIndex = TIER_ORDER.indexOf(tierName);
            const isHigherTier = tierIndex > currentTierIndex;
            const features = plan?.features
              ? typeof plan.features === 'string'
                ? JSON.parse(plan.features)
                : plan.features
              : [];

            return (
              <motion.div
                key={tierName}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`soc-card relative flex flex-col ${
                  isCurrent ? `ring-1 ${config?.borderColor}` : ''
                } ${config?.popular ? `ring-1 ${config?.borderColor}` : ''}`}
              >
                {/* Popular badge */}
                {config?.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="inline-block px-3 py-0.5 rounded-full text-xs font-semibold bg-soc-accent text-soc-bg">
                      Most Popular
                    </span>
                  </div>
                )}

                {/* Current Plan badge */}
                {isCurrent && (
                  <div className="absolute top-3 right-3">
                    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${config?.badgeBg}`}>
                      Current
                    </span>
                  </div>
                )}

                {/* Plan Header */}
                <div className="text-center mb-6 pt-2">
                  <div className={`w-14 h-14 rounded-xl mx-auto mb-3 flex items-center justify-center ${config?.bgAccent}`}>
                    <Icon className={`w-7 h-7 ${config?.color}`} />
                  </div>
                  <h3 className="text-xl font-bold text-white">
                    {tierName.charAt(0).toUpperCase() + tierName.slice(1)}
                  </h3>
                  {plan?.price !== undefined && (
                    <p className="text-2xl font-bold text-white mt-2">
                      {Number(plan.price) === 0 ? (
                        'Free'
                      ) : (
                        <>
                          ${plan.price}
                          <span className="text-sm text-soc-muted font-normal">/mo</span>
                        </>
                      )}
                    </p>
                  )}
                </div>

                {/* Features List */}
                <div className="flex-1 mb-6">
                  <ul className="space-y-2.5">
                    {Array.isArray(features) && features.length > 0 ? (
                      features.map((feature, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <Check className={`w-4 h-4 mt-0.5 shrink-0 ${config?.color}`} />
                          <span className="text-soc-text">{feature}</span>
                        </li>
                      ))
                    ) : (
                      FEATURE_COMPARISON.filter((f) => f[tierName]).map((f, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <Check className={`w-4 h-4 mt-0.5 shrink-0 ${config?.color}`} />
                          <span className="text-soc-text">{f.label}</span>
                        </li>
                      ))
                    )}
                  </ul>
                </div>

                {/* Action Button */}
                <div className="mt-auto">
                  {isCurrent ? (
                    <button
                      disabled
                      className="soc-btn-ghost w-full opacity-60 cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      <Check className="w-4 h-4" />
                      Current Plan
                    </button>
                  ) : isHigherTier ? (
                    <button
                      onClick={() => openCheckout(tierName)}
                      className={`${config?.btnClass} w-full flex items-center justify-center gap-2`}
                    >
                      <ArrowRight className="w-4 h-4" />
                      Upgrade
                    </button>
                  ) : (
                    <button
                      disabled
                      className="soc-btn-ghost w-full opacity-40 cursor-not-allowed"
                    >
                      Downgrade N/A
                    </button>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Payment Checkout Modal */}
      {checkoutPlan && (() => {
        const plan = plans.find((p) => (p.name || '').toLowerCase() === checkoutPlan);
        const config = PLAN_CONFIG[checkoutPlan];
        const Icon = config?.icon || Shield;
        return (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-soc-card border border-soc-border rounded-2xl shadow-2xl max-w-md w-full overflow-hidden"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-soc-border">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${config?.bgAccent}`}>
                    <Icon className={`w-5 h-5 ${config?.color}`} />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">
                      Upgrade to {checkoutPlan.charAt(0).toUpperCase() + checkoutPlan.slice(1)}
                    </h3>
                    <p className="text-xs text-soc-muted">
                      {plan?.price ? `$${plan.price}/month` : ''}
                    </p>
                  </div>
                </div>
                <button onClick={() => setCheckoutPlan(null)} className="text-soc-muted hover:text-white transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Payment Form */}
              <form onSubmit={handleCheckoutSubmit} className="p-6 space-y-4">
                <div>
                  <label className="block text-xs font-medium text-soc-muted mb-1.5 uppercase tracking-wider">Cardholder Name</label>
                  <input
                    type="text"
                    value={cardName}
                    onChange={(e) => setCardName(e.target.value)}
                    placeholder="John Smith"
                    required
                    className="soc-input w-full"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-soc-muted mb-1.5 uppercase tracking-wider">Card Number</label>
                  <div className="relative">
                    <input
                      type="text"
                      value={cardNumber}
                      onChange={(e) => setCardNumber(formatCardNumber(e.target.value))}
                      placeholder="4242 4242 4242 4242"
                      required
                      maxLength={19}
                      className="soc-input w-full pl-10"
                    />
                    <CreditCard className="w-4 h-4 text-soc-muted absolute left-3 top-1/2 -translate-y-1/2" />
                  </div>
                  <p className="text-xs text-soc-muted mt-1">Use 4242 4242 4242 4242 for testing</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-soc-muted mb-1.5 uppercase tracking-wider">Expiry</label>
                    <input
                      type="text"
                      value={cardExpiry}
                      onChange={(e) => setCardExpiry(formatExpiry(e.target.value))}
                      placeholder="12/28"
                      required
                      maxLength={5}
                      className="soc-input w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-soc-muted mb-1.5 uppercase tracking-wider">CVC</label>
                    <input
                      type="text"
                      value={cardCvc}
                      onChange={(e) => setCardCvc(e.target.value.replace(/\D/g, '').slice(0, 3))}
                      placeholder="123"
                      required
                      maxLength={3}
                      className="soc-input w-full"
                    />
                  </div>
                </div>

                {/* Order Summary */}
                <div className="bg-soc-surface rounded-lg p-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-soc-muted">{checkoutPlan.charAt(0).toUpperCase() + checkoutPlan.slice(1)} Plan</span>
                    <span className="text-white">${plan?.price || '0.00'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-soc-muted">Tax</span>
                    <span className="text-white">$0.00</span>
                  </div>
                  <div className="border-t border-soc-border pt-2 flex justify-between font-semibold">
                    <span className="text-white">Total</span>
                    <span className="text-white">${plan?.price || '0.00'}/mo</span>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={processing}
                  className="soc-btn-primary w-full flex items-center justify-center gap-2 !py-3"
                >
                  {processing ? (
                    <>
                      <Zap className="w-4 h-4 animate-pulse" />
                      Processing Payment...
                    </>
                  ) : (
                    <>
                      <Lock className="w-4 h-4" />
                      Pay ${plan?.price || '0.00'} &amp; Upgrade
                    </>
                  )}
                </button>

                <p className="text-xs text-soc-muted text-center flex items-center justify-center gap-1">
                  <Lock className="w-3 h-3" />
                  Secured with 256-bit SSL encryption
                </p>
              </form>
            </motion.div>
          </div>
        );
      })()}

      {/* Feature Comparison Table */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="soc-card overflow-hidden !p-0"
      >
        <div className="px-4 py-3 border-b border-soc-border">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Zap className="w-5 h-5 text-soc-accent" />
            Feature Comparison
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-soc-border">
                <th className="text-left text-xs font-medium text-soc-muted uppercase tracking-wider px-4 py-3">
                  Feature
                </th>
                <th className="text-center text-xs font-medium text-blue-400 uppercase tracking-wider px-4 py-3">
                  <div className="flex items-center justify-center gap-1">
                    <Shield className="w-3.5 h-3.5" />
                    Free
                  </div>
                </th>
                <th className="text-center text-xs font-medium text-soc-accent uppercase tracking-wider px-4 py-3">
                  <div className="flex items-center justify-center gap-1">
                    <Star className="w-3.5 h-3.5" />
                    Premium
                  </div>
                </th>
                <th className="text-center text-xs font-medium text-yellow-400 uppercase tracking-wider px-4 py-3">
                  <div className="flex items-center justify-center gap-1">
                    <Crown className="w-3.5 h-3.5" />
                    Exclusive
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-soc-border">
              {FEATURE_COMPARISON.map((row, i) => (
                <tr
                  key={row.label}
                  className={`hover:bg-soc-surface/50 transition-colors ${
                    i % 2 === 0 ? 'bg-soc-surface/20' : ''
                  }`}
                >
                  <td className="px-4 py-3 text-sm text-soc-text">{row.label}</td>
                  <td className="px-4 py-3 text-center">
                    {row.free ? (
                      <Check className="w-4 h-4 text-blue-400 mx-auto" />
                    ) : (
                      <span className="text-soc-muted/40 text-lg leading-none">--</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {row.premium ? (
                      <Check className="w-4 h-4 text-soc-accent mx-auto" />
                    ) : (
                      <span className="text-soc-muted/40 text-lg leading-none">--</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {row.exclusive ? (
                      <Check className="w-4 h-4 text-yellow-400 mx-auto" />
                    ) : (
                      <span className="text-soc-muted/40 text-lg leading-none">--</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}
