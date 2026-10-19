import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ShieldCheck, ArrowRight, Layers, FileText } from 'lucide-react';
import { useFarm } from '../context/useFarm';
import { RecommendationForm } from '../components/recommendation/RecommendationForm';
import { RecommendationCard } from '../components/recommendation/RecommendationCard';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { DisclaimerBox } from '../components/common/DisclaimerBox';
import { RegionalCandidatesSection } from '../components/advisory/RegionalCandidatesSection';
import { fetchRecommendations } from '../api/recommendations';
import type { AgriculturalInput, RecommendationRequest, CropRecommendationItem } from '../types/recommendation';
import type { ApiState } from '../types/common';
import type { RecommendationResponse } from '../types/recommendation';

export const RecommendationsPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    location,
    fieldSoilType,
    irrigationStatus,
    croppingSeason,
    recommendationState,
    setRecommendationState,
    weatherState,
    soilState,
    satelliteState,
  } = useFarm();

  const handleGenerateRecommendations = async (inputs: AgriculturalInput, topK: number) => {
    setRecommendationState((prev: ApiState<RecommendationResponse>) => ({ ...prev, loading: true, error: null }));

    const req: RecommendationRequest = {
      latitude: location.latitude,
      longitude: location.longitude,
      observation_date: new Date().toISOString().split('T')[0],
      agricultural_inputs: inputs,
      top_k: topK,
      weather_context: weatherState.data,
      soil_context: soilState.data,
      satellite_context: satelliteState.data,
      fetch_live_weather: !weatherState.data,
      fetch_live_soil: !soilState.data,
      fetch_live_satellite: !satelliteState.data,
      soil_type: fieldSoilType,
      irrigation_status: irrigationStatus,
      season: croppingSeason,
    };

    try {
      const response = await fetchRecommendations(req);
      setRecommendationState({
        data: response,
        loading: false,
        error: null,
      });
    } catch (err) {
      setRecommendationState({
        data: null,
        loading: false,
        error: err instanceof Error ? err.message : 'Recommendation request failed',
      });
    }
  };

  const rec = recommendationState.data;

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-600" />
            <span>Crop Recommendation Engine (Phase 8)</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Random Forest machine learning model trained on controlled multi-dimensional agricultural trials.
          </p>
        </div>

        <div className="text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 font-semibold self-start sm:self-auto">
          Model: crop_recommendation_rf_v1
        </div>
      </div>

      {/* Input Form */}
      <RecommendationForm
        onSubmit={handleGenerateRecommendations}
        isLoading={recommendationState.loading}
      />

      {/* Error state */}
      {recommendationState.error && (
        <ErrorAlert
          title="Recommendation Engine Failed"
          message={recommendationState.error}
          onRetry={() => {
            const inputs = {
              nitrogen: 80,
              phosphorus: 40,
              potassium: 40,
              temperature: 26.5,
              humidity: 65,
              ph: 6.8,
              rainfall: 120,
            };
            handleGenerateRecommendations(inputs, 3);
          }}
        />
      )}

      {/* Results View */}
      {rec && (
        <div className="space-y-8">
          {/* Concept 1: Locally Relevant Regional Candidates (UAS Raichur & ICAR Zone 2) */}
          {rec.regional_advisory && (
            <RegionalCandidatesSection report={rec.regional_advisory} />
          )}

          {/* Concept 2: Benchmark Machine Learning Model Inference (22-Crop Academic Baseline) */}
          <div className="space-y-4 pt-4 border-t border-slate-200">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">
                    Concept 2: Academic Benchmark
                  </span>
                </div>
                <h2 className="text-base font-bold text-slate-900 mt-1">
                  Benchmark ML Predictions ({rec.recommendations.length} Crops)
                </h2>
                <p className="text-xs text-slate-500">
                  Ranked strictly by the Random Forest classifier trained on 2,200 controlled academic trial plots.
                </p>
              </div>

              <button
                type="button"
                onClick={() => navigate('/advisory')}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold transition-all shadow-xs cursor-pointer self-start sm:self-auto"
              >
                <span>View Evidence-Based Advisory Report</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Educational Banner Explaining Coffee & Jute */}
            <div className="p-3.5 rounded-xl bg-amber-50/80 border border-amber-200 text-xs text-amber-900 space-y-1">
              <span className="font-bold block">
                Educational Agronomic Notice on Benchmark ML Predictions:
              </span>
              <p className="text-amber-800 leading-relaxed">
                The benchmark model classifies crops based solely on mathematical proximity to 2,200 academic trial plots (22 fixed crops). It does not contain regional staples like Sorghum or Groundnut, nor geographical boundary awareness. Non-regional crops such as <strong>Coffee</strong> and <strong>Jute</strong> appear because Raichur&apos;s ambient temperature (26.5°C) and NPK inputs match their academic trial hypercube. For real-world farming in Raichur/Yadgir, refer to the <strong>Locally Relevant Crop Candidates</strong> above.
              </p>
            </div>

            {/* Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {rec.recommendations.map((item: CropRecommendationItem) => (
                <RecommendationCard
                  key={item.crop}
                  item={item}
                  onInspectAdvisory={() => navigate('/advisory')}
                />
              ))}
            </div>
          </div>

          {/* Transparent Model Input Features Vector */}
          {rec.model_input_features && (
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs space-y-3">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-4 h-4 text-emerald-600" />
                <span>Engineered 11-Feature Vector Ingested by Random Forest</span>
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-xs">
                {Object.entries(rec.model_input_features).map(([k, v]) => (
                  <div key={k} className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="text-[10px] text-slate-500 uppercase font-mono block truncate">
                      {k}
                    </span>
                    <span className="font-bold text-slate-900 font-mono">
                      {typeof v === 'number' ? v.toFixed(3) : String(v)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Transparent Explanations */}
          {rec.explanation && rec.explanation.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs space-y-2.5">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-600" />
                <span>Data-Grounded Model Explanations</span>
              </h3>
              <ul className="space-y-1.5 text-xs text-slate-700 leading-relaxed">
                {rec.explanation.map((exp: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2 p-2 rounded-lg bg-slate-50">
                    <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    <span>{exp}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Limitations */}
          {rec.limitations && rec.limitations.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs space-y-2.5">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Scientific Limitations & Operational Boundaries
              </h3>
              <ul className="space-y-1 text-xs text-slate-600 leading-relaxed list-disc list-inside">
                {rec.limitations.map((lim: string, idx: number) => (
                  <li key={idx}>{lim}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Mandatory Disclaimer Box */}
          <DisclaimerBox disclaimer={rec.disclaimer} />
        </div>
      )}
    </div>
  );
};
