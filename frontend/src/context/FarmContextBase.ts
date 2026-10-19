import { createContext } from 'react';
import type { FarmLocation, ApiState } from '../types/common';
import type { WeatherResponse } from '../types/weather';
import type { SoilResponse } from '../types/soil';
import type { SatelliteResponse } from '../types/satellite';
import type {
  RecommendationResponse,
  AgriculturalInput,
  SoilType,
  IrrigationStatus,
  CropSeason,
} from '../types/recommendation';
import type { FarmAdvisoryResponse } from '../types/advisory';

export interface FarmContextType {
  location: FarmLocation;
  setLocation: (loc: FarmLocation) => void;
  applyPreset: (presetIndex: number) => void;

  // Agricultural inputs
  agriculturalInputs: AgriculturalInput;
  setAgriculturalInputs: React.Dispatch<React.SetStateAction<AgriculturalInput>>;

  // Field confirmation parameters
  fieldSoilType: SoilType | null;
  setFieldSoilType: React.Dispatch<React.SetStateAction<SoilType | null>>;
  irrigationStatus: IrrigationStatus | null;
  setIrrigationStatus: React.Dispatch<React.SetStateAction<IrrigationStatus | null>>;
  croppingSeason: CropSeason | null;
  setCroppingSeason: React.Dispatch<React.SetStateAction<CropSeason | null>>;

  // Environmental context states
  weatherState: ApiState<WeatherResponse>;
  soilState: ApiState<SoilResponse>;
  satelliteState: ApiState<SatelliteResponse>;

  // Recommendations and Advisory states
  recommendationState: ApiState<RecommendationResponse>;
  setRecommendationState: React.Dispatch<React.SetStateAction<ApiState<RecommendationResponse>>>;
  advisoryState: ApiState<FarmAdvisoryResponse>;
  setAdvisoryState: React.Dispatch<React.SetStateAction<ApiState<FarmAdvisoryResponse>>>;

  // Actions
  fetchEnvironmentalData: (lat?: number, lon?: number) => Promise<void>;
  backendOnline: boolean | null;
  refreshBackendHealth: () => Promise<void>;
}

export const FarmContext = createContext<FarmContextType | undefined>(undefined);
