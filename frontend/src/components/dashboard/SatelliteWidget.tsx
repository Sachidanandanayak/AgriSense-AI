import React from 'react';
import { Satellite, Eye, Droplet, Leaf, AlertTriangle } from 'lucide-react';
import { useFarm } from '../../context/useFarm';
import { LoadingSkeleton } from '../common/LoadingSkeleton';

export const SatelliteWidget: React.FC = () => {
  const { satelliteState, fetchEnvironmentalData } = useFarm();
  const { data, loading, error } = satelliteState;

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
              <Satellite className="w-4 h-4 text-emerald-600" />
              <span>Sentinel-2 Earth Observation</span>
            </h3>
            <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
              Unavailable
            </span>
          </div>
          <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-200/60 text-xs text-slate-600 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              {error
                ? `Satellite indices unavailable: ${error}`
                : 'Connect to backend to retrieve Sentinel-2 cloud-filtered vegetation and moisture spectral indices (NDVI, NDWI, NDMI).'}
            </p>
          </div>
        </div>
        <button
          onClick={() => fetchEnvironmentalData()}
          className="mt-4 w-full py-2 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-semibold transition-colors border border-emerald-200 cursor-pointer"
        >
          Query Sentinel-2 Feed
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Satellite className="w-4 h-4 text-emerald-600" />
            <span>Spectral Remote Sensing</span>
          </h3>
          <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
            {data.data_source} Harmonized
          </span>
        </div>

        {/* Spectral Indices Grid */}
        <div className="grid grid-cols-3 gap-2.5 mt-4">
          <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100/80 text-center">
            <div className="flex items-center justify-center gap-1 text-[11px] font-semibold text-emerald-800">
              <Leaf className="w-3 h-3 text-emerald-600" />
              <span>NDVI</span>
            </div>
            <div className="text-lg font-bold text-emerald-950 mt-1">
              {data.ndvi_median.toFixed(3)}
            </div>
            <p className="text-[10px] text-emerald-700/80 mt-0.5">Canopy Greenness</p>
          </div>

          <div className="p-3 rounded-xl bg-sky-50/60 border border-sky-100/80 text-center">
            <div className="flex items-center justify-center gap-1 text-[11px] font-semibold text-sky-800">
              <Droplet className="w-3 h-3 text-sky-600" />
              <span>NDWI</span>
            </div>
            <div className="text-lg font-bold text-sky-950 mt-1">
              {data.ndwi_median.toFixed(3)}
            </div>
            <p className="text-[10px] text-sky-700/80 mt-0.5">Surface Water</p>
          </div>

          <div className="p-3 rounded-xl bg-indigo-50/60 border border-indigo-100/80 text-center">
            <div className="flex items-center justify-center gap-1 text-[11px] font-semibold text-indigo-800">
              <Eye className="w-3 h-3 text-indigo-600" />
              <span>NDMI</span>
            </div>
            <div className="text-lg font-bold text-indigo-950 mt-1">
              {data.ndmi_median.toFixed(3)}
            </div>
            <p className="text-[10px] text-indigo-700/80 mt-0.5">Moisture Stress</p>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
        <span>
          Window: {data.start_date} to {data.end_date}
        </span>
        <span className="font-semibold text-emerald-700">
          {data.usable_observations} clear scene{data.usable_observations === 1 ? '' : 's'}
        </span>
      </div>
    </div>
  );
};
