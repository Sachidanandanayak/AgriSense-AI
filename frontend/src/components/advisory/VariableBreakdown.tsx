import React from 'react';
import type { VariableCompatibility } from '../../types/advisory';
import { StatusBadge } from '../common/StatusBadge';
import { Thermometer, CloudRain, TestTube, Layers, HelpCircle } from 'lucide-react';

interface VariableBreakdownProps {
  evaluations: Record<string, VariableCompatibility>;
}

export const VariableBreakdown: React.FC<VariableBreakdownProps> = ({ evaluations }) => {
  const getVariableIcon = (varName: string) => {
    const lower = varName.toLowerCase();
    if (lower.includes('temp')) return <Thermometer className="w-4 h-4 text-rose-500" />;
    if (lower.includes('rain')) return <CloudRain className="w-4 h-4 text-sky-500" />;
    if (lower.includes('ph')) return <TestTube className="w-4 h-4 text-emerald-500" />;
    if (lower.includes('texture') || lower.includes('soil')) return <Layers className="w-4 h-4 text-amber-500" />;
    return <HelpCircle className="w-4 h-4 text-slate-400" />;
  };

  const entries = Object.entries(evaluations);

  if (entries.length === 0) {
    return (
      <div className="p-4 text-xs text-slate-500 bg-slate-50 rounded-xl border border-slate-100 text-center">
        No variable compatibility evaluations available for this candidate.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {entries.map(([key, item]) => (
        <div
          key={key}
          className="p-3.5 rounded-xl border border-slate-200/80 bg-white hover:bg-slate-50/50 transition-colors shadow-2xs"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-slate-100 shrink-0">
                {getVariableIcon(item.variable)}
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">{item.variable}</h4>
                <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-0.5">
                  <span>
                    Observed:{' '}
                    <strong className="text-slate-800">
                      {item.observed_value !== null && item.observed_value !== undefined
                        ? String(item.observed_value)
                        : 'Unavailable'}
                    </strong>{' '}
                    {item.observed_unit && item.observed_value !== null && (
                      <span className="text-slate-500">{item.observed_unit}</span>
                    )}
                  </span>
                </div>
              </div>
            </div>
            <StatusBadge status={item.status} size="sm" />
          </div>

          {/* FAO Optimal & Absolute Range Reference */}
          <div className="mt-2.5 pt-2.5 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
            <div className="text-slate-600 bg-slate-50/80 px-2.5 py-1.5 rounded-lg border border-slate-100">
              <span className="font-semibold text-slate-700">Optimal Range:</span>{' '}
              <span className="font-mono text-slate-800">
                {item.documented_optimal_range || 'Not documented'}
              </span>
            </div>
            <div className="text-slate-600 bg-slate-50/80 px-2.5 py-1.5 rounded-lg border border-slate-100">
              <span className="font-semibold text-slate-700">Absolute Range:</span>{' '}
              <span className="font-mono text-slate-800">
                {item.documented_absolute_range || 'Not documented'}
              </span>
            </div>
          </div>

          {/* Explanatory justification */}
          <p className="mt-2 text-xs text-slate-600 leading-relaxed bg-emerald-50/30 p-2 rounded-lg border border-emerald-100/60">
            {item.reason}
          </p>

          <div className="mt-2 flex items-center justify-between text-[10px] text-slate-600">
            <span>Authoritative Source: {item.source}</span>
          </div>
        </div>
      ))}
    </div>
  );
};
