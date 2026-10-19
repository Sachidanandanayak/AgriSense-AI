/**
 * Common frontend state and location interfaces
 */

export interface FarmLocation {
  latitude: number;
  longitude: number;
  name?: string;
  region?: string;
}

export interface LocationPreset {
  name: string;
  region: string;
  latitude: number;
  longitude: number;
  description: string;
  defaultInputs?: {
    nitrogen: number;
    phosphorus: number;
    potassium: number;
    temperature: number;
    humidity: number;
    ph: number;
    rainfall: number;
  };
}

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/**
 * Verified Indian agricultural region presets for rapid farmer/demo evaluation.
 * Note: Preset coordinates point to established agricultural university and research
 * experimental stations (sample locations) to guarantee non-null digital soil mappings,
 * distinct from arbitrary farm coordinates.
 */
export const AGRICULTURAL_PRESETS: LocationPreset[] = [
  {
    name: 'Raichur — UAS MARS Research Station (Sample Location)',
    region: 'Karnataka, India',
    latitude: 16.2160,
    longitude: 77.3300,
    description: 'Sample agricultural research location: University of Agricultural Sciences (UAS) Main Agricultural Research Station (MARS), Raichur. Deccan Plateau Semi-Arid Zone: Black cotton soil, suited for cotton, rice, and pulses.',
    defaultInputs: {
      nitrogen: 80.0,
      phosphorus: 40.0,
      potassium: 40.0,
      temperature: 26.5,
      humidity: 65.0,
      ph: 6.8,
      rainfall: 120.0,
    },
  },
  {
    name: 'Ludhiana — PAU Experimental Farm (Sample Location)',
    region: 'Punjab, India',
    latitude: 30.9020,
    longitude: 75.7950,
    description: 'Sample agricultural research location: Punjab Agricultural University (PAU) Experimental Farm (West Agronomy Station), Ludhiana. Indo-Gangetic Alluvial Plain: Highly fertile loam, irrigated wheat, rice, and maize.',
    defaultInputs: {
      nitrogen: 120.0,
      phosphorus: 60.0,
      potassium: 50.0,
      temperature: 24.0,
      humidity: 55.0,
      ph: 7.2,
      rainfall: 180.0,
    },
  },
  {
    name: 'Nashik — Niphad Agricultural Station (Sample Location)',
    region: 'Maharashtra, India',
    latitude: 20.0800,
    longitude: 74.0500,
    description: 'Sample agricultural research location: Niphad Agricultural Research Station / Niphad Horticulture Belt, Nashik. Western Ghats Leeward Zone: Well-drained medium loams, grapes, pomegranate, and onions.',
    defaultInputs: {
      nitrogen: 70.0,
      phosphorus: 55.0,
      potassium: 60.0,
      temperature: 25.5,
      humidity: 60.0,
      ph: 6.9,
      rainfall: 140.0,
    },
  },
  {
    name: 'Guntur — Lam RARS Research Station (Sample Location)',
    region: 'Andhra Pradesh, India',
    latitude: 16.4150,
    longitude: 80.4420,
    description: 'Sample agricultural research location: Regional Agricultural Research Station (RARS) Lam, ANGRAU, Guntur. Krishna Delta Agro-Ecological Zone: Deep clay loam, paddy, cotton, and chillies.',
    defaultInputs: {
      nitrogen: 90.0,
      phosphorus: 45.0,
      potassium: 45.0,
      temperature: 28.5,
      humidity: 70.0,
      ph: 7.4,
      rainfall: 210.0,
    },
  },
];
