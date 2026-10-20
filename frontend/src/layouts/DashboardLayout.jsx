import React from 'react';
import {
  LayoutDashboard,
  Video,
  Users,
  ShieldAlert,
  Activity,
  History,
  Cpu,
  Database,
  Settings,
  Wifi,
  WifiOff,
  Crosshair,
  AlertTriangle
} from 'lucide-react';

const navItems = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'live', label: 'Live Detection', icon: Video },
  { id: 'tracking', label: 'Human Tracking', icon: Users },
  { id: 'weapons', label: 'Weapon Detection', icon: ShieldAlert },
  { id: 'pose', label: 'Pose Tracking', icon: Activity },
  { id: 'history', label: 'Detection History', icon: History },
  { id: 'models', label: 'Model Management', icon: Cpu },
  { id: 'training', label: 'Dataset & Training', icon: Database },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export function DashboardLayout({
  activeTab,
  setActiveTab,
  isConnected,
  fps = 0,
  device = 'CPU',
  activeTracksCount = 0,
  weaponsCount = 0,
  children
}) {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0a0d14] text-slate-200">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800/80 bg-[#0e131f] flex flex-col justify-between shrink-0">
        <div>
          {/* Logo / Header */}
          <div className="p-4 border-b border-slate-800/80 flex items-center space-x-3">
            <div className="p-2 bg-blue-600/20 border border-blue-500/40 rounded-lg text-blue-400">
              <Crosshair className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-wider text-slate-100 uppercase">
                Aegis-Vision AI
              </h1>
              <p className="text-[10px] text-slate-400 tracking-tight">
                Armed Tracking & Pose HUD
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-2 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-blue-600/15 border border-blue-500/30 text-blue-400 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-slate-500'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* System Notice Footer */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-900/50">
          <div className="flex items-center space-x-2 text-[11px] text-amber-400/90 mb-1">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
            <span className="font-semibold uppercase tracking-wider">Passive CV System</span>
          </div>
          <p className="text-[10px] text-slate-500 leading-tight">
            Situational awareness & human review only. No physical response automation.
          </p>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Command Bar */}
        <header className="h-14 border-b border-slate-800/80 bg-[#0e131f]/90 backdrop-blur px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-4">
            <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
              {navItems.find((i) => i.id === activeTab)?.label}
            </span>
            <div className="h-3 w-[1px] bg-slate-700" />
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-400">Tracked Humans:</span>
              <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-mono text-[11px] font-semibold border border-blue-500/30">
                {activeTracksCount}
              </span>
            </div>
            {weaponsCount > 0 && (
              <div className="flex items-center space-x-2 text-xs">
                <span className="text-amber-400 font-semibold animate-pulse">Weapons Flagged:</span>
                <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[11px] font-bold border border-amber-500/40">
                  {weaponsCount}
                </span>
              </div>
            )}
          </div>

          {/* Right Status Badges */}
          <div className="flex items-center space-x-4">
            {/* FPS Badge */}
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-800/80 border border-slate-700/60 text-[11px] font-mono">
              <span className="text-slate-400">FPS:</span>
              <span className="text-emerald-400 font-semibold">{fps.toFixed(1)}</span>
            </div>

            {/* Hardware Device */}
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-800/80 border border-slate-700/60 text-[11px]">
              <Cpu className="w-3.5 h-3.5 text-blue-400" />
              <span className="text-slate-300 font-mono uppercase font-semibold">{device}</span>
            </div>

            {/* WebSocket Connection Status */}
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-800/80 border border-slate-700/60 text-[11px]">
              {isConnected ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-emerald-400 font-medium">WS Live</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-rose-500" />
                  <span className="text-rose-400 font-medium">WS Offline</span>
                </>
              )}
            </div>
          </div>
        </header>

        {/* Viewport Container */}
        <main className="flex-1 overflow-y-auto p-6 bg-[#0a0d14]">
          {children}
        </main>
      </div>
    </div>
  );
}
