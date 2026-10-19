import React from 'react';
import { FarmMapSelector } from '../components/map/FarmMapSelector';
import { WeatherWidget } from '../components/dashboard/WeatherWidget';
import { SoilWidget } from '../components/dashboard/SoilWidget';
import { SatelliteWidget } from '../components/dashboard/SatelliteWidget';
import { useFarm } from '../context/useFarm';
import { MapPin, Info } from 'lucide-react';

export const FarmMapPage: React.FC = () => {
  const { location } = useFarm();

  return (
    <div className="space-y-6">
      {/* Page Title & Scope Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <MapPin className="w-5 h-5 text-emerald-600" />
            <span>Interactive Farm Map & Environmental Scouting</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Pin farm coordinates to query localized Open-Meteo weather, Sentinel-2 spectral indices, and ISRIC SoilGrids 2.0 digital mapping.
          </p>
        </div>

        <div className="text-xs font-mono px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 self-start sm:self-auto font-medium">
          Target: {location.latitude.toFixed(4)}°N, {location.longitude.toFixed(4)}°E
        </div>
      </div>

      {/* Main Map Selector */}
      <FarmMapSelector heightClass="h-[480px]" />

      {/* Point-Based Architectural Caveat Notice */}
      <div className="p-4 rounded-xl bg-slate-100 border border-slate-200/90 text-xs text-slate-600 flex items-start gap-3">
        <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Point-Based Analysis Scope:</strong> Environmental context is queried using a point-centered 500-meter circular buffer. It reflects agro-ecological conditions at this geographic point and does not represent an exact cadastral legal farm boundary.
        </p>
      </div>

      {/* Live Scouted Environmental Metrics for Pin */}
      <div>
        <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4">
          Scouted Environmental Conditions for Current Pin
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <WeatherWidget />
          <SoilWidget />
          <SatelliteWidget />
        </div>
      </div>
    </div>
  );
};
