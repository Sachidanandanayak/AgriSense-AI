import React, { useState } from 'react';
import type { CropAdvisoryItem } from '../../types/advisory';
import { StatusBadge } from '../common/StatusBadge';
import { VariableBreakdown } from './VariableBreakdown';
import { ChevronDown, ChevronUp, ExternalLink, Calendar, AlertCircle } from 'lucide-react';

interface CropAdvisoryCardProps {
  item: CropAdvisoryItem;
}

export const CropAdvisoryCard: React.FC<CropAdvisoryCardProps> = ({ item }) => {
  const [expanded, setExpanded] = useState(true);
  const [showProvenance, setShowProvenance] = useState(false);

  const cropTitle = item.crop.charAt(0).toUpperCase() + item.crop.slice(1);
  const prov = item.requirement_provenance;

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden transition-all">
      {/* Header Bar */}
      <div className="p-5 bg-gradient-to-r from-slate-50/80 to-white border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <span className="w-8 h-8 rounded-xl bg-slate-900 text-white font-bold text-xs flex items-center justify-center shrink-0 shadow-2xs">
            #{item.rank}
          </span>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-bold text-slate-900 tracking-tight">{cropTitle}</h3>
              {item.scientific_name && (
                <span className="text-xs italic text-slate-500 font-serif">
                  ({item.scientific_name})
                </span>
              )}
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-500 mt-0.5">
              <span>
                ML Confidence:{' '}
                <strong className="text-emerald-800">{item.confidence_percentage}</strong>
              </span>
              {item.growth_cycle_days && (
                <span className="flex items-center gap-1 text-slate-600">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  Cycle: {item.growth_cycle_days}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Overall Status & Expand */}
        <div className="flex items-center gap-3 self-end md:self-auto">
          <div className="text-right">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-0.5">
              Overall Compatibility
            </span>
            <StatusBadge status={item.overall_compatibility} size="md" />
          </div>

          <button
            onClick={() => setExpanded(!expanded)}
            className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors cursor-pointer"
            aria-label={expanded ? 'Collapse Details' : 'Expand Details'}
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="p-5 sm:p-6 space-y-5">
          {/* Advisory Notes / Limiting Factors */}
          {item.advisory_notes.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Agronomic Observations & Actionable Guidance
              </h4>
              <div className="space-y-1.5">
                {item.advisory_notes.map((note, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-amber-50/60 border border-amber-200/70 text-xs text-amber-900 leading-relaxed flex items-start gap-2"
                  >
                    <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <span>{note}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Variable Breakdown */}
          <div>
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
              Documented Environmental Variable Compatibility (FAO ECOCROP)
            </h4>
            <VariableBreakdown evaluations={item.compatibility_evaluations} />
          </div>

          {/* Provenance Accordion Toggle */}
          {prov && (
            <div className="pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowProvenance(!showProvenance)}
                className="text-xs font-semibold text-emerald-800 hover:text-emerald-900 flex items-center gap-1.5 cursor-pointer"
              >
                <span>{showProvenance ? 'Hide' : 'View'} Authoritative Source Provenance Metadata</span>
                <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showProvenance ? 'rotate-180' : ''}`} />
              </button>

              {showProvenance && (
                <div className="mt-3 p-4 rounded-xl bg-slate-50 border border-slate-200/80 text-xs space-y-2 text-slate-700">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-900">{prov.source_name}</span>
                    <a
                      href={prov.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-emerald-700 hover:underline font-medium text-[11px]"
                    >
                      <span>Visit Portal</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  {prov.source_version_or_reference && (
                    <p className="text-[11px] text-slate-600">
                      <strong>Reference:</strong> {prov.source_version_or_reference}
                    </p>
                  )}
                  {prov.source_field && (
                    <p className="text-[11px] font-mono text-slate-600 break-words">
                      <strong>Database Fields:</strong> {prov.source_field}
                    </p>
                  )}
                  {prov.notes && (
                    <p className="text-[11px] text-slate-500 italic mt-1">
                      {prov.notes}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
