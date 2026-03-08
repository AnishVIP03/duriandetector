/**
 * TierGate — Subscription tier gating wrapper component.
 * Checks if the current user's role meets the required tier.
 * Shows an "Upgrade Required" screen if not.
 */
import { useAuthStore } from '../../store/authStore';
import { Lock, ArrowUpCircle, Shield, Star, Crown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const TIER_LEVELS = { free: 0, premium: 1, exclusive: 2, admin: 3 };

const TIER_INFO = {
  premium: {
    label: 'Premium',
    icon: Star,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
  },
  exclusive: {
    label: 'Exclusive',
    icon: Crown,
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/30',
  },
};

export default function TierGate({ requiredTier, children, featureName }) {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const userLevel = TIER_LEVELS[user?.role] ?? 0;
  const requiredLevel = TIER_LEVELS[requiredTier] ?? 0;

  // User has sufficient tier — render children
  if (userLevel >= requiredLevel) {
    return children;
  }

  const tierInfo = TIER_INFO[requiredTier] || TIER_INFO.premium;
  const TierIcon = tierInfo.icon;

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className={`p-6 rounded-2xl ${tierInfo.bgColor} border ${tierInfo.borderColor} mb-6`}>
        <Lock className={`w-16 h-16 ${tierInfo.color}`} />
      </div>

      <h2 className="text-2xl font-bold text-white mb-2">
        {featureName || 'This Feature'} is Locked
      </h2>

      <p className="text-soc-muted mb-2 max-w-md">
        This feature requires a <span className={`font-semibold ${tierInfo.color}`}>{tierInfo.label}</span> subscription or above.
      </p>

      <p className="text-soc-muted/60 text-sm mb-8 max-w-md">
        Upgrade your plan to unlock {featureName ? featureName.toLowerCase() : 'this feature'} and other advanced capabilities.
      </p>

      <button
        onClick={() => navigate('/subscription')}
        className="flex items-center gap-2 px-6 py-3 bg-soc-accent hover:bg-soc-accent/80 rounded-lg text-white font-medium transition-colors"
      >
        <ArrowUpCircle className="w-5 h-5" />
        View Plans & Upgrade
      </button>

      <div className="mt-6 flex items-center gap-2 text-soc-muted/40 text-xs">
        <TierIcon className="w-3 h-3" />
        <span>You are on the {user?.role || 'free'} plan</span>
      </div>
    </div>
  );
}
