import React from 'react';
import { Layers, TestTube, AlertTriangle } from 'lucide-react';
import { useFarm } from '../../context/useFarm';
import { LoadingSkeleton } from '../common/LoadingSkeleton';

export const SoilWidget: React.FC = () => {
  const { soilState, fetchEnvironmentalData } = useFarm();
  const { data, loading, error } = soilState;

  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-5 w-32 bg-slate-200 animate-pulse rounded" />
          <div className="h-4 w-16 bg-slate-100 animate-pulse rounded" />
        </div>
        <LoadingSkeleton lines={4} />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-amber-700" />
              <span>ISRIC SoilGrids 2.0</span>
            </h3>
            <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
              Unavailable
            </span>
          </div>
          <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-200/60 text-xs text-slate-600 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              {error
                ? `Soil data unavailable: ${error}`
                : 'Connect to backend to retrieve 250m resolution digital soil properties (pH, clay, sand, silt fractions).'}
            </p>
          </div>
        </div>
        <button
          onClick={() => fetchEnvironmentalData()}
          className="mt-4 w-full py-2 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-900 text-xs font-semibold transition-colors border border-amber-200 cursor-pointer"
        >
          Query SoilGrids Feed
        </button>
      </div>
    );
  }

  const s = data.soil;

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-4 h-4 text-amber-700" />
            <span>Digital Soil Properties</span>
          </h3>
          <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-200">
            {data.data_source} ({data.depth_interval})
          </span>
        </div>

        {/* Soil Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 mt-4">
          <div className="p-3 rounded-xl bg-slate-50/80 border border-slate-100">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
              <TestTube className="w-3.5 h-3.5 text-emerald-600" />
              <span>Soil pH</span>
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-xl font-bold text-slate-900">
                {s.ph !== null && s.ph !== undefined ? s.ph.toFixed(1) : '—'}
              </span>
              <span className="text-xs font-semibold text-slate-500">pH</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50/80 border border-slate-100">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
              <span>Clay Content</span>
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-xl font-bold text-slate-900">
                {s.clay_pct !== null && s.clay_pct !== undefined ? s.clay_pct.toFixed(1) : '—'}
              </span>
              <span className="text-xs font-semibold text-slate-500">%</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50/80 border border-slate-100">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
              <span>Sand Content</span>
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-xl font-bold text-slate-900">
                {s.sand_pct !== null && s.sand_pct !== undefined ? s.sand_pct.toFixed(1) : '—'}
              </span>
              <span className="text-xs font-semibold text-slate-500">%</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50/80 border border-slate-100">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
              <span>Organic Carbon</span>
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-xl font-bold text-slate-900">
                {s.organic_carbon_g_kg !== null && s.organic_carbon_g_kg !== undefined
                  ? s.organic_carbon_g_kg.toFixed(1)
                  : '—'}
              </span>
              <span className="text-xs font-semibold text-slate-500">g/kg</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
        <span>Resolution: ~{data.resolution_m}m grid estimate</span>
        <span className="text-[10px] text-slate-400">CC BY 4.0 ISRIC</span>
      </div>
    </div>
  );
};
