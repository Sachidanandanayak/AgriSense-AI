import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Calendar,
  Layers,
  Droplets,
  ExternalLink,
  BookOpen,
} from 'lucide-react';
import type {
  RegionalAdvisoryReport,
  RegionalCropCandidate,
  RegionalSuitabilityTier,
} from '../../types/recommendation';

interface RegionalCandidatesSectionProps {
  report?: RegionalAdvisoryReport | null;
}

export const RegionalCandidatesSection: React.FC<RegionalCandidatesSectionProps> = ({ report }) => {
  if (!report) {
    return null;
  }

  const getTierBadge = (tier: RegionalSuitabilityTier, label: string) => {
    switch (tier) {
      case 'tier1_recommended':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>{label || 'Tier 1: Recommended Primary Candidate'}</span>
          </span>
        );
      case 'tier2_conditional':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>{label || 'Tier 2: Conditional / Management Required'}</span>
          </span>
        );
      case 'tier3_incompatible':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300">
            <XCircle className="w-3.5 h-3.5 text-rose-600" />
            <span>{label || 'Tier 3: Incompatible / Agronomic Hazard'}</span>
          </span>
        );
    }
  };

  const getBorderColor = (tier: RegionalSuitabilityTier) => {
    switch (tier) {
      case 'tier1_recommended':
        return 'border-emerald-200/90 bg-emerald-50/20';
      case 'tier2_conditional':
        return 'border-amber-200/90 bg-amber-50/20';
      case 'tier3_incompatible':
        return 'border-slate-200 bg-slate-50/60 opacity-85';
    }
  };

  const formatSoilName = (soil?: string | null) => {
    if (!soil) return 'Auto-detect / Field Unconfirmed';
    if (soil === 'deep_black') return 'Deep Black Soil (Vertisol / Yerri Bhumi)';
    if (soil === 'medium_black') return 'Medium Black Soil';
    if (soil === 'red_sandy_loam') return 'Red Sandy Loam / Chalka Soil (Alfisol)';
    if (soil === 'loam') return 'Mixed Alluvial / Loam';
    return soil;
  };

  const formatIrrigationName = (irr?: string | null) => {
    if (!irr) return 'Unconfirmed Water Access';
    if (irr === 'rainfed') return 'Rainfed (Dryland / Monsoon dependent)';
    if (irr === 'canal_irrigated') return 'Canal Irrigated (Tungabhadra / Upper Krishna Command)';
    if (irr === 'borewell_irrigated') return 'Borewell / Lift / Drip Irrigated';
    return irr;
  };

  const formatSeasonName = (season?: string | null) => {
    if (!season) return 'Unspecified Season';
    if (season === 'kharif') return 'Kharif (Monsoon / Jun–Oct)';
    if (season === 'rabi') return 'Rabi (Post-monsoon / Oct–Feb)';
    if (season === 'summer') return 'Summer (Feb–May)';
    return season;
  };

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="bg-gradient-to-r from-emerald-900 to-slate-900 text-white rounded-2xl p-5 sm:p-6 shadow-xs border border-emerald-800/40">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-emerald-700/80 text-emerald-100">
                UAS Raichur & ICAR Package of Practices
              </span>
              <span className="text-xs text-emerald-300 font-medium">
                Districts: {report.districts.join(' & ')} (Zone 2 NEDZ / Zone 1)
              </span>
            </div>
            <h2 className="text-lg sm:text-xl font-bold tracking-tight text-white">
              Locally Relevant Crop Candidates
            </h2>
            <p className="text-xs text-emerald-200/90 max-w-3xl leading-relaxed">
              Agronomic suitability evaluated strictly against regional field trials from the University of Agricultural Sciences, Raichur and ICAR-KVK. Prioritizes certified regional staples across farmer-confirmed soil and water conditions.
            </p>
          </div>

          <div className="shrink-0 bg-white/10 backdrop-blur-xs p-3 rounded-xl border border-white/10 text-right self-start md:self-auto">
            <span className="text-[10px] uppercase font-bold text-emerald-300 block">
              Evaluated Candidates
            </span>
            <span className="text-xl font-extrabold text-white">
              {report.candidates.length} Local Crops
            </span>
          </div>
        </div>

        {/* Confirmed Field Parameters Bar */}
        <div className="mt-4 pt-4 border-t border-emerald-800/60 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="flex items-center gap-2 bg-emerald-950/60 px-3 py-2 rounded-lg border border-emerald-800/50">
            <Layers className="w-4 h-4 text-emerald-400 shrink-0" />
            <div>
              <span className="text-[10px] uppercase text-emerald-300/80 block font-semibold">Field Soil</span>
              <span className="font-semibold text-white">{formatSoilName(report.field_soil_type)}</span>
            </div>
          </div>

          <div className="flex items-center gap-2 bg-emerald-950/60 px-3 py-2 rounded-lg border border-emerald-800/50">
            <Droplets className="w-4 h-4 text-cyan-400 shrink-0" />
            <div>
              <span className="text-[10px] uppercase text-emerald-300/80 block font-semibold">Irrigation Access</span>
              <span className="font-semibold text-white">{formatIrrigationName(report.irrigation_access)}</span>
            </div>
          </div>

          <div className="flex items-center gap-2 bg-emerald-950/60 px-3 py-2 rounded-lg border border-emerald-800/50">
            <Calendar className="w-4 h-4 text-amber-400 shrink-0" />
            <div>
              <span className="text-[10px] uppercase text-emerald-300/80 block font-semibold">Cropping Season</span>
              <span className="font-semibold text-white">{formatSeasonName(report.cropping_season)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Context Notes Banner */}
      {report.context_notes.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/90 text-xs text-slate-700 space-y-1">
          <span className="font-bold text-slate-900 block mb-1">Agro-Ecological Context & Notes:</span>
          <ul className="list-disc list-inside space-y-1 text-slate-600">
            {report.context_notes.map((note, idx) => (
              <li key={idx}>{note}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Candidate Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {report.candidates.map((crop: RegionalCropCandidate) => (
          <div
            key={crop.crop_key}
            className={`rounded-2xl border p-5 shadow-xs transition-all hover:shadow-sm space-y-4 ${getBorderColor(
              crop.suitability_tier
            )}`}
          >
            {/* Card Header */}
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="text-base font-bold text-slate-900">
                    {crop.display_name}
                  </h3>
                  <span className="text-xs font-semibold text-emerald-800 bg-emerald-100/80 px-2 py-0.5 rounded-md">
                    {crop.kannada_name}
                  </span>
                </div>
                <p className="text-xs text-slate-500 italic mt-0.5">
                  {crop.scientific_name} (EcoCrop #{crop.ecocrop_code})
                </p>
              </div>

              {getTierBadge(crop.suitability_tier, crop.tier_label)}
            </div>

            {/* Sowing Calendar */}
            <div className="flex items-center gap-2 text-xs bg-white/90 p-2.5 rounded-xl border border-slate-200/80">
              <Calendar className="w-4 h-4 text-emerald-600 shrink-0" />
              <div>
                <span className="font-semibold text-slate-700">Optimal Sowing Window: </span>
                <span className="font-bold text-slate-900">{crop.sowing_window}</span>
              </div>
            </div>

            {/* Certified Varieties */}
            <div className="space-y-1.5">
              <span className="text-[11px] uppercase font-bold text-slate-600 tracking-wider block">
                Certified UAS Raichur & ICAR Varieties:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {crop.recommended_varieties.map((v, i) => (
                  <span
                    key={i}
                    className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-800 shadow-2xs"
                  >
                    {v}
                  </span>
                ))}
              </div>
            </div>

            {/* Soil Compatibility Note */}
            <div className="text-xs space-y-1 bg-white/80 p-3 rounded-xl border border-slate-200/80">
              <div className="flex items-center gap-1.5 font-bold text-slate-800">
                <Layers className="w-3.5 h-3.5 text-amber-600" />
                <span>Soil Behavior & Compatibility:</span>
              </div>
              <p className="text-slate-600 leading-relaxed pl-5">{crop.soil_compatibility_note}</p>
            </div>

            {/* Water Management Note */}
            <div className="text-xs space-y-1 bg-white/80 p-3 rounded-xl border border-slate-200/80">
              <div className="flex items-center gap-1.5 font-bold text-slate-800">
                <Droplets className="w-3.5 h-3.5 text-sky-600" />
                <span>Water & Irrigation Management:</span>
              </div>
              <p className="text-slate-600 leading-relaxed pl-5">{crop.water_management_note}</p>
            </div>

            {/* Agronomic Advice Bullets */}
            {crop.agronomic_advice.length > 0 && (
              <div className="text-xs space-y-1.5 pt-1">
                <span className="text-[11px] uppercase font-bold text-slate-600 tracking-wider block">
                  Actionable Package of Practices Advice:
                </span>
                <ul className="list-disc list-inside space-y-1 text-slate-600 leading-relaxed">
                  {crop.agronomic_advice.map((adv, idx) => (
                    <li key={idx}>{adv}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Provenance Citations */}
            {crop.provenance_sources.length > 0 && (
              <div className="pt-2 border-t border-slate-200/70 text-[11px] text-slate-500 space-y-1">
                <span className="font-semibold text-slate-700 flex items-center gap-1">
                  <BookOpen className="w-3 h-3 text-emerald-600" />
                  <span>Authoritative Provenance:</span>
                </span>
                <div className="space-y-0.5">
                  {crop.provenance_sources.map((src, idx) => {
                    const parts = src.split(': http');
                    const label = parts[0];
                    const url = parts.length > 1 ? `http${parts[1]}` : null;
                    return (
                      <div key={idx} className="flex items-center gap-1 text-slate-600 truncate">
                        <span>• {label}</span>
                        {url && (
                          <a
                            href={url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-emerald-700 hover:text-emerald-900 inline-flex items-center gap-0.5 font-medium underline"
                          >
                            <ExternalLink className="w-2.5 h-2.5 inline" />
                            <span>Link</span>
                          </a>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
