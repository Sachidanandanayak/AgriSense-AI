import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Sprout,
  LayoutDashboard,
  MapPin,
  Sparkles,
  ClipboardCheck,
  BookOpenCheck,
  Settings,
  Activity,
  Layers,
} from 'lucide-react';
import { useFarm } from '../../context/useFarm';

interface SidebarProps {
  onNavigate?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onNavigate }) => {
  const { backendOnline } = useFarm();

  const navItems = [
    {
      to: '/',
      label: 'Dashboard',
      icon: LayoutDashboard,
      description: 'Executive overview & metrics',
    },
    {
      to: '/map',
      label: 'Farm Map & Scouting',
      icon: MapPin,
      description: 'Interactive geospatial selection',
    },
    {
      to: '/recommendations',
      label: 'Crop Recommendations',
      icon: Sparkles,
      description: 'ML candidate ranking',
    },
    {
      to: '/advisory',
      label: 'Farm Advisory',
      icon: ClipboardCheck,
      description: 'FAO ECOCROP evidence',
    },
    {
      to: '/methodology',
      label: 'Sources & Methodology',
      icon: BookOpenCheck,
      description: 'FAO & Earth Engine proof',
    },
    {
      to: '/settings',
      label: 'API & Settings',
      icon: Settings,
      description: 'Connection & backend health',
    },
  ];

  return (
    <aside className="w-64 h-full bg-slate-900 text-slate-100 flex flex-col border-r border-slate-800 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-emerald-600 text-white shadow-md shadow-emerald-900/30">
            <Sprout className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-1.5">
              AgriSense AI
            </h1>
            <p className="text-[11px] font-medium text-emerald-400">Precision Agriculture</p>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <div className="px-3 py-2 text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
          Core Engine
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-emerald-600/90 text-white shadow-xs font-semibold'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <div className="flex-1 truncate">
                <div>{item.label}</div>
              </div>
            </NavLink>
          );
        })}
      </nav>

      {/* Backend Status Footer */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/40">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5" />
            Backend API
          </span>
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
              backendOnline
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : backendOnline === false
                ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                : 'bg-slate-700/40 text-slate-400'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                backendOnline ? 'bg-emerald-400 animate-pulse' : backendOnline === false ? 'bg-rose-400' : 'bg-slate-400'
              }`}
            />
            {backendOnline ? 'Connected' : backendOnline === false ? 'Offline' : 'Checking'}
          </span>
        </div>
        <div className="flex items-center justify-between text-[11px] text-slate-500">
          <span className="flex items-center gap-1">
            <Layers className="w-3 h-3" />
            Phases 1–10
          </span>
          <span className="font-mono text-[10px]">v0.1.0</span>
        </div>
      </div>
    </aside>
  );
};
