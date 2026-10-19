/**
 * ISRIC SoilGrids 2.0 Response matching backend app.schemas.soil
 */
export interface SoilProperties {
  ph?: number | null;
  clay_pct?: number | null;
  sand_pct?: number | null;
  silt_pct?: number | null;
  organic_carbon_g_kg?: number | null;
  bulk_density?: number | null;
  cec?: number | null;
  nitrogen_g_kg?: number | null;
}

export interface SoilResponse {
  latitude: number;
  longitude: number;
  depth_interval: string;
  soil: SoilProperties;
  data_source: string;
  resolution_m: number;
  disclaimer: string;
}
