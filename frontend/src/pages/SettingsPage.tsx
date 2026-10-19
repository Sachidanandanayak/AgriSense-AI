import React, { useState } from 'react';
import { Settings, Server, RefreshCw, CheckCircle2, XCircle, Globe, Terminal } from 'lucide-react';
import { getApiBaseUrl, setApiBaseUrl } from '../api/client';
import { checkBackendHealth } from '../api/health';
import { useFarm } from '../context/useFarm';

export const SettingsPage: React.FC = () => {
  const { backendOnline, refreshBackendHealth } = useFarm();
  const [urlInput, setUrlInput] = useState(getApiBaseUrl());
  const [testResult, setTestResult] = useState<{
    testing: boolean;
    success?: boolean;
    message?: string;
    latencyMs?: number;
  }>({ testing: false });

  const handleSaveUrl = (e: React.FormEvent) => {
    e.preventDefault();
    setApiBaseUrl(urlInput);
    refreshBackendHealth();
  };

  const handleResetDefault = () => {
    const defaultUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
    setUrlInput(defaultUrl);
    setApiBaseUrl(null);
    refreshBackendHealth();
  };

  const handleRunHealthCheck = async () => {
    setTestResult({ testing: true });
    const startTime = performance.now();
    try {
      const res = await checkBackendHealth();
      const latency = Math.round(performance.now() - startTime);
      setTestResult({
        testing: false,
        success: res.healthy,
        message: res.healthy
          ? `Backend is healthy and responsive (Status: "${res.statusText}").`
          : `Health check failed: ${res.statusText}`,
        latencyMs: latency,
      });
      refreshBackendHealth();
    } catch (err) {
      const latency = Math.round(performance.now() - startTime);
      setTestResult({
        testing: false,
        success: false,
        message: err instanceof Error ? err.message : 'Connection failed',
        latencyMs: latency,
      });
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
          <Settings className="w-5 h-5 text-emerald-600" />
          <span>System Settings & API Configuration</span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Manage backend API endpoints, verify network connectivity, and review active system components.
        </p>
      </div>

      {/* Backend API Configuration */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-slate-100 text-slate-700">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">FastAPI Backend Connection</h2>
              <p className="text-xs text-slate-500">Configurable backend service URL</p>
            </div>
          </div>

          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
              backendOnline
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-rose-50 text-rose-700 border border-rose-200'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                backendOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
              }`}
            />
            {backendOnline ? 'Online / Healthy' : 'Offline / Unreachable'}
          </span>
        </div>

        <form onSubmit={handleSaveUrl} className="space-y-3">
          <label htmlFor="api-base-url-input" className="block text-xs font-semibold text-slate-700">
            Backend API Base URL (default: http://127.0.0.1:8000)
          </label>
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              id="api-base-url-input"
              type="url"
              required
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="http://127.0.0.1:8000"
              className="flex-1 text-xs font-mono px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
            />
            <div className="flex gap-2">
              <button
                type="submit"
                className="px-4 py-2 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold transition-colors cursor-pointer shadow-xs"
              >
                Save URL
              </button>
              <button
                type="button"
                onClick={handleResetDefault}
                className="px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium transition-colors cursor-pointer"
              >
                Reset Default
              </button>
            </div>
          </div>
          <p className="text-[11px] text-slate-500">
            Overrides are saved locally in browser storage. Defaults to <code>VITE_API_BASE_URL</code>.
          </p>
        </form>

        {/* Live Diagnostics */}
        <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <button
            type="button"
            onClick={handleRunHealthCheck}
            disabled={testResult.testing}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold transition-all shadow-xs cursor-pointer disabled:opacity-50 self-start sm:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${testResult.testing ? 'animate-spin' : ''}`} />
            <span>{testResult.testing ? 'Pinging /health...' : 'Test Backend Health Ping'}</span>
          </button>

          {testResult.message && (
            <div
              className={`flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-lg border ${
                testResult.success
                  ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
                  : 'bg-rose-50 text-rose-900 border-rose-200'
              }`}
            >
              {testResult.success ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
              )}
              <span>
                {testResult.message}{' '}
                {testResult.latencyMs !== undefined && (
                  <span className="font-mono text-[11px] opacity-75">
                    ({testResult.latencyMs}ms)
                  </span>
                )}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Backend Command Cheatsheet */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs space-y-3">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
          <Terminal className="w-4 h-4 text-slate-600" />
          <span>Local Development Commands</span>
        </h3>
        <div className="space-y-2 text-xs">
          <div className="p-3 rounded-xl bg-slate-900 text-slate-200 font-mono text-[11px] space-y-1">
            <p className="text-slate-400"># Start FastAPI backend (from backend/ directory):</p>
            <p className="text-emerald-400">.venv\Scripts\uvicorn app.main:app --reload --port 8000</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-900 text-slate-200 font-mono text-[11px] space-y-1">
            <p className="text-slate-400"># Start Vite frontend (from frontend/ directory):</p>
            <p className="text-emerald-400">npm run dev</p>
          </div>
        </div>
      </div>

      {/* System Technical Stack Info */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs space-y-3">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
          <Globe className="w-4 h-4 text-emerald-600" />
          <span>Platform Information & Stack Specifications</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-[10px] text-slate-500 uppercase block font-semibold">Backend</span>
            <span className="font-bold text-slate-900">FastAPI & Python 3.10</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-[10px] text-slate-500 uppercase block font-semibold">ML Framework</span>
            <span className="font-bold text-slate-900">Scikit-learn 1.5+</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-[10px] text-slate-500 uppercase block font-semibold">Frontend</span>
            <span className="font-bold text-slate-900">React 19 & TypeScript</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-[10px] text-slate-500 uppercase block font-semibold">Styling & Map</span>
            <span className="font-bold text-slate-900">Tailwind CSS & Leaflet</span>
          </div>
        </div>
      </div>
    </div>
  );
};
