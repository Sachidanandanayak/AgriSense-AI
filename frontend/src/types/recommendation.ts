import type { WeatherResponse } from './weather';
import type { SatelliteResponse } from './satellite';
import type { SoilResponse } from './soil';

export interface AgriculturalInput {
  nitrogen: number;
  phosphorus: number;
  potassium: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
}

export type SoilType = 'deep_black' | 'medium_black' | 'red_sandy_loam' | 'loam';
export type IrrigationStatus = 'rainfed' | 'canal_irrigated' | 'borewell_irrigated';
export type CropSeason = 'kharif' | 'rabi' | 'summer';
export type RegionalSuitabilityTier = 'tier1_recommended' | 'tier2_conditional' | 'tier3_incompatible';

export interface RegionalCropCandidate {
  crop_key: string;
  display_name: string;
  kannada_name: string;
  scientific_name: string;
  ecocrop_code: number;
  suitability_tier: RegionalSuitabilityTier;
  tier_label: string;
  sowing_window: string;
  recommended_varieties: string[];
  soil_compatibility_note: string;
  water_management_note: string;
  agronomic_advice: string[];
  provenance_sources: string[];
}

export interface RegionalAdvisoryReport {
  region_name: string;
  districts: string[];
  field_soil_type?: SoilType | null;
  irrigation_access?: IrrigationStatus | null;
  cropping_season?: CropSeason | null;
  candidates: RegionalCropCandidate[];
  context_notes: string[];
}

export interface RecommendationRequest {
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
}

export interface CropRecommendationItem {
  crop: string;
  rank: number;
  probability_estimate: number;
  confidence_percentage: string;
}

export interface EnvironmentalContext {
  weather?: WeatherResponse | null;
  satellite?: SatelliteResponse | null;
  soil?: SoilResponse | null;
}

export interface DataQualityReport {
  model_available: boolean;
  model_version: string;
  weather_available: boolean;
  satellite_available: boolean;
  soil_available: boolean;
  missing_sources: string[];
  warnings: string[];
}

export interface RecommendationResponse {
  latitude: number;
  longitude: number;
  observation_date?: string | null;
  recommendations: CropRecommendationItem[];
  regional_advisory?: RegionalAdvisoryReport | null;
  environmental_context: EnvironmentalContext;
  data_quality: DataQualityReport;
  explanation: string[];
  limitations: string[];
  model_input_features: Record<string, number>;
  disclaimer: string;
}
