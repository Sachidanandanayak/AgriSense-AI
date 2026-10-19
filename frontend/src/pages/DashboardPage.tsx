import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Thermometer,
  CloudRain,
  Leaf,
  Layers,
  Sparkles,
  ArrowRight,
  MapPin,
  ClipboardCheck,
} from 'lucide-react';
import { useFarm } from '../context/useFarm';
import { StatCard } from '../components/common/StatCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { WeatherWidget } from '../components/dashboard/WeatherWidget';
import { SoilWidget } from '../components/dashboard/SoilWidget';
import { SatelliteWidget } from '../components/dashboard/SatelliteWidget';
import { DisclaimerBox } from '../components/common/DisclaimerBox';
import type { CropRecommendationItem } from '../types/recommendation';
import type { CropAdvisoryItem } from '../types/advisory';

export const DashboardPage: React.FC = () => {
  const {
    location,
    weatherState,
    soilState,
    satelliteState,
    recommendationState,
    advisoryState,
    fetchEnvironmentalData,
  } = useFarm();

  const { data: w, loading: weatherLoading, error: weatherError } = weatherState;

  // Initial fetch on mount if no data yet
  useEffect(() => {
    if (!w && !weatherLoading && !weatherError) {
      fetchEnvironmentalData();
    }
  }, [w, weatherLoading, weatherError, fetchEnvironmentalData]);

  const s = soilState.data?.soil;
  const sat = satelliteState.data;
  const rec = recommendationState.data;
  const adv = advisoryState.data;

  return (
    <div className="space-y-6">
      {/* Welcome & Farm Header */}
      <div className="bg-gradient-to-r from-emerald-900 to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 text-xs font-semibold backdrop-blur-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Precision Agriculture Executive Dashboard
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Farm Intelligence & Evidence-Based Advisory
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-normal">
            Synthesizing multi-source satellite observations, open weather metrics, digital soil mapping, and machine learning recommendations with authoritative FAO ECOCROP ecological compatibility.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-3">
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/10 backdrop-blur-xs text-xs font-medium text-slate-200 border border-white/10">
              <MapPin className="w-3.5 h-3.5 text-emerald-400" />
              <span>{location.name || 'Current Location'}: {location.latitude.toFixed(4)}°N, {location.longitude.toFixed(4)}°E</span>
            </div>

            <Link
              to="/map"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-all shadow-xs"
            >
              <span>Change Farm Coordinates</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Ambient background decoration */}
        <div className="absolute -right-12 -bottom-12 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      {/* Primary Environmental Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Ambient Temperature"
          value={w ? w.temperature_c.toFixed(1) : null}
          unit="°C"
          subtitle={w ? `Humidity: ${w.humidity_percent.toFixed(0)}%` : 'Open-Meteo Feed'}
          icon={Thermometer}
          iconBg="bg-rose-50"
          iconColor="text-rose-600"
          isLoading={weatherState.loading}
        />

        <StatCard
          title="Recent Precipitation"
          value={w ? w.rainfall_mm.toFixed(1) : null}
          unit="mm"
          subtitle={w ? `Wind: ${w.wind_speed_mps.toFixed(1)} m/s` : 'Open-Meteo Feed'}
          icon={CloudRain}
          iconBg="bg-sky-50"
          iconColor="text-sky-600"
          isLoading={weatherState.loading}
        />

        <StatCard
          title="Topsoil pH (0-5cm)"
          value={s?.ph !== null && s?.ph !== undefined ? s.ph.toFixed(1) : null}
          unit="pH"
          subtitle={s?.clay_pct ? `Clay: ${s.clay_pct.toFixed(0)}% | Sand: ${s.sand_pct?.toFixed(0)}%` : 'ISRIC SoilGrids 2.0'}
          icon={Layers}
          iconBg="bg-amber-50"
          iconColor="text-amber-700"
          isLoading={soilState.loading}
        />

        <StatCard
          title="Sentinel-2 NDVI"
          value={sat ? sat.ndvi_median.toFixed(3) : null}
          subtitle={sat ? `${sat.usable_observations} clear scenes in window` : 'Canopy Greenness'}
          icon={Leaf}
          iconBg="bg-emerald-50"
          iconColor="text-emerald-700"
          isLoading={satelliteState.loading}
        />
      </div>

      {/* Environmental Deep-Dive Widgets */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <span>Live Environmental Context Providers</span>
          </h2>
          <span className="text-xs text-slate-500">Phases 4–6 Multi-Source Integration</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <WeatherWidget />
          <SoilWidget />
          <SatelliteWidget />
        </div>
      </div>

      {/* Crop Recommendations & Advisory Summaries */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ML Recommendations Preview Card */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Crop Recommendations (Phase 8)</h3>
                  <p className="text-xs text-slate-500">Random Forest Benchmark Classification</p>
                </div>
              </div>
              <Link
                to="/recommendations"
                className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1"
              >
                <span>Full Analysis</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {rec ? (
              <div className="mt-4 space-y-3">
                <p className="text-xs text-slate-600">
                  Top-ranked candidates based on trial distribution classification:
                </p>
                <div className="space-y-2">
                  {rec.recommendations.slice(0, 3).map((item: CropRecommendationItem) => (
                    <div
                      key={item.crop}
                      className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs"
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="w-5 h-5 rounded-md bg-emerald-600 text-white font-bold text-[10px] flex items-center justify-center">
                          #{item.rank}
                        </span>
                        <span className="font-bold text-slate-900 capitalize">{item.crop}</span>
                      </div>
                      <div className="text-right">
                        <span className="font-extrabold text-emerald-800">
                          {item.confidence_percentage}
                        </span>
                        <span className="text-[10px] text-slate-400 block">Confidence</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="mt-6 py-8 text-center text-xs text-slate-500 bg-slate-50/70 rounded-xl border border-slate-100 space-y-3">
                <Sparkles className="w-8 h-8 text-slate-300 mx-auto" />
                <p>No recommendation executed yet for this session.</p>
                <Link
                  to="/recommendations"
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-semibold transition-colors shadow-xs"
                >
                  Configure & Run ML Model
                </Link>
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span>Model Scope: 2,200 sample controlled trial baseline</span>
            <span className="text-emerald-700 font-medium">11-Feature Vector</span>
          </div>
        </div>

        {/* Evidence-Based Advisory Preview Card */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700">
                  <ClipboardCheck className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Farm Advisory (Phase 9)</h3>
                  <p className="text-xs text-slate-500">FAO ECOCROP Ecological Compatibility</p>
                </div>
              </div>
              <Link
                to="/advisory"
                className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1"
              >
                <span>Full Advisory Report</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {adv ? (
              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-600 font-medium">Top Candidate Overall Status:</span>
                  <StatusBadge
                    status={adv.crop_advisories[0]?.overall_compatibility || 'unavailable'}
                    size="sm"
                  />
                </div>

                <div className="space-y-2">
                  {adv.crop_advisories.slice(0, 2).map((item: CropAdvisoryItem) => (
                    <div
                      key={item.crop}
                      className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-900 capitalize">
                          {item.crop} {item.scientific_name ? `(${item.scientific_name})` : ''}
                        </span>
                        <StatusBadge status={item.overall_compatibility} size="sm" />
                      </div>
                      <p className="text-[11px] text-slate-600 truncate">
                        {item.advisory_notes[0] || 'Grounded in documented FAO biophysical parameters.'}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="mt-6 py-8 text-center text-xs text-slate-500 bg-slate-50/70 rounded-xl border border-slate-100 space-y-3">
                <ClipboardCheck className="w-8 h-8 text-slate-300 mx-auto" />
                <p>No advisory report generated yet for current location.</p>
                <Link
                  to="/advisory"
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-semibold transition-colors shadow-xs"
                >
                  Generate FAO Advisory Report
                </Link>
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
            <span>Methodology: Liebig Law of the Minimum (Zero Guessing)</span>
            <span className="text-emerald-700 font-medium">FAO-56 Water Check</span>
          </div>
        </div>
      </div>

      {/* Mandatory Scientific Disclaimer */}
      <DisclaimerBox
        disclaimer={
          rec?.disclaimer ||
          'This farm advisory dashboard synthesizes benchmark machine learning recommendations with authoritative FAO ECOCROP ecological requirements and observed environmental context. The benchmark model probability estimate reflects classification likelihood relative to its training trial distribution and does NOT represent a scientifically validated crop suitability, commercial yield, or harvest success guarantee.'
        }
      />
    </div>
  );
};
