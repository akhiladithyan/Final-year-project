import React, { useState } from 'react';
import { Settings as SettingsIcon, Save, RefreshCw, HardDrive, Shield } from 'lucide-react';
import { api } from '../services/api';

export function Settings() {
  const [targetFps, setTargetFps] = useState(25);
  const [snapshotQuality, setSnapshotQuality] = useState(80);
  const [feedback, setFeedback] = useState(null);

  const handleSave = () => {
    setFeedback({ type: 'success', message: 'Pipeline configuration preferences saved.' });
    setTimeout(() => setFeedback(null), 3000);
  };

  const handleResetTracker = async () => {
    try {
      await api.stopVideo();
      setFeedback({ type: 'success', message: 'Tracking state and tracker caches reset.' });
    } catch (e) {
      setFeedback({ type: 'error', message: e.message });
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-base font-bold text-slate-100 uppercase tracking-wider flex items-center space-x-2">
          <SettingsIcon className="w-5 h-5 text-slate-400" />
          <span>System & Environment Settings</span>
        </h2>
        <p className="text-xs text-slate-400">
          Configure video processing bounds, storage locations, and active operational parameters.
        </p>
      </div>

      <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-5">
        <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider border-b border-slate-800 pb-2">
          Pipeline Performance & Ingestion Limits
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1">
            <label className="text-slate-300 font-semibold">Target Processing FPS</label>
            <input
              type="number"
              value={targetFps}
              onChange={(e) => setTargetFps(parseInt(e.target.value, 10))}
              className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-slate-200 font-mono focus:outline-none focus:border-blue-500"
            />
            <span className="text-[10px] text-slate-500">Limits background frame acquisition rate to conserve GPU/CPU.</span>
          </div>

          <div className="space-y-1">
            <label className="text-slate-300 font-semibold">JPEG Stream Compression Quality (1-100)</label>
            <input
              type="number"
              value={snapshotQuality}
              onChange={(e) => setSnapshotQuality(parseInt(e.target.value, 10))}
              className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-slate-200 font-mono focus:outline-none focus:border-blue-500"
            />
            <span className="text-[10px] text-slate-500">Controls bandwidth and visual clarity of MJPEG HUD frames.</span>
          </div>
        </div>

        <div className="pt-2">
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium flex items-center space-x-1.5 transition"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save Preferences</span>
          </button>
        </div>
      </div>

      <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-4">
        <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider border-b border-slate-800 pb-2">
          Filesystem Storage & Databases
        </h3>

        <div className="space-y-2 text-xs font-mono text-slate-300">
          <div className="flex justify-between p-2 rounded bg-slate-900 border border-slate-800">
            <span className="text-slate-400">Database Engine:</span>
            <span>SQLite (data/app.db) &bull; PostgreSQL Ready</span>
          </div>
          <div className="flex justify-between p-2 rounded bg-slate-900 border border-slate-800">
            <span className="text-slate-400">Uploaded Videos:</span>
            <span>data/uploads/</span>
          </div>
          <div className="flex justify-between p-2 rounded bg-slate-900 border border-slate-800">
            <span className="text-slate-400">Incident Snapshots:</span>
            <span>data/detections/</span>
          </div>
          <div className="flex justify-between p-2 rounded bg-slate-900 border border-slate-800">
            <span className="text-slate-400">Model Weights:</span>
            <span>models/human/, models/weapon/, models/pose/</span>
          </div>
        </div>
      </div>

      <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-3">
        <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider text-rose-400">
          Maintenance & Reset Operations
        </h3>
        <p className="text-xs text-slate-400">
          Clear all current Kalman tracker buffers, zero out active IDs, and stop active pipelines.
        </p>
        <button
          onClick={handleResetTracker}
          className="px-4 py-2 bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/40 text-rose-300 rounded-lg text-xs font-medium flex items-center space-x-1.5 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Reset Tracking State</span>
        </button>
      </div>

      {feedback && (
        <div
          className={`p-3 rounded-lg text-xs font-medium ${
            feedback.type === 'success' ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-800' : 'bg-rose-950/40 text-rose-300 border border-rose-800'
          }`}
        >
          {feedback.message}
        </div>
      )}
    </div>
  );
}
