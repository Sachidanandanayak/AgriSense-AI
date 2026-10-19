import React from 'react';
import { ClipboardCheck, RefreshCw, AlertTriangle, FileText, Satellite } from 'lucide-react';
import { useFarm } from '../context/useFarm';
import { CropAdvisoryCard } from '../components/advisory/CropAdvisoryCard';
import { WaterAdvisoryCard } from '../components/advisory/WaterAdvisoryCard';
import { RiskFlagList } from '../components/advisory/RiskFlagList';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { DisclaimerBox } from '../components/common/DisclaimerBox';
import { RegionalCandidatesSection } from '../components/advisory/RegionalCandidatesSection';
import { fetchFarmAdvisory } from '../api/advisory';
import { shouldFetchLive } from '../api/client';
import type { FarmAdvisoryRequest, CropAdvisoryItem, FarmAdvisoryResponse } from '../types/advisory';
import type { ApiState } from '../types/common';

export const AdvisoryPage: React.FC = () => {
  const {
    location,
    agriculturalInputs,
    fieldSoilType,
    irrigationStatus,
    croppingSeason,
    weatherState,
    soilState,
    satelliteState,
    recommendationState,
    advisoryState,
    setAdvisoryState,
  } = useFarm();

  const handleGenerateAdvisory = async (options?: { forceLiveEnv?: boolean }) => {
    setAdvisoryState((prev: ApiState<FarmAdvisoryResponse>) => ({ ...prev, loading: true, error: null }));

    const force = options?.forceLiveEnv ?? false;
    const req: FarmAdvisoryRequest = {
      latitude: location.latitude,
      longitude: location.longitude,
      observation_date: new Date().toISOString().split('T')[0],
      agricultural_inputs: agriculturalInputs,
      top_k: recommendationState.data?.recommendations.length || 3,
      weather_context: weatherState.data,
      soil_context: soilState.data,
      satellite_context: satelliteState.data,
      fetch_live_weather: shouldFetchLive(weatherState, force),
      fetch_live_soil: shouldFetchLive(soilState, force),
      fetch_live_satellite: shouldFetchLive(satelliteState, force),
      soil_type: fieldSoilType,
      irrigation_status: irrigationStatus,
      season: croppingSeason,
      recommendation_response: recommendationState.data,
    };

    try {
      const response = await fetchFarmAdvisory(req);
      setAdvisoryState({
        data: response,
        loading: false,
        error: null,
      });
    } catch (err) {
      setAdvisoryState({
        data: null,
        loading: false,
        error: err instanceof Error ? err.message : 'Farm advisory generation failed',
      });
    }
  };

  const adv = advisoryState.data;

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <ClipboardCheck className="w-5 h-5 text-emerald-600" />
            <span>Evidence-Based Farm Advisory (Phase 9)</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Authoritative agronomic compatibility evaluations grounded strictly in FAO ECOCROP biophysical descriptors and FAO-56 crop-water methodology.
          </p>
        </div>

        <button
          type="button"
          onClick={() => handleGenerateAdvisory()}
          disabled={advisoryState.loading}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold transition-all shadow-sm hover:shadow disabled:opacity-50 cursor-pointer self-start sm:self-auto"
        >
          <RefreshCw className={`w-4 h-4 ${advisoryState.loading ? 'animate-spin' : ''}`} />
          <span>{advisoryState.loading ? 'Evaluating Compatibility...' : 'Generate Full Farm Advisory'}</span>
        </button>
      </div>

      {/* Error state */}
      {advisoryState.error && (
        <ErrorAlert
          title="Advisory Engine Notice"
          message={advisoryState.error}
          onRetry={() => handleGenerateAdvisory()}
        />
      )}

      {/* No report prompt */}
      {!adv && !advisoryState.loading && !advisoryState.error && (
        <div className="p-8 sm:p-12 text-center bg-white rounded-3xl border border-slate-200/90 shadow-xs space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-emerald-50 text-emerald-700 mx-auto flex items-center justify-center">
            <ClipboardCheck className="w-7 h-7" />
          </div>
          <div className="max-w-md mx-auto space-y-1.5">
            <h3 className="text-base font-bold text-slate-900">
              No Advisory Report Generated Yet
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Click &quot;Generate Full Farm Advisory&quot; to evaluate your current farm coordinates and agricultural inputs against authoritative FAO ECOCROP ecological thresholds.
            </p>
          </div>
          <button
            onClick={() => handleGenerateAdvisory()}
            className="px-6 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold tracking-wide transition-all shadow-xs cursor-pointer"
          >
            Run Agronomic Compatibility Evaluation
          </button>
        </div>
      )}

      {/* Full Advisory Results */}
      {adv && (
        <div className="space-y-6">
          {/* Executive Overview Banner */}
          <div className="bg-emerald-950 text-white rounded-2xl p-5 sm:p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md bg-emerald-800 text-emerald-200">
                  Agro-Ecological Audit Complete
                </span>
                <span className="text-xs text-slate-300">
                  Ref Date: {adv.observation_date || 'Today'}
                </span>
              </div>
              <h2 className="text-lg font-bold text-white mt-1.5">
                Evaluation Grounded in Liebig&apos;s Law of the Minimum
              </h2>
              <p className="text-xs text-emerald-200/90 mt-1 max-w-2xl leading-relaxed">
                Zero arbitrary suitability scoring formulas (no &quot;30% NDVI + 30% soil + 40% weather&quot;). Individual limiting factors determine boundary viability.
              </p>
            </div>

            <div className="text-right self-start md:self-auto shrink-0 bg-white/10 backdrop-blur-xs p-3 rounded-xl border border-white/10">
              <span className="text-[11px] text-slate-300 uppercase block font-semibold">
                Evaluated Species
              </span>
              <span className="text-xl font-extrabold text-white">
                {adv.crop_advisories.length} Crops
              </span>
            </div>
          </div>

          {/* Regional Agronomic Candidates (UAS Raichur & ICAR Zone 2 / 1) */}
          <RegionalCandidatesSection report={adv.regional_advisory} />

          {/* Candidate Crop Advisory Cards */}
          <div className="space-y-5">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Candidate Crop Agro-Ecological Profiles & Environmental Compatibility (FAO ECOCROP)
            </h3>
            {adv.crop_advisories.map((cropItem: CropAdvisoryItem) => (
              <CropAdvisoryCard key={cropItem.crop} item={cropItem} />
            ))}
          </div>

          {/* Water Requirement Advisory */}
          <WaterAdvisoryCard waterAdvisory={adv.water_advisory} />

          {/* Sentinel-2 Context Card */}
          {adv.satellite_context && (
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs space-y-3">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Satellite className="w-4 h-4 text-emerald-600" />
                  <span>Sentinel-2 Spectral Remote Sensing Context</span>
                </h3>
                <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                  {adv.satellite_context.available ? 'Observational Indicator' : 'Unavailable'}
                </span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed font-medium">
                {adv.satellite_context.summary}
              </p>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-[11px] text-slate-500 leading-relaxed">
                <strong>Mandatory Remote Sensing Caveat:</strong> {adv.satellite_context.disclaimer}
              </div>
            </div>
          )}

          {/* Global Risk Indicators */}
          <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Consolidated Agronomic Risk & Data Quality Flags</span>
            </h3>
            <RiskFlagList flags={adv.risk_flags} />
          </div>

          {/* Explanations List */}
          {adv.explanations && adv.explanations.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs space-y-3">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-600" />
                <span>Transparent Agronomic Explanations</span>
              </h3>
              <ul className="space-y-2 text-xs text-slate-700 leading-relaxed">
                {adv.explanations.map((exp: string, idx: number) => (
                  <li key={idx} className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                    {exp}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Scientific Limitations */}
          {adv.limitations && adv.limitations.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs space-y-3">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Authoritative Scientific Limitations & Boundary Scope
              </h3>
              <ul className="space-y-1.5 text-xs text-slate-600 leading-relaxed list-disc list-inside">
                {adv.limitations.map((lim: string, idx: number) => (
                  <li key={idx}>{lim}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Mandatory Disclaimer */}
          <DisclaimerBox disclaimer={adv.disclaimer} />
        </div>
      )}
    </div>
  );
};
