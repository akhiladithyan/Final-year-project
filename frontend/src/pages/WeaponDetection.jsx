import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  Sliders,
  CheckCircle2,
  Cpu,
  FileCheck,
  Info
} from 'lucide-react';
import { api } from '../services/api';

export function WeaponDetection({ telemetry }) {
  const [modelStatus, setModelStatus] = useState(null);
  const [weaponConf, setWeaponConf] = useState(0.50);
  const [customWeightsPath, setCustomWeightsPath] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const fetchModel = async () => {
    try {
      const res = await api.getModelStatus();
      setModelStatus(res);
      if (res.models?.weapon_detection?.threshold) {
        setWeaponConf(res.models.weapon_detection.threshold);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchModel();
  }, []);

  const handleUpdateThreshold = async () => {
    setIsUpdating(true);
    setFeedback(null);
    try {
      await api.updateThresholds({ weapon_conf: parseFloat(weaponConf) });
      setFeedback({ type: 'success', message: `Confidence threshold updated to ${(weaponConf * 100).toFixed(0)}%` });
      await fetchModel();
    } catch (e) {
      setFeedback({ type: 'error', message: e.message });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleLoadWeights = async () => {
    if (!customWeightsPath) return;
    setIsUpdating(true);
    setFeedback(null);
    try {
      const res = await api.loadWeaponWeights(customWeightsPath);
      setFeedback({ type: 'success', message: res.message });
      await fetchModel();
    } catch (e) {
      setFeedback({ type: 'error', message: e.message || 'Failed to load weights' });
    } finally {
      setIsUpdating(false);
    }
  };

  const isAwaitingTraining = modelStatus?.models?.weapon_detection?.status === 'awaiting_training';

  return (
    <div className="space-y-6">
      {/* Safety Policy & Passive CV Architecture Notice */}
      <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/40 text-amber-300 text-xs flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 shrink-0 text-amber-400 mt-0.5" />
        <div className="space-y-1">
          <p className="font-bold uppercase tracking-wider text-amber-200">
            Passive Computer Vision System — Situational Awareness Only
          </p>
          <p className="text-slate-300 leading-relaxed">
            This module detects visible visual patterns corresponding to weapons for operator review. It does not predict intent, establish ownership, or automate physical actions. Unverified or low-confidence detections remain unassigned to avoid false alarms.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Weapon Detection Engine Status & Configuration */}
        <div className="lg:col-span-2 space-y-6">
          {/* Status Box */}
          <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  <span>Module 2: Custom Weapon Detection Engine</span>
                </h3>
                <p className="text-xs text-slate-400">YOLO-based object detector specialized for weapon classes</p>
              </div>

              {isAwaitingTraining ? (
                <span className="px-3 py-1 rounded-full bg-amber-500/20 text-amber-400 text-xs font-bold border border-amber-500/30">
                  Awaiting Training
                </span>
              ) : (
                <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold border border-emerald-500/30">
                  Model Weights Active
                </span>
              )}
            </div>

            {isAwaitingTraining && (
              <div className="p-3.5 rounded-lg bg-slate-900/90 border border-slate-800 space-y-2 text-xs">
                <p className="text-slate-200 font-semibold flex items-center space-x-1.5">
                  <Info className="w-4 h-4 text-blue-400" />
                  <span>Training Dataset & Weights Workflow</span>
                </p>
                <p className="text-slate-400 leading-relaxed text-[11px]">
                  Custom weights are not yet trained or loaded. The system will not fabricate results. To train or load weights:
                  1. Visit the <strong>Dataset & Training</strong> tab.
                  2. Prepare annotated images for the 4 target classes.
                  3. Run the PyTorch training pipeline or load a pre-existing <code>best.pt</code> file.
                </p>
              </div>
            )}

            {/* Configured Classes */}
            <div>
              <label className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block mb-2">
                Configured Weapon Classes
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {['Handgun', 'Rifle', 'Shotgun', 'Knife'].map((cls, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-center"
                  >
                    <span className="text-xs font-bold text-slate-200 block">{cls}</span>
                    <span className="text-[9px] text-slate-500 font-mono">Class #{idx}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Confidence Threshold Slider */}
            <div className="p-4 rounded-lg bg-slate-900/70 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-200 flex items-center space-x-1.5">
                  <Sliders className="w-3.5 h-3.5 text-blue-400" />
                  <span>Confidence Threshold</span>
                </span>
                <span className="font-mono font-bold text-blue-400 text-sm">
                  {(weaponConf * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0.10"
                max="0.95"
                step="0.05"
                value={weaponConf}
                onChange={(e) => setWeaponConf(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <div className="flex justify-between text-[10px] text-slate-500">
                <span>10% (High Sensitivity)</span>
                <span>50% (Balanced)</span>
                <span>95% (High Precision)</span>
              </div>
              <button
                onClick={handleUpdateThreshold}
                disabled={isUpdating}
                className="py-1.5 px-4 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium transition"
              >
                Apply Threshold
              </button>
            </div>
          </div>

          {/* Load Custom Weights */}
          <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-3">
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <FileCheck className="w-4 h-4 text-emerald-400" />
              <span>Load Custom Trained Weights (.pt)</span>
            </h3>
            <div className="space-y-2">
              <input
                type="text"
                value={customWeightsPath}
                onChange={(e) => setCustomWeightsPath(e.target.value)}
                placeholder="models/weapon/best.pt"
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
              />
              <button
                onClick={handleLoadWeights}
                disabled={isUpdating || !customWeightsPath}
                className="py-1.5 px-4 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded text-xs font-medium transition"
              >
                Load Model Weights
              </button>
            </div>
            {feedback && (
              <p
                className={`text-xs ${
                  feedback.type === 'success' ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {feedback.message}
              </p>
            )}
          </div>
        </div>

        {/* Right 1 Col: Current Sighting Activity */}
        <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-4">
          <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-1.5">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <span>Instant Frame Sightings</span>
          </h3>

          {(!telemetry.weapons || telemetry.weapons.length === 0) ? (
            <p className="text-xs text-slate-500 italic py-6 text-center">
              No weapons detected in current frame.
            </p>
          ) : (
            <div className="space-y-3">
              {telemetry.weapons.map((w, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-rose-950/20 border border-rose-800/40 text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-rose-300 uppercase tracking-wide">
                      {w.class_name}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono font-bold text-[11px]">
                      {(w.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="font-mono text-[10px] text-slate-400">
                    BBox: [{w.bbox.join(', ')}]
                  </div>
                  <span className="inline-block text-[10px] text-amber-400 font-medium">
                    &bull; Flagged for Human Review
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
