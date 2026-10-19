import React, { useState } from 'react';
import { Sparkles, Sliders, RefreshCw, Info, Layers } from 'lucide-react';
import { useFarm } from '../../context/useFarm';
import type {
  AgriculturalInput,
  SoilType,
  IrrigationStatus,
  CropSeason,
} from '../../types/recommendation';

interface RecommendationFormProps {
  onSubmit: (inputs: AgriculturalInput, topK: number) => void;
  isLoading: boolean;
}

export const RecommendationForm: React.FC<RecommendationFormProps> = ({ onSubmit, isLoading }) => {
  const {
    agriculturalInputs,
    setAgriculturalInputs,
    fieldSoilType,
    setFieldSoilType,
    irrigationStatus,
    setIrrigationStatus,
    croppingSeason,
    setCroppingSeason,
    weatherState,
    soilState,
  } = useFarm();
  const [topK, setTopK] = useState(3);

  const handleChange = (field: keyof AgriculturalInput, val: string) => {
    const num = parseFloat(val);
    setAgriculturalInputs((prev) => ({
      ...prev,
      [field]: isNaN(num) ? 0 : num,
    }));
  };

  const handleAutofillFromEnvironment = () => {
    setAgriculturalInputs((prev) => {
      const next = { ...prev };
      if (weatherState.data) {
        next.temperature = Number(weatherState.data.temperature_c.toFixed(1));
        next.humidity = Number(weatherState.data.humidity_percent.toFixed(1));
      }
      if (soilState.data?.soil?.ph) {
        next.ph = Number(soilState.data.soil.ph.toFixed(1));
      }
      return next;
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(agriculturalInputs, topK);
  };

  const canAutofill = Boolean(weatherState.data || soilState.data?.soil?.ph);

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs p-5 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-emerald-600" />
            <span>Farm Nutrient & Environmental Parameters</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Agricultural inputs required by the 11-feature benchmark Random Forest model.
          </p>
        </div>

        {canAutofill && (
          <button
            type="button"
            onClick={handleAutofillFromEnvironment}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-semibold border border-emerald-200/80 transition-colors cursor-pointer self-start sm:self-auto"
          >
            <RefreshCw className="w-3.5 h-3.5 text-emerald-600" />
            <span>Autofill from Live Feeds</span>
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} className="mt-5 space-y-5">
        {/* Soil Nutrients Section */}
        <div>
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
            Soil Chemical Nutrients (NPK)
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
            <div>
              <label htmlFor="input-nitrogen" className="block text-xs font-semibold text-slate-700 mb-1">
                Nitrogen (N) <span className="text-slate-400 font-normal">kg/ha</span>
              </label>
              <input
                id="input-nitrogen"
                type="number"
                min="0"
                step="0.1"
                required
                value={agriculturalInputs.nitrogen}
                onChange={(e) => handleChange('nitrogen', e.target.value)}
                className="w-full text-xs font-medium px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label htmlFor="input-phosphorus" className="block text-xs font-semibold text-slate-700 mb-1">
                Phosphorus (P) <span className="text-slate-400 font-normal">kg/ha</span>
              </label>
              <input
                id="input-phosphorus"
                type="number"
                min="0"
                step="0.1"
                required
                value={agriculturalInputs.phosphorus}
                onChange={(e) => handleChange('phosphorus', e.target.value)}
                className="w-full text-xs font-medium px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label htmlFor="input-potassium" className="block text-xs font-semibold text-slate-700 mb-1">
                Potassium (K) <span className="text-slate-400 font-normal">kg/ha</span>
              </label>
              <input
                id="input-potassium"
                type="number"
                min="0"
                step="0.1"
                required
                value={agriculturalInputs.potassium}
                onChange={(e) => handleChange('potassium', e.target.value)}
                className="w-full text-xs font-medium px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
              />
            </div>
          </div>
        </div>

        {/* Climate & Soil Acidity Section */}
        <div>
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
            Climate & Soil pH
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
            <div>
              <label htmlFor="input-temperature" className="block text-xs font-semibold text-slate-700 mb-1">
                Temperature <span className="text-slate-400 font-normal">°C</span>
              </label>
              <input
                id="input-temperature"
                type="number"
                min="-20"
                max="60"
                step="0.1"
                required
                value={agriculturalInputs.temperature}
                onChange={(e) => handleChange('temperature', e.target.value)}
                className="w-full text-xs font-medium px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label htmlFor="input-humidity" className="block text-xs font-semibold text-slate-700 mb-1">
                Rel. Humidity <span className="text-slate-400 font-normal">%</span>
              </label>
              <input
                id="input-humidity"
                type="number"
                min="0"
                max="100"
                step="0.1"
                required
                value={agriculturalInputs.humidity}
                onChange={(e) => handleChange('humidity', e.target.value)}
                className="w-full text-xs font-medium px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label htmlFor="input-ph" className="block text-xs font-semibold text-slate-700 mb-1">
                Soil pH <span className="text-slate-400 font-normal">0–14</span>
              </label>
              <input
                id="input-ph"
                type="number"
                min="0"
                max="14"
                step="0.1"
                required
                value={agriculturalInputs.ph}
                onChange={(e) => handleChange('ph', e.target.value)}
                className="w-full text-xs font-medium px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label htmlFor="input-rainfall" className="block text-xs font-semibold text-slate-700 mb-1">
                Rainfall <span className="text-slate-400 font-normal">mm</span>
              </label>
              <input
                id="input-rainfall"
                type="number"
                min="0"
                step="0.1"
                required
                value={agriculturalInputs.rainfall}
                onChange={(e) => handleChange('rainfall', e.target.value)}
                className="w-full text-xs font-medium px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
              />
            </div>
          </div>
        </div>

        {/* Farmer Field Confirmation Section (Raichur / Yadgir Zone 2) */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-emerald-600" />
              <span>Field Soil & Water Confirmation</span>
            </h4>
            <span className="text-[10px] text-slate-500 font-medium">
              Overrules single-point SoilGrids estimate
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
            <div>
              <label htmlFor="input-soil-type" className="block text-xs font-semibold text-slate-700 mb-1">
                Field Soil Type
              </label>
              <select
                id="input-soil-type"
                value={fieldSoilType || ''}
                onChange={(e) => setFieldSoilType((e.target.value as SoilType) || null)}
                className="w-full text-xs font-medium px-3 py-2 bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-emerald-500 cursor-pointer"
              >
                <option value="">Auto-detect from SoilGrids (Estimate)</option>
                <option value="deep_black">Deep Black Soil (Vertisol / Yerri Bhumi)</option>
                <option value="medium_black">Medium Black Soil</option>
                <option value="red_sandy_loam">Red Sandy Loam / Chalka Soil (Alfisol)</option>
                <option value="loam">Mixed Alluvial / Loam</option>
              </select>
            </div>

            <div>
              <label htmlFor="input-irrigation-status" className="block text-xs font-semibold text-slate-700 mb-1">
                Irrigation Water Access
              </label>
              <select
                id="input-irrigation-status"
                value={irrigationStatus || ''}
                onChange={(e) => setIrrigationStatus((e.target.value as IrrigationStatus) || null)}
                className="w-full text-xs font-medium px-3 py-2 bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-emerald-500 cursor-pointer"
              >
                <option value="">Select Water Access</option>
                <option value="rainfed">Rainfed (Dryland / Monsoon dependent)</option>
                <option value="canal_irrigated">Canal Irrigated (Tungabhadra / Krishna)</option>
                <option value="borewell_irrigated">Borewell / Lift / Drip Irrigated</option>
              </select>
            </div>

            <div>
              <label htmlFor="input-season" className="block text-xs font-semibold text-slate-700 mb-1">
                Cropping Season
              </label>
              <select
                id="input-season"
                value={croppingSeason || ''}
                onChange={(e) => setCroppingSeason((e.target.value as CropSeason) || null)}
                className="w-full text-xs font-medium px-3 py-2 bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-emerald-500 cursor-pointer"
              >
                <option value="">Select Season</option>
                <option value="kharif">Kharif (Monsoon / Jun–Oct)</option>
                <option value="rabi">Rabi (Post-monsoon / Oct–Feb)</option>
                <option value="summer">Summer (Feb–May)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Top-K Candidate Selector & Submit */}
        <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-t border-slate-100">
          <div className="flex items-center gap-2">
            <label htmlFor="input-topk" className="text-xs font-semibold text-slate-700">Top-K Crops:</label>
            <select
              id="input-topk"
              aria-label="Select Top-K Crops"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="text-xs font-medium bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 focus:bg-white focus:outline-hidden cursor-pointer"
            >
              {[1, 2, 3, 4, 5, 6, 8, 10].map((k) => (
                <option key={k} value={k}>
                  Top {k} candidates
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="px-6 py-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold tracking-wide transition-all shadow-sm hover:shadow disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
          >
            <Sparkles className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>{isLoading ? 'Running Model Inference...' : 'Generate Crop Recommendations'}</span>
          </button>
        </div>
      </form>

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2 text-[11px] text-slate-500">
        <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        <span>
          Ratios (N/P, N/K, P/K, Rain/Temp) are engineered deterministically by the backend pipeline.
        </span>
      </div>
    </div>
  );
};
