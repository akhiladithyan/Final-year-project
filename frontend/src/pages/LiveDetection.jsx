import React, { useState, useRef } from 'react';
import {
  Play,
  Pause,
  Square,
  Maximize2,
  Camera,
  Users,
  ShieldAlert,
  Link as LinkIcon,
  Activity,
  AlertCircle,
  Eye
} from 'lucide-react';
import { api } from '../services/api';

export function LiveDetection({ telemetry, alerts }) {
  const [isPaused, setIsPaused] = useState(false);
  const [videoRunning, setVideoRunning] = useState(true);
  const videoContainerRef = useRef(null);

  const handlePause = async () => {
    try {
      if (isPaused) {
        await api.resumeVideo();
        setIsPaused(false);
      } else {
        await api.pauseVideo();
        setIsPaused(true);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleStop = async () => {
    try {
      await api.stopVideo();
      setVideoRunning(false);
    } catch (e) {
      console.error(e);
    }
  };

  const handleFullscreen = () => {
    if (videoContainerRef.current) {
      if (!document.fullscreenElement) {
        videoContainerRef.current.requestFullscreen().catch(err => {
          alert(`Error attempting to enable full-screen mode: ${err.message}`);
        });
      } else {
        document.exitFullscreen();
      }
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
      {/* Main Video Screen Area (3 Cols) */}
      <div className="lg:col-span-3 flex flex-col space-y-3">
        {/* Video Viewport Container */}
        <div
          ref={videoContainerRef}
          className="relative flex-1 min-h-[460px] bg-black rounded-xl border border-slate-800 overflow-hidden flex items-center justify-center shadow-2xl group"
        >
          {/* MJPEG Feed Image */}
          <img
            src="/api/video/feed"
            alt="AI Surveillance Stream"
            className="w-full h-full object-contain"
            onError={(e) => {
              // Fallback placeholder when stream is stopped or idle
              e.target.style.display = 'none';
            }}
            onLoad={(e) => {
              e.target.style.display = 'block';
            }}
          />

          {/* Active Overlay Watermark */}
          <div className="absolute top-4 left-4 flex items-center space-x-2 px-3 py-1 bg-slate-900/80 backdrop-blur rounded border border-slate-700/60 text-xs">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
            <span className="font-mono font-semibold tracking-wider text-slate-200">LIVE FEED</span>
            <span className="text-slate-500">|</span>
            <span className="font-mono text-emerald-400">{telemetry.fps?.toFixed(1) || '0.0'} FPS</span>
          </div>

          {/* Top Right Device Badge */}
          <div className="absolute top-4 right-4 flex items-center space-x-2 px-3 py-1 bg-slate-900/80 backdrop-blur rounded border border-slate-700/60 text-xs">
            <span className="text-slate-400">Inference:</span>
            <span className="font-mono font-bold text-blue-400 uppercase">{telemetry.device || 'CPU'}</span>
          </div>

          {/* Bottom Floating Bar on Hover */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-2 bg-slate-900/90 backdrop-blur rounded-xl border border-slate-700 flex items-center space-x-3 opacity-90 hover:opacity-100 transition shadow-lg">
            <button
              onClick={handlePause}
              className="p-2 hover:bg-slate-800 rounded-lg text-slate-300 hover:text-white transition"
              title={isPaused ? 'Resume Stream' : 'Pause Stream'}
            >
              {isPaused ? <Play className="w-4 h-4 text-emerald-400" /> : <Pause className="w-4 h-4 text-amber-400" />}
            </button>

            <button
              onClick={handleStop}
              className="p-2 hover:bg-slate-800 rounded-lg text-slate-300 hover:text-rose-400 transition"
              title="Stop Pipeline"
            >
              <Square className="w-4 h-4" />
            </button>

            <div className="h-4 w-[1px] bg-slate-700" />

            <button
              onClick={handleFullscreen}
              className="p-2 hover:bg-slate-800 rounded-lg text-slate-300 hover:text-blue-400 transition"
              title="Toggle Fullscreen"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Informational Guidance Alert Banner */}
        <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <Eye className="w-4 h-4 text-blue-400" />
            <span>
              HUD renders bounding boxes, tracking identity numbers, upper-body pose skeletons, and review badges in real time.
            </span>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">
            Frame #{telemetry.frame_number || 0}
          </span>
        </div>
      </div>

      {/* Right Side Telemetry & Detections Panel (1 Col) */}
      <div className="space-y-4 flex flex-col h-full overflow-y-auto">
        {/* Active Persons Box */}
        <div className="p-4 rounded-xl bg-[#0f1420] border border-slate-800 space-y-3 shrink-0">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-1.5">
              <Users className="w-4 h-4 text-blue-400" />
              <span>Tracked Individuals ({telemetry.humans?.length || 0})</span>
            </h3>
          </div>

          {(!telemetry.humans || telemetry.humans.length === 0) ? (
            <p className="text-xs text-slate-500 italic py-2">No humans detected in frame</p>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {telemetry.humans.map((h, i) => (
                <div
                  key={i}
                  className="p-2 rounded-lg bg-slate-900/80 border border-slate-800 text-xs flex items-center justify-between"
                >
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-bold text-blue-400">ID #{h.tracker_id}</span>
                      <span className="text-[10px] text-slate-400">({(h.confidence * 100).toFixed(1)}%)</span>
                    </div>
                    {h.association_status && h.association_status !== 'NONE' && (
                      <div className="mt-1 flex items-center space-x-1">
                        <span
                          className={`px-1 py-0.5 rounded text-[9px] font-bold ${
                            h.association_status === 'PROBABLE'
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                              : 'bg-orange-500/20 text-orange-300 border border-orange-500/30'
                          }`}
                        >
                          {h.association_status}: {h.associated_weapon || 'WEAPON'}
                        </span>
                      </div>
                    )}
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">
                    vel: {h.velocity?.toFixed(1) || '0'} px/f
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Weapons Flagged Box */}
        <div className="p-4 rounded-xl bg-[#0f1420] border border-slate-800 space-y-3 shrink-0">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-1.5">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <span>Weapons Flagged ({telemetry.weapons?.length || 0})</span>
            </h3>
          </div>

          {(!telemetry.weapons || telemetry.weapons.length === 0) ? (
            <div className="text-xs text-slate-500 italic py-2 space-y-1">
              <p>No weapons flagged in current frame.</p>
              <p className="text-[10px] text-slate-600">Model strictly gates unverified objects.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {telemetry.weapons.map((w, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg bg-rose-950/20 border border-rose-800/40 text-xs flex items-center justify-between"
                >
                  <div>
                    <span className="font-bold text-rose-300 uppercase">{w.class_name}</span>
                    <p className="text-[10px] text-rose-400/80">Human Review Required</p>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono text-[11px] font-bold">
                    {(w.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Live Alerts Stream */}
        <div className="p-4 rounded-xl bg-[#0f1420] border border-slate-800 space-y-3 flex-1 flex flex-col min-h-0">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-1.5">
              <Activity className="w-4 h-4 text-amber-400" />
              <span>Live Alert Stream</span>
            </h3>
            <span className="text-[10px] text-slate-500">{alerts?.length || 0} events</span>
          </div>

          <div className="space-y-2 flex-1 overflow-y-auto pr-1">
            {(!alerts || alerts.length === 0) ? (
              <p className="text-xs text-slate-500 italic py-2">No alerts triggered yet</p>
            ) : (
              alerts.slice(0, 10).map((a, i) => (
                <div
                  key={i}
                  className="p-2 rounded-lg bg-slate-900/80 border border-slate-800/90 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                        a.severity === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : a.severity === 'WARNING'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      }`}
                    >
                      {a.alert_type}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {new Date(a.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 leading-snug">{a.message}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
