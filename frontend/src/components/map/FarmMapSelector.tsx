import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, Navigation, Compass, AlertCircle } from 'lucide-react';
import { useFarm } from '../../context/useFarm';
import { AGRICULTURAL_PRESETS } from '../../types/common';

// Fix Leaflet's default icon path issues in bundlers
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

interface FarmMapSelectorProps {
  onAnalyzeLocation?: () => void;
  heightClass?: string;
}

export const FarmMapSelector: React.FC<FarmMapSelectorProps> = ({
  onAnalyzeLocation,
  heightClass = 'h-[440px]',
}) => {
  const { location, setLocation, applyPreset, fetchEnvironmentalData } = useFarm();

  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);
  const circleRef = useRef<L.Circle | null>(null);

  const [inputLat, setInputLat] = useState(location.latitude.toFixed(4));
  const [inputLon, setInputLon] = useState(location.longitude.toFixed(4));
  const [prevLocation, setPrevLocation] = useState(location);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [geoLocating, setGeoLocating] = useState(false);

  // Sync inputs when location changes externally (e.g. preset change)
  if (prevLocation.latitude !== location.latitude || prevLocation.longitude !== location.longitude) {
    setPrevLocation(location);
    setInputLat(location.latitude.toFixed(4));
    setInputLon(location.longitude.toFixed(4));
    setValidationError(null);
  }

  // Update map view and markers when location changes
  useEffect(() => {
    if (mapInstanceRef.current) {
      const latLng: L.LatLngExpression = [location.latitude, location.longitude];
      mapInstanceRef.current.setView(latLng, 12);
      if (markerRef.current) {
        markerRef.current.setLatLng(latLng);
      }
      if (circleRef.current) {
        circleRef.current.setLatLng(latLng);
      }
    }
  }, [location.latitude, location.longitude]);

  // Keep stable refs for mount-only map initialization
  const locationRef = useRef(location);
  const setLocationRef = useRef(setLocation);

  useEffect(() => {
    locationRef.current = location;
    setLocationRef.current = setLocation;
  }, [location, setLocation]);

  // Initialize Leaflet Map once on mount
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const initialLatLng: L.LatLngExpression = [locationRef.current.latitude, locationRef.current.longitude];

    const map = L.map(mapContainerRef.current, {
      center: initialLatLng,
      zoom: 12,
      zoomControl: true,
      attributionControl: true,
    });

    // High quality OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    // Initial marker
    const marker = L.marker(initialLatLng, { draggable: true }).addTo(map);
    marker.bindPopup(`<b>Farm Location</b><br/>${initialLatLng[0]}°N, ${initialLatLng[1]}°E`).openPopup();

    // 500m analysis buffer circle
    const circle = L.circle(initialLatLng, {
      radius: 500,
      color: '#059669',
      fillColor: '#10b981',
      fillOpacity: 0.15,
      weight: 2,
      dashArray: '4, 4',
    }).addTo(map);

    markerRef.current = marker;
    circleRef.current = circle;
    mapInstanceRef.current = map;

    // Handle marker drag
    marker.on('dragend', () => {
      const pos = marker.getLatLng();
      const newLat = Number(pos.lat.toFixed(4));
      const newLon = Number(pos.lng.toFixed(4));
      setLocationRef.current({
        latitude: newLat,
        longitude: newLon,
        name: 'Selected Pin Location',
      });
      circle.setLatLng(pos);
    });

    // Handle map click
    map.on('click', (e: L.LeafletMouseEvent) => {
      const newLat = Number(e.latlng.lat.toFixed(4));
      const newLon = Number(e.latlng.lng.toFixed(4));
      setLocationRef.current({
        latitude: newLat,
        longitude: newLon,
        name: 'Map Selected Coordinate',
      });
      marker.setLatLng(e.latlng);
      circle.setLatLng(e.latlng);
      marker.bindPopup(`<b>Selected Coordinate</b><br/>${newLat}°N, ${newLon}°E`).openPopup();
    });

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  const handleManualCoordinateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const lat = parseFloat(inputLat);
    const lon = parseFloat(inputLon);

    if (isNaN(lat) || lat < -90 || lat > 90) {
      setValidationError('Latitude must be a valid number between -90.0 and 90.0 degrees.');
      return;
    }
    if (isNaN(lon) || lon < -180 || lon > 180) {
      setValidationError('Longitude must be a valid number between -180.0 and 180.0 degrees.');
      return;
    }

    setValidationError(null);
    const roundedLat = Number(lat.toFixed(4));
    const roundedLon = Number(lon.toFixed(4));
    setLocation({
      latitude: roundedLat,
      longitude: roundedLon,
      name: 'Custom Coordinates',
    });
  };

  const handleExplicitGeolocation = () => {
    if (!navigator.geolocation) {
      setValidationError('Geolocation is not supported by your browser.');
      return;
    }
    setGeoLocating(true);
    setValidationError(null);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGeoLocating(false);
        const lat = Number(pos.coords.latitude.toFixed(4));
        const lon = Number(pos.coords.longitude.toFixed(4));
        setLocation({
          latitude: lat,
          longitude: lon,
          name: 'Device Current Location',
        });
      },
      (err) => {
        setGeoLocating(false);
        setValidationError(`Location access denied or unavailable (${err.message}). Please use map pin or manual entry.`);
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden">
      {/* Map Control Bar */}
      <div className="p-4 sm:p-5 border-b border-slate-200/90 bg-slate-50/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <MapPin className="w-4 h-4 text-emerald-600" />
            <span>Interactive Farm Location Selector</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Click map, drag marker, or enter WGS84 coordinates. Green boundary indicates 500m analysis buffer.
          </p>
        </div>

        {/* Region Presets Dropdown */}
        <div className="flex items-center gap-2">
          <label htmlFor="farm-preset-select" className="text-xs font-semibold text-slate-600 flex items-center gap-1">
            <Compass className="w-3.5 h-3.5 text-slate-400" />
            <span>Presets:</span>
          </label>
          <select
            id="farm-preset-select"
            aria-label="Select Farm Region Preset"
            onChange={(e) => {
              const idx = Number(e.target.value);
              if (!isNaN(idx)) applyPreset(idx);
            }}
            value={AGRICULTURAL_PRESETS.findIndex(
              (p) => Math.abs(p.latitude - location.latitude) < 0.001
            )}
            className="text-xs font-medium bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 hover:border-slate-300 focus:outline-hidden focus:ring-1 focus:ring-emerald-500 cursor-pointer shadow-2xs"
          >
            {AGRICULTURAL_PRESETS.map((p, i) => (
              <option key={p.name} value={i}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Interactive Leaflet Map Canvas */}
      <div className={`relative w-full ${heightClass}`}>
        <div ref={mapContainerRef} className="w-full h-full" />

        {/* Floating Explicit GPS Button */}
        <div className="absolute top-4 right-4 z-1000">
          <button
            type="button"
            onClick={handleExplicitGeolocation}
            disabled={geoLocating}
            title="Use device location (explicit action)"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/95 backdrop-blur-xs text-slate-700 hover:text-emerald-700 border border-slate-200/90 text-xs font-semibold shadow-md hover:bg-slate-50 transition-all disabled:opacity-50 cursor-pointer"
          >
            <Navigation className={`w-3.5 h-3.5 ${geoLocating ? 'animate-spin text-emerald-600' : 'text-slate-600'}`} />
            <span>{geoLocating ? 'Locating...' : 'My Location'}</span>
          </button>
        </div>
      </div>

      {/* Manual Coordinate Form and Action */}
      <div className="p-4 sm:p-5 bg-white border-t border-slate-200/90">
        <form onSubmit={handleManualCoordinateSubmit} className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <label htmlFor="map-latitude-input" className="text-xs font-bold text-slate-600 uppercase tracking-wider">Lat:</label>
              <input
                id="map-latitude-input"
                type="number"
                step="0.0001"
                min="-90"
                max="90"
                value={inputLat}
                onChange={(e) => setInputLat(e.target.value)}
                placeholder="16.2160"
                className="w-28 text-xs font-mono px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <label htmlFor="map-longitude-input" className="text-xs font-bold text-slate-600 uppercase tracking-wider">Lon:</label>
              <input
                id="map-longitude-input"
                type="number"
                step="0.0001"
                min="-180"
                max="180"
                value={inputLon}
                onChange={(e) => setInputLon(e.target.value)}
                placeholder="77.3300"
                className="w-28 text-xs font-mono px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
              />
            </div>
            <button
              type="submit"
              className="px-3.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold transition-colors cursor-pointer"
            >
              Update Pin
            </button>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => {
                fetchEnvironmentalData();
                if (onAnalyzeLocation) onAnalyzeLocation();
              }}
              className="w-full sm:w-auto px-5 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold tracking-wide transition-all shadow-sm hover:shadow cursor-pointer flex items-center justify-center gap-2"
            >
              <Compass className="w-4 h-4" />
              <span>Scout Environmental Data for Pin</span>
            </button>
          </div>
        </form>

        {validationError && (
          <div className="mt-3 flex items-center gap-2 text-xs font-medium text-rose-700 bg-rose-50 border border-rose-200/80 p-2.5 rounded-lg">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{validationError}</span>
          </div>
        )}

        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
          <span>Analysis Method: WGS84 point-centered 500m radial buffer</span>
          <span className="hidden sm:inline">Notice: Does not represent surveyed farm legal boundaries</span>
        </div>
      </div>
    </div>
  );
};
