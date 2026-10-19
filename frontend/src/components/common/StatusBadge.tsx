import React from 'react';
import type { CompatibilityStatus } from '../../types/advisory';
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle } from 'lucide-react';

interface StatusBadgeProps {
  status: CompatibilityStatus | string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  showIcon = true,
}) => {
  const norm = (status || 'unavailable').toLowerCase() as CompatibilityStatus;

  const config = {
    favorable: {
      label: 'Favorable',
      bg: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      icon: CheckCircle2,
      iconColor: 'text-emerald-600',
    },
    caution: {
      label: 'Caution',
      bg: 'bg-amber-50 text-amber-800 border-amber-200',
      icon: AlertTriangle,
      iconColor: 'text-amber-600',
    },
    unfavorable: {
      label: 'Unfavorable',
      bg: 'bg-rose-50 text-rose-800 border-rose-200',
      icon: XCircle,
      iconColor: 'text-rose-600',
    },
    unavailable: {
      label: 'Unavailable',
      bg: 'bg-slate-100 text-slate-700 border-slate-200',
      icon: HelpCircle,
      iconColor: 'text-slate-500',
    },
  }[norm] || {
    label: norm,
    bg: 'bg-slate-100 text-slate-700 border-slate-200',
    icon: HelpCircle,
    iconColor: 'text-slate-500',
  };

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-medium',
    lg: 'text-sm px-3 py-1.5 gap-2 font-semibold',
  }[size];

  const IconComponent = config.icon;

  return (
    <span
      className={`inline-flex items-center rounded-full border ${config.bg} ${sizeClasses} transition-colors`}
    >
      {showIcon && <IconComponent className={`w-3.5 h-3.5 ${config.iconColor} shrink-0`} />}
      <span>{config.label}</span>
    </span>
  );
};
