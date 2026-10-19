import React from 'react';
import { ShieldAlert, BookOpen } from 'lucide-react';

interface DisclaimerBoxProps {
  title?: string;
  disclaimer: string;
  className?: string;
}

export const DisclaimerBox: React.FC<DisclaimerBoxProps> = ({
  title = 'Mandatory Scientific & Operational Disclaimer',
  disclaimer,
  className = '',
}) => {
  return (
    <div
      className={`rounded-xl border border-amber-200/90 bg-amber-50/60 p-4.5 text-amber-950 shadow-xs ${className}`}
    >
      <div className="flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
        <div className="space-y-1.5 flex-1">
          <div className="flex items-center gap-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-900">
              {title}
            </h4>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-200/70 text-amber-900 font-semibold">
              Authoritative Notice
            </span>
          </div>
          <p className="text-xs text-amber-900/90 leading-relaxed font-normal">
            {disclaimer}
          </p>
          <div className="pt-1 flex items-center gap-1.5 text-[11px] text-amber-800 font-medium">
            <BookOpen className="w-3.5 h-3.5" />
            <span>
              Always verify agronomic recommendations with local certified agricultural extension officers and soil laboratories.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
