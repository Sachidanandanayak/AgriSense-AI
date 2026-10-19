import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number | null | undefined;
  unit?: string;
  subtitle?: string;
  icon: LucideIcon;
  iconBg?: string;
  iconColor?: string;
  badge?: React.ReactNode;
  isLoading?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  unit,
  subtitle,
  icon: Icon,
  iconBg = 'bg-emerald-50',
  iconColor = 'text-emerald-700',
  badge,
  isLoading = false,
}) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-xs hover:shadow-sm transition-all duration-200">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-lg ${iconBg} ${iconColor} shrink-0`}>
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{title}</p>
            {isLoading ? (
              <div className="h-7 w-24 bg-slate-200 animate-pulse rounded mt-1" />
            ) : (
              <div className="flex items-baseline gap-1.5 mt-0.5">
                <span className="text-2xl font-bold text-slate-900 tracking-tight">
                  {value !== null && value !== undefined && value !== '' ? value : '—'}
                </span>
                {unit && (
                  <span className="text-xs font-semibold text-slate-500">{unit}</span>
                )}
              </div>
            )}
          </div>
        </div>
        {badge && <div className="shrink-0">{badge}</div>}
      </div>
      {subtitle && (
        <p className="text-xs text-slate-500 mt-3 pt-3 border-t border-slate-100 flex items-center gap-1.5 truncate">
          {subtitle}
        </p>
      )}
    </div>
  );
};
