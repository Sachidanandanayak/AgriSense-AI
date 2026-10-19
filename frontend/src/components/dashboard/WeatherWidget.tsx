import React from 'react';
import { CloudRain, Thermometer, Droplets, Wind, Clock, AlertTriangle } from 'lucide-react';
import { useFarm } from '../../context/useFarm';
import { LoadingSkeleton } from '../common/LoadingSkeleton';

export const WeatherWidget: React.FC = () => {
  const { weatherState, fetchEnvironmentalData } = useFarm();
  const { data, loading, error } = weatherState;

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
              <CloudRain className="w-4 h-4 text-sky-600" />
              <span>Current Weather Observations</span>
            </h3>
            <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
              Unavailable
            </span>
          </div>
          <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-200/60 text-xs text-slate-600 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              {error
                ? `Weather data unavailable: ${error}`
                : 'Connect to backend and sync environmental observations to view live Open-Meteo weather metrics.'}
            </p>
          </div>
        </div>
        <button
          onClick={() => fetchEnvironmentalData()}
          className="mt-4 w-full py-2 rounded-lg bg-sky-50 hover:bg-sky-100 text-sky-800 text-xs font-semibold transition-colors border border-sky-200 cursor-pointer"
        >
          Query Weather Feed
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <CloudRain className="w-4 h-4 text-sky-600" />
            <span>Meteorological Context</span>
          </h3>
          <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-sky-50 text-sky-800 border border-sky-200">
            Open-Meteo Feed
          </span>
        </div>

        {/* Primary Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 mt-4">
          <div className="p-3 rounded-xl bg-slate-50/80 border border-slate-100">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
              <Thermometer className="w-3.5 h-3.5 text-rose-500" />
              <span>Temperature</span>
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-xl font-bold text-slate-900">
                {data.temperature_c.toFixed(1)}
              </span>
              <span className="text-xs font-semibold text-slate-500">°C</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50/80 border border-slate-100">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
              <Droplets className="w-3.5 h-3.5 text-sky-500" />
              <span>Rel. Humidity</span>
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-xl font-bold text-slate-900">
                {data.humidity_percent.toFixed(0)}
              </span>
              <span className="text-xs font-semibold text-slate-500">%</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50/80 border border-slate-100">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
              <CloudRain className="w-3.5 h-3.5 text-indigo-500" />
              <span>Precipitation</span>
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-xl font-bold text-slate-900">
                {data.rainfall_mm.toFixed(1)}
              </span>
              <span className="text-xs font-semibold text-slate-500">mm</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50/80 border border-slate-100">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
              <Wind className="w-3.5 h-3.5 text-teal-500" />
              <span>Wind Speed</span>
            </div>
            <div className="mt-1 flex items-baseline gap-1">
              <span className="text-xl font-bold text-slate-900">
                {data.wind_speed_mps.toFixed(1)}
              </span>
              <span className="text-xs font-semibold text-slate-500">m/s</span>
            </div>
          </div>
        </div>
      </div>

      {data.weather_timestamp && (
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3 text-slate-400" />
            Observed
          </span>
          <span className="font-mono text-slate-600">
            {data.weather_timestamp.replace('T', ' ')}
          </span>
        </div>
      )}
    </div>
  );
};
