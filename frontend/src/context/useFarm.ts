import { useContext } from 'react';
import { FarmContext } from './FarmContextBase';
import type { FarmContextType } from './FarmContextBase';

export function useFarm(): FarmContextType {
  const context = useContext(FarmContext);
  if (!context) {
    throw new Error('useFarm must be used within a FarmProvider');
  }
  return context;
}
