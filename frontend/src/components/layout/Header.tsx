import React from 'react';
import { MapPin, Menu, RefreshCw, Compass } from 'lucide-react';
import { useFarm } from '../../context/useFarm';
import { AGRICULTURAL_PRESETS } from '../../types/common';

interface HeaderProps {
  onToggleMobileSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleMobileSidebar }) => {
  const { location, applyPreset, fetchEnvironmentalData, weatherState, soilState, satelliteState } = useFarm();

  const isRefreshing = weatherState.loading || soilState.loading || satelliteState.loading;

  return (
    <header className="h-16 bg-white border-b border-slate-200/90 px-4 sm:px-6 flex items-center justify-between gap-4 sticky top-0 z-20">
      {/* Mobile Toggle + Title */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileSidebar}
          className="p-2 rounded-lg text-slate-600 hover:bg-slate-100 lg:hidden"
          aria-label="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="hidden sm:flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200/60">
            Precision Ag SaaS
          </span>
        </div>
      </div>

      {/* Farm Location Picker & Quick Actions */}
      <div className="flex items-center gap-2 sm:gap-3 flex-wrap justify-end">
        {/* Preset Selector */}
        <div className="relative inline-block text-left">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50/70 hover:bg-slate-100/70 transition-colors">
            <Compass className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <select
              aria-label="Agricultural Region Presets"
              className="bg-transparent text-xs font-medium text-slate-700 outline-hidden cursor-pointer"
              onChange={(e) => {
                const idx = Number(e.target.value);
                if (!isNaN(idx)) applyPreset(idx);
              }}
              value={AGRICULTURAL_PRESETS.findIndex(
                (p) => Math.abs(p.latitude - location.latitude) < 0.001
              )}
            >
              {AGRICULTURAL_PRESETS.map((p, idx) => (
                <option key={p.name} value={idx}>
                  {p.name} ({p.region})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Current Active Coordinates Pill */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50/80 border border-emerald-200 text-emerald-900 text-xs font-mono font-medium shadow-2xs">
          <MapPin className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
          <span>
            {location.latitude.toFixed(4)}°N, {location.longitude.toFixed(4)}°E
          </span>
        </div>

        {/* Sync / Refresh Environmental Context */}
        <button
          onClick={() => fetchEnvironmentalData()}
          disabled={isRefreshing}
          title="Fetch latest weather, satellite, and soil data for current coordinates"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold shadow-xs disabled:opacity-60 transition-all cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span className="hidden md:inline">Sync Environmental Data</span>
        </button>
      </div>
    </header>
  );
};
