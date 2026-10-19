import React from 'react';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';

interface RiskFlagListProps {
  flags: string[];
}

export const RiskFlagList: React.FC<RiskFlagListProps> = ({ flags }) => {
  if (flags.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 text-xs text-emerald-900 flex items-center gap-2.5">
        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
        <span className="font-medium">
          Zero agronomic risk flags or environmental boundary violations identified for current conditions.
        </span>
      </div>
    );
  }

  // Map machine keys to friendly explanations
  const flagDescriptions: Record<string, string> = {
    temperature_outside_documented_range:
      'Observed temperature falls outside the documented optimal or absolute FAO ECOCROP viability boundaries.',
    rainfall_outside_documented_range:
      'Observed rainfall falls outside documented optimal or absolute FAO ECOCROP viability boundaries.',
    soil_ph_outside_documented_range:
      'Observed soil pH deviates from documented optimal or absolute FAO ECOCROP viability boundaries.',
    soil_texture_outside_documented_range:
      'Classified physical soil texture is outside documented FAO ECOCROP viable texture classes.',
    soil_texture_information_missing:
      'Soil clay/sand physical texture fraction information is missing or unrecorded in context.',
    weather_data_missing:
      'Live meteorological observations were not available; evaluations defaulted to supplied seasonal inputs.',
    satellite_data_missing:
      'Sentinel-2 spectral earth observations were not available for vegetative canopy analysis.',
    soil_data_missing:
      'Digital soil mapping (ISRIC SoilGrids) context was not available for the target coordinates.',
    stale_environmental_data:
      'Supplied environmental observations exceeded maximum freshness windows relative to reference date.',
    crop_requirement_data_unavailable:
      'Authoritative FAO ECOCROP requirement profile is unavailable for one or more evaluated species.',
  };

  return (
    <div className="space-y-2.5">
      {flags.map((flag) => {
        const desc = flagDescriptions[flag] || `Agronomic operational risk indicator: ${flag}`;
        return (
          <div
            key={flag}
            className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/90 text-amber-950 flex items-start gap-3 shadow-2xs"
          >
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold font-mono text-amber-900">{flag}</span>
                <span className="text-[10px] px-2 py-0.2 rounded-full bg-amber-200/70 text-amber-900 font-semibold">
                  Risk Indicator
                </span>
              </div>
              <p className="text-xs text-amber-800/90 mt-1 leading-relaxed">{desc}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};
