import React from 'react';
import type { WaterAdvisory } from '../../types/advisory';
import { Droplet, Info } from 'lucide-react';
import { StatusBadge } from '../common/StatusBadge';

interface WaterAdvisoryCardProps {
  waterAdvisory: WaterAdvisory;
}

export const WaterAdvisoryCard: React.FC<WaterAdvisoryCardProps> = ({ waterAdvisory }) => {
  const isAvailable = waterAdvisory.status === 'available';

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs p-5 sm:p-6 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-sky-50 text-sky-700 shrink-0">
            <Droplet className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <span>Crop Water & Irrigation Requirement Advisory</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Methodology: {waterAdvisory.methodology}
            </p>
          </div>
        </div>
        <StatusBadge status={waterAdvisory.status} size="md" />
      </div>

      {/* Explanatory Reason Box */}
      <div
        className={`p-4 rounded-xl border text-xs leading-relaxed ${
          isAvailable
            ? 'bg-sky-50/70 border-sky-200 text-sky-950'
            : 'bg-slate-50 border-slate-200 text-slate-700'
        }`}
      >
        <p className="font-medium">{waterAdvisory.reason}</p>
      </div>

      {/* Available calculation display */}
      {isAvailable && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">
              Ref. ET0
            </span>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-xl font-bold text-slate-900">
                {waterAdvisory.reference_evapotranspiration_et0_mm_day?.toFixed(2)}
              </span>
              <span className="text-xs text-slate-500 font-medium">mm/day</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">
              Crop Coeff (Kc)
            </span>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-xl font-bold text-slate-900">
                {waterAdvisory.crop_coefficient_kc?.toFixed(2)}
              </span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">
              Crop Demand (ETc)
            </span>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-xl font-bold text-slate-900">
                {waterAdvisory.crop_evapotranspiration_etc_mm_day?.toFixed(2)}
              </span>
              <span className="text-xs text-slate-500 font-medium">mm/day</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-emerald-50/70 border border-emerald-200">
            <span className="text-[11px] font-semibold text-emerald-800 uppercase">
              Net Irrigation Req
            </span>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-xl font-bold text-emerald-950">
                {waterAdvisory.estimated_irrigation_requirement_mm?.toFixed(2)}
              </span>
              <span className="text-xs text-emerald-700 font-semibold">mm</span>
            </div>
          </div>
        </div>
      )}

      {/* Missing Parameters Checklist when status is unavailable */}
      {!isAvailable && waterAdvisory.missing_parameters && waterAdvisory.missing_parameters.length > 0 && (
        <div className="pt-2">
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <span>Mandatory Missing Parameters under FAO-56 Standard:</span>
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {waterAdvisory.missing_parameters.map((param) => (
              <div
                key={param}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-50 border border-slate-200/80 text-xs text-slate-700 font-mono"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" />
                <span className="truncate">{param}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scientific notes */}
      {waterAdvisory.notes && (
        <div className="pt-3 border-t border-slate-100 flex items-start gap-2 text-[11px] text-slate-500">
          <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">{waterAdvisory.notes}</p>
        </div>
      )}
    </div>
  );
};
