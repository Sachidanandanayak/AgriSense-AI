/**
 * Sentinel-2 Satellite Response matching backend app.schemas.satellite
 */
export interface IndexStatistics {
  min?: number | null;
  max?: number | null;
  mean?: number | null;
  median?: number | null;
  std_dev?: number | null;
}

export interface SatelliteResponse {
  latitude: number;
  longitude: number;
  radius_m: number;
  start_date: string;
  end_date: string;
  usable_observations: number;
  cloud_probability_threshold: number;
  ndvi_median: number;
  ndwi_median: number;
  ndmi_median: number;
  data_source: string;
  statistics?: Record<string, IndexStatistics> | null;
  disclaimer: string;
}
