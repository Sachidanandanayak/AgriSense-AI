import React, { useState, useEffect, useCallback } from 'react';
import type { FarmLocation, ApiState } from '../types/common';
import { AGRICULTURAL_PRESETS } from '../types/common';
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
import { fetchWeather } from '../api/weather';
import { fetchSoil } from '../api/soil';
import { fetchSatellite } from '../api/satellite';
import { checkBackendHealth } from '../api/health';
import { FarmContext } from './FarmContextBase';
export type { FarmContextType } from './FarmContextBase';

const defaultPreset = AGRICULTURAL_PRESETS[0];

const defaultAgriculturalInputs: AgriculturalInput = {
  nitrogen: defaultPreset.defaultInputs?.nitrogen ?? 80,
  phosphorus: defaultPreset.defaultInputs?.phosphorus ?? 40,
  potassium: defaultPreset.defaultInputs?.potassium ?? 40,
  temperature: defaultPreset.defaultInputs?.temperature ?? 26.5,
  humidity: defaultPreset.defaultInputs?.humidity ?? 65.0,
  ph: defaultPreset.defaultInputs?.ph ?? 6.8,
  rainfall: defaultPreset.defaultInputs?.rainfall ?? 120.0,
};

export const FarmProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [location, setLocation] = useState<FarmLocation>({
    latitude: defaultPreset.latitude,
    longitude: defaultPreset.longitude,
    name: defaultPreset.name,
    region: defaultPreset.region,
  });

  const [agriculturalInputs, setAgriculturalInputs] = useState<AgriculturalInput>(defaultAgriculturalInputs);
  const [fieldSoilType, setFieldSoilType] = useState<SoilType | null>('deep_black');
  const [irrigationStatus, setIrrigationStatus] = useState<IrrigationStatus | null>('canal_irrigated');
  const [croppingSeason, setCroppingSeason] = useState<CropSeason | null>('kharif');

  const [weatherState, setWeatherState] = useState<ApiState<WeatherResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const [soilState, setSoilState] = useState<ApiState<SoilResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const [satelliteState, setSatelliteState] = useState<ApiState<SatelliteResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const [recommendationState, setRecommendationState] = useState<ApiState<RecommendationResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const [advisoryState, setAdvisoryState] = useState<ApiState<FarmAdvisoryResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  const refreshBackendHealth = useCallback(async () => {
    const res = await checkBackendHealth();
    setBackendOnline(res.healthy);
  }, []);

  useEffect(() => {
    let mounted = true;
    checkBackendHealth().then((res) => {
      if (mounted) setBackendOnline(res.healthy);
    });
    const interval = setInterval(() => {
      checkBackendHealth().then((res) => {
        if (mounted) setBackendOnline(res.healthy);
      });
    }, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const fetchEnvironmentalData = useCallback(async (targetLat?: number, targetLon?: number) => {
    const lat = targetLat ?? location.latitude;
    const lon = targetLon ?? location.longitude;

    // Reset loading states
    setWeatherState((prev) => ({ ...prev, loading: true, error: null }));
    setSoilState((prev) => ({ ...prev, loading: true, error: null }));
    setSatelliteState((prev) => ({ ...prev, loading: true, error: null }));

    // Fetch weather
    try {
      const weather = await fetchWeather(lat, lon);
      setWeatherState({ data: weather, loading: false, error: null });
      if (weather.temperature_c !== undefined && weather.humidity_percent !== undefined) {
        setAgriculturalInputs((prev) => ({
          ...prev,
          temperature: Number(weather.temperature_c.toFixed(1)),
          humidity: Number(weather.humidity_percent.toFixed(1)),
        }));
      }
    } catch (err) {
      setWeatherState({
        data: null,
        loading: false,
        error: err instanceof Error ? err.message : 'Weather unavailable',
      });
    }

    // Fetch soil
    try {
      const soil = await fetchSoil(lat, lon, '0-5cm');
      setSoilState({ data: soil, loading: false, error: null });
      if (soil.soil?.ph !== undefined && soil.soil.ph !== null) {
        setAgriculturalInputs((prev) => ({
          ...prev,
          ph: Number(soil.soil.ph!.toFixed(1)),
        }));
      }
    } catch (err) {
      setSoilState({
        data: null,
        loading: false,
        error: err instanceof Error ? err.message : 'Soil data unavailable',
      });
    }

    // Fetch satellite (default recent 14-day window)
    try {
      const today = new Date();
      const past = new Date();
      past.setDate(today.getDate() - 14);
      const startStr = past.toISOString().split('T')[0];
      const endStr = today.toISOString().split('T')[0];

      const sat = await fetchSatellite(lat, lon, startStr, endStr, 500);
      setSatelliteState({ data: sat, loading: false, error: null });
    } catch (err) {
      setSatelliteState({
        data: null,
        loading: false,
        error: err instanceof Error ? err.message : 'Satellite observations unavailable',
      });
    }
  }, [location.latitude, location.longitude]);

  const applyPreset = useCallback((presetIndex: number) => {
    const p = AGRICULTURAL_PRESETS[presetIndex];
    if (!p) return;
    setLocation({
      latitude: p.latitude,
      longitude: p.longitude,
      name: p.name,
      region: p.region,
    });
    if (p.defaultInputs) {
      setAgriculturalInputs(p.defaultInputs);
    }
  }, []);

  return (
    <FarmContext.Provider
      value={{
        location,
        setLocation,
        applyPreset,
        agriculturalInputs,
        setAgriculturalInputs,
        fieldSoilType,
        setFieldSoilType,
        irrigationStatus,
        setIrrigationStatus,
        croppingSeason,
        setCroppingSeason,
        weatherState,
        soilState,
        satelliteState,
        recommendationState,
        setRecommendationState,
        advisoryState,
        setAdvisoryState,
        fetchEnvironmentalData,
        backendOnline,
        refreshBackendHealth,
      }}
    >
      {children}
    </FarmContext.Provider>
  );
};
