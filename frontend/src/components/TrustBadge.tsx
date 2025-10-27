import { ShieldAlert, ShieldCheck, HelpCircle, AlertTriangle, Info } from 'lucide-react'; // 'Shield' removed
import { useState } from 'react';
import { ScamScore } from '../services/api';

interface TrustBadgeProps {
  scoreData: ScamScore | null;
  isLoading: boolean;
}

export default function TrustBadge({ scoreData, isLoading }: TrustBadgeProps) {
  const [isPopoverVisible, setIsPopoverVisible] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2 p-2 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse">
        <HelpCircle className="w-5 h-5 text-gray-400" />
        <span className="text-sm font-medium text-gray-500">Checking domain trust...</span>
      </div>
    );
  }

  if (!scoreData) {
    return null; // Don't render if there's an error
  }

  // 'score' variable removed from destructuring
  const { trust_level, whois_days_old } = scoreData;

  const getBadgeDetails = () => {
    switch (trust_level) {
      case 'high':
        return {
          Icon: ShieldCheck,
          color: 'text-green-600 dark:text-green-400',
          bgColor: 'bg-green-50 dark:bg-green-900/20',
          text: 'Trusted Domain',
        };
      case 'medium':
        return {
          Icon: ShieldAlert,
          color: 'text-yellow-600 dark:text-yellow-400',
          bgColor: 'bg-yellow-50 dark:bg-yellow-900/20',
          text: 'Use Caution',
        };
      case 'low':
        return {
          Icon: AlertTriangle,
          color: 'text-red-600 dark:text-red-400',
          bgColor: 'bg-red-50 dark:bg-red-900/20',
          text: 'Suspicious Domain',
        };
      default: // 'unknown'
        return {
          Icon: HelpCircle,
          color: 'text-gray-600 dark:text-gray-400',
          bgColor: 'bg-gray-100 dark:bg-gray-800',
          text: 'Trust Unknown',
        };
    }
  };

  const { Icon, color, bgColor, text } = getBadgeDetails();

  const getEvidence = () => {
    if (trust_level === 'unknown') {
      return 'We could not determine a trust score for this domain.';
    }
    if (whois_days_old !== null && whois_days_old !== undefined) {
      if (trust_level === 'high') {
        return `This domain was registered ${whois_days_old} days ago, indicating it is well-established.`;
      }
      if (trust_level === 'medium' || trust_level === 'low') {
        return `This domain was registered ${whois_days_old} days ago. Newly registered domains can sometimes be a sign of a suspicious site.`;
      }
    }
    return 'This score is based on automated checks.';
  };

  return (
    <div className={`relative flex items-center space-x-2 p-2 rounded-lg ${bgColor} ${color}`}>
      <Icon className="w-5 h-5" />
      <span className="text-sm font-medium">{text}</span>
      <button
        onMouseEnter={() => setIsPopoverVisible(true)}
        onMouseLeave={() => setIsPopoverVisible(false)}
        onClick={() => setIsPopoverVisible(!isPopoverVisible)}
        className="cursor-pointer"
        aria-label="More information"
      >
        <Info className="w-4 h-4" />
      </button>

      {isPopoverVisible && (
        <div className="absolute top-full left-0 mt-2 w-72 p-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10">
          <h4 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">Evidence:</h4>
          <p className="text-xs text-gray-600 dark:text-gray-400">
            {getEvidence()}
          </p>
        </div>
      )}
    </div>
  );
}