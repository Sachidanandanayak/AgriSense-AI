import type { WeatherResponse } from './weather';
import type { SatelliteResponse } from './satellite';
import type { SoilResponse } from './soil';
import type {
  AgriculturalInput,
  EnvironmentalContext,
  RecommendationResponse,
  SoilType,
  IrrigationStatus,
  CropSeason,
  RegionalCropCandidate,
  RegionalAdvisoryReport,
} from './recommendation';

export type CompatibilityStatus = 'favorable' | 'caution' | 'unfavorable' | 'unavailable';
export type WaterAdvisoryStatus = 'available' | 'unavailable';

export interface RequirementProvenance {
  source_name: string;
  source_url: string;
  source_field?: string | null;
  source_version_or_reference?: string | null;
  notes?: string | null;
}

export interface CropEnvironmentalRequirement {
  crop_name: string;
  scientific_name: string;
  ecocrop_code?: number | null;
  common_name?: string | null;
  temp_min_c?: number | null;
  temp_opt_min_c?: number | null;
  temp_opt_max_c?: number | null;
  temp_max_c?: number | null;
  rainfall_min_mm?: number | null;
  rainfall_opt_min_mm?: number | null;
  rainfall_opt_max_mm?: number | null;
  rainfall_max_mm?: number | null;
  soil_ph_min?: number | null;
  soil_ph_opt_min?: number | null;
  soil_ph_opt_max?: number | null;
  soil_ph_max?: number | null;
  soil_textures_optimal?: string[] | null;
  soil_textures_absolute?: string[] | null;
  soil_drainage_optimal?: string | null;
  soil_drainage_absolute?: string | null;
  soil_depth_optimal?: string | null;
  soil_depth_absolute?: string | null;
  soil_fertility_optimal?: string | null;
  soil_salinity_optimal?: string | null;
  crop_cycle_min_days?: number | null;
  crop_cycle_max_days?: number | null;
  provenance: RequirementProvenance;
}

export interface VariableCompatibility {
  variable: string;
  status: CompatibilityStatus;
  observed_value?: string | number | null;
  observed_unit?: string | null;
  documented_optimal_range?: string | null;
  documented_absolute_range?: string | null;
  reason: string;
  source: string;
}

export interface WaterAdvisory {
  status: WaterAdvisoryStatus;
  methodology: string;
  reference_evapotranspiration_et0_mm_day?: number | null;
  crop_coefficient_kc?: number | null;
  crop_evapotranspiration_etc_mm_day?: number | null;
  estimated_irrigation_requirement_mm?: number | null;
  reason: string;
  missing_parameters: string[];
  notes: string;
}

export interface SatelliteEnvironmentalContext {
  available: boolean;
  observation_window?: string | null;
  usable_observations?: number | null;
  ndvi_median?: number | null;
  ndwi_median?: number | null;
  ndmi_median?: number | null;
  summary: string;
  disclaimer: string;
}

export interface CropAdvisoryItem {
  crop: string;
  scientific_name?: string | null;
  rank: number;
  probability_estimate: number;
  confidence_percentage: string;
  overall_compatibility: CompatibilityStatus;
  compatibility_evaluations: Record<string, VariableCompatibility>;
  growth_cycle_days?: string | null;
  risk_flags: string[];
  advisory_notes: string[];
  requirement_provenance?: RequirementProvenance | null;
}

export interface DataQualityAudit {
  model_available: boolean;
  weather_available: boolean;
  satellite_available: boolean;
  soil_available: boolean;
  missing_sources: string[];
  stale_sources: string[];
  risk_flags: string[];
  warnings: string[];
}

export interface FarmAdvisoryRequest {
  latitude: number;
  longitude: number;
  observation_date?: string | null;
  agricultural_inputs?: AgriculturalInput | null;
  nitrogen?: number | null;
  phosphorus?: number | null;
  potassium?: number | null;
  temperature?: number | null;
  humidity?: number | null;
  ph?: number | null;
  rainfall?: number | null;
  top_k?: number;
  weather_context?: WeatherResponse | null;
  satellite_context?: SatelliteResponse | null;
  soil_context?: SoilResponse | null;
  fetch_live_weather?: boolean;
  fetch_live_satellite?: boolean;
  fetch_live_soil?: boolean;
  soil_type?: SoilType | null;
  irrigation_status?: IrrigationStatus | null;
  season?: CropSeason | null;
  rainfall_is_annual?: boolean | null;
  recommendation_response?: RecommendationResponse | null;
  fao56_water_inputs?: Record<string, number> | null;
}

export interface FarmAdvisoryResponse {
  latitude: number;
  longitude: number;
  observation_date?: string | null;
  crop_advisories: CropAdvisoryItem[];
  regional_advisory?: RegionalAdvisoryReport | null;
  water_advisory: WaterAdvisory;
  satellite_context?: SatelliteEnvironmentalContext | null;
  risk_flags: string[];
  environmental_context: EnvironmentalContext;
  data_quality: DataQualityAudit;
  explanations: string[];
  limitations: string[];
  disclaimer: string;
}

export type { RegionalCropCandidate, RegionalAdvisoryReport };
