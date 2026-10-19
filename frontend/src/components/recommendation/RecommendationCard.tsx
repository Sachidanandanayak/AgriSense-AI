import React from 'react';
import { Award, ArrowRight, ShieldCheck } from 'lucide-react';
import type { CropRecommendationItem } from '../../types/recommendation';

interface RecommendationCardProps {
  item: CropRecommendationItem;
  onInspectAdvisory?: (crop: string) => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  item,
  onInspectAdvisory,
}) => {
  const isTopRank = item.rank === 1;

  // Capitalize crop name
  const cropTitle = item.crop.charAt(0).toUpperCase() + item.crop.slice(1);

  return (
    <div
      className={`rounded-2xl border p-5 transition-all duration-200 flex flex-col justify-between ${
        isTopRank
          ? 'bg-gradient-to-br from-emerald-50/70 to-white border-emerald-300/80 shadow-xs'
          : 'bg-white border-slate-200/90 shadow-2xs hover:shadow-xs'
      }`}
    >
      <div>
        {/* Header: Rank + Confidence */}
        <div className="flex items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center justify-center w-7 h-7 rounded-lg text-xs font-bold ${
                isTopRank
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-700 font-semibold'
              }`}
            >
              #{item.rank}
            </span>
            <div>
              <h3 className="text-base font-bold text-slate-900 tracking-tight">{cropTitle}</h3>
            </div>
          </div>

          <div className="text-right">
            <div className="text-sm font-extrabold text-emerald-800">
              {item.confidence_percentage}
            </div>
            <p className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider">
              Confidence Estimate
            </p>
          </div>
        </div>

        {/* Probability bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-xs text-slate-600 mb-1.5 font-medium">
            <span>Model Probability</span>
            <span className="font-mono text-[11px]">
              {(item.probability_estimate * 100).toFixed(2)}% (prob: {item.probability_estimate.toFixed(4)})
            </span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isTopRank ? 'bg-emerald-600' : 'bg-emerald-500/70'
              }`}
              style={{ width: `${Math.min(100, item.probability_estimate * 100)}%` }}
            />
          </div>
        </div>

        <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-100 text-[11px] text-slate-600 leading-relaxed flex items-start gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          <p>
            Preserved Random Forest classification likelihood relative to trial dataset distribution.
            Not a guaranteed harvest or yield percentage.
          </p>
        </div>
      </div>

      {/* Action Footer */}
      {onInspectAdvisory && (
        <div className="mt-4 pt-3 border-t border-slate-100">
          <button
            type="button"
            onClick={() => onInspectAdvisory(item.crop)}
            className="w-full py-2 px-3 rounded-xl bg-white hover:bg-slate-50 text-slate-800 text-xs font-semibold border border-slate-200 transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-2xs hover:shadow-xs"
          >
            <Award className="w-3.5 h-3.5 text-emerald-600" />
            <span>Inspect FAO ECOCROP Compatibility</span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
          </button>
        </div>
      )}
    </div>
  );
};
