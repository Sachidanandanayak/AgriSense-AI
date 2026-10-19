/**
 * Weather Response matching backend app.schemas.weather.WeatherResponse
 */
export interface WeatherResponse {
  latitude: number;
  longitude: number;
  temperature_c: number;
  humidity_percent: number;
  rainfall_mm: number;
  wind_speed_mps: number;
  weather_timestamp?: string | null;
}
