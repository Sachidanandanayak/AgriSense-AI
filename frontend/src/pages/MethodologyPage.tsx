import React from 'react';
import { BookOpenCheck, ExternalLink, ShieldCheck, Scale, Droplets, Layers, Sparkles } from 'lucide-react';

export const MethodologyPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Title */}
      <div>
        <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
          <BookOpenCheck className="w-5 h-5 text-emerald-600" />
          <span>Scientific Methodology & Source Provenance</span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Detailed transparency documentation on agronomic baselines, remote sensing limitations, machine learning boundaries, and authoritative data provenance.
        </p>
      </div>

      {/* Principle 1: ML Model Boundary */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-700">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">
              1. Benchmark Machine Learning Model Scope
            </h2>
            <p className="text-xs text-slate-500">Phase 3 & Phase 8 Model Architecture</p>
          </div>
        </div>
        <p className="text-xs text-slate-700 leading-relaxed">
          The recommendation engine utilizes a Random Forest classifier trained on a controlled benchmark agronomic dataset of 2,200 trials covering 22 crop species. Its outputs represent statistical classification probabilities within feature space boundaries.
        </p>
        <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200 text-xs text-amber-900 leading-relaxed">
          <strong>Mandatory Caveat:</strong> The probability estimate returned by this model is <em>never</em> represented as a field-validated suitability score, commercial yield forecast, or harvest guarantee. AgriSense AI strictly forbids converting model classification likelihood into marketing percentages.
        </div>
      </div>

      {/* Principle 2: FAO ECOCROP Ecological Descriptors */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-700">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">
                2. FAO ECOCROP Crop Ecological Requirements
              </h2>
              <p className="text-xs text-slate-500">Phase 9 Evidence-Based Agronomic Profiles</p>
            </div>
          </div>
          <a
            href="https://ecocrop.apps.fao.org/ecocrop/srv/en/home"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-emerald-700 hover:underline inline-flex items-center gap-1 font-semibold"
          >
            <span>FAO EcoCrop Portal</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
        <p className="text-xs text-slate-700 leading-relaxed">
          Every crop profile in AgriSense AI is verified directly against the Food and Agriculture Organization (FAO) Crop Ecological Requirements Database.
        </p>
        <ul className="text-xs text-slate-600 space-y-1 list-disc list-inside">
          <li><strong>Thermal Limits:</strong> TMIN, TOPMN, TOPMX, TMAX (Absolute minimum, optimal range, absolute maximum temperature).</li>
          <li><strong>Precipitation Limits:</strong> RMIN, ROPMN, ROPMX, RMAX (Absolute minimum, optimal range, absolute maximum rainfall).</li>
          <li><strong>Soil pH Boundaries:</strong> PHMIN, PHOPMN, PHOPMX, PHMAX (Chemical acidity/alkalinity tolerances).</li>
          <li><strong>Physical Soil Requirements:</strong> TEXT, DRA, DEP (Soil texture groups, drainage tolerances, root depth).</li>
          <li><strong>Growth Cycle Duration:</strong> GMIN, GMAX (Crop growth cycle in days).</li>
        </ul>
      </div>

      {/* Principle 3: Sprengel-Liebig Law of the Minimum */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-700">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">
              3. The Law of the Minimum vs. Arbitrary Scoring Formulas
            </h2>
            <p className="text-xs text-slate-500">Carl Sprengel (1828) & Justus von Liebig (1840)</p>
          </div>
        </div>
        <p className="text-xs text-slate-700 leading-relaxed">
          Agricultural science establishes that crop performance is determined not by total resources available, but by the single scarcest limiting factor. For instance, high soil fertility cannot compensate for temperatures below biological freezing.
        </p>
        <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 leading-relaxed space-y-1">
          <p className="font-semibold text-slate-900">Why AgriSense AI Rejects Arbitrary Weighting Formulas:</p>
          <p>
            Formulas such as <code>Suitability = 30% NDVI + 30% soil + 40% weather</code> are unscientific inventions. AgriSense AI instead evaluates each environmental dimension transparently as <strong>favorable</strong>, <strong>caution</strong>, <strong>unfavorable</strong>, or <strong>unavailable</strong>.
          </p>
        </div>
      </div>

      {/* Principle 4: Water Advisory FAO-56 Standard */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-sky-50 text-sky-700">
              <Droplets className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">
                4. FAO-56 Penman-Monteith Crop Water Requirements
              </h2>
              <p className="text-xs text-slate-500">Allen, Pereira, Raes, & Smith (1998)</p>
            </div>
          </div>
          <a
            href="https://www.fao.org/land-water/resources/tools/software/cropwat/en"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-sky-700 hover:underline inline-flex items-center gap-1 font-semibold"
          >
            <span>FAO CROPWAT</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
        <p className="text-xs text-slate-700 leading-relaxed">
          Under FAO Irrigation and Drainage Paper No. 56, reference evapotranspiration (ET0) requires net solar radiation, daily temperature extrema, standardized 2-meter wind profiles, and vapor pressure. Seasonal crop water demand (ETc) requires stage-specific crop coefficients (Kc).
        </p>
        <div className="p-3.5 rounded-xl bg-sky-50/70 border border-sky-200 text-xs text-sky-950 leading-relaxed">
          <strong>Zero Fabrication Policy:</strong> Instantaneous weather readings (such as a single ambient temperature or current rain reading) cannot be presented as seasonal irrigation requirements. When radiation or Kc parameters are missing, the status is transparently marked <code>unavailable</code> with explicit parameter disclosures.
        </div>
      </div>

      {/* Principle 5: Remote Sensing Caveats */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-700">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">
              5. Sentinel-2 Satellite Remote Sensing Context
            </h2>
            <p className="text-xs text-slate-500">European Space Agency Copernicus Constellation</p>
          </div>
        </div>
        <p className="text-xs text-slate-700 leading-relaxed">
          Spectral indices (NDVI for canopy greenness, NDWI for surface water, NDMI for canopy moisture stress) provide spatial vegetative context. They reflect surface optical reflectance at the time of overpass.
        </p>
        <p className="text-xs text-slate-600 leading-relaxed italic">
          NDVI alone does not prove crop suitability, soil fertility, or pest immunity. Satellite indices must remain contextual indicators rather than crop suitability scores.
        </p>
      </div>
    </div>
  );
};
