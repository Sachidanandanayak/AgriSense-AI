import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { FarmProvider } from './context/FarmContext';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { FarmMapPage } from './pages/FarmMapPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { AdvisoryPage } from './pages/AdvisoryPage';
import { MethodologyPage } from './pages/MethodologyPage';
import { SettingsPage } from './pages/SettingsPage';

export function App() {
  return (
    <FarmProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="map" element={<FarmMapPage />} />
            <Route path="recommendations" element={<RecommendationsPage />} />
            <Route path="advisory" element={<AdvisoryPage />} />
            <Route path="methodology" element={<MethodologyPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </FarmProvider>
  );
}

export default App;
