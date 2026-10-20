import React, { useState, useEffect } from 'react';
import { Cpu, Sliders, CheckCircle2, HardDrive, ShieldCheck, Activity, Users } from 'lucide-react';
import { api } from '../services/api';

export function ModelManagement() {
  const [modelStatus, setModelStatus] = useState(null);
  const [availableWeights, setAvailableWeights] = useState([]);
  const [humanConf, setHumanConf] = useState(0.45);
  const [weaponConf, setWeaponConf] = useState(0.50);
  const [poseConf, setPoseConf] = useState(0.50);
  const [message, setMessage] = useState(null);

  const fetchData = async () => {
    try {
      const [mStat, wList] = await Promise.all([
        api.getModelStatus(),
        api.getAvailableWeights()
      ]);
      setModelStatus(mStat);
      setAvailableWeights(wList.weights || []);
      if (mStat.models) {
        if (mStat.models.human_detection?.threshold) setHumanConf(mStat.models.human_detection.threshold);
        if (mStat.models.weapon_detection?.threshold) setWeaponConf(mStat.models.weapon_detection.threshold);
        if (mStat.models.pose_estimation?.threshold) setPoseConf(mStat.models.pose_estimation.threshold);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleApplyThresholds = async () => {
    try {
      await api.updateThresholds({
        human_conf: parseFloat(humanConf),
        weapon_conf: parseFloat(weaponConf),
        pose_conf: parseFloat(poseConf)
      });
      setMessage({ type: 'success', text: 'Confidence thresholds updated across all AI modules.' });
      await fetchData();
    } catch (e) {
      setMessage({ type: 'error', text: e.message });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-base font-bold text-slate-100 uppercase tracking-wider flex items-center space-x-2">
          <Cpu className="w-5 h-5 text-blue-400" />
          <span>Model Management & Hardware Acceleration</span>
        </h2>
        <p className="text-xs text-slate-400">
          Inspect YOLO neural network weights, GPU VRAM allocation, and configure runtime confidence gating.
        </p>
      </div>

      {/* Hardware Device Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-[#0f1420] border border-slate-800 space-y-1">
          <span className="text-[10px] text-slate-400 uppercase font-semibold">Active Compute Device</span>
          <p className="text-lg font-bold text-blue-400 font-mono uppercase">
            {modelStatus?.device || 'CPU'}
          </p>
          <p className="text-[10px] text-slate-500">
            {modelStatus?.cuda_available ? 'CUDA acceleration enabled' : 'CPU fallback mode'}
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#0f1420] border border-slate-800 space-y-1">
          <span className="text-[10px] text-slate-400 uppercase font-semibold">GPU Hardware Model</span>
          <p className="text-lg font-bold text-slate-100 font-mono">
            {modelStatus?.gpu_name || 'Host CPU'}
          </p>
          <p className="text-[10px] text-slate-500">
            VRAM Allocated: {modelStatus?.vram_allocated_mb || 0} MB
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#0f1420] border border-slate-800 space-y-1">
          <span className="text-[10px] text-slate-400 uppercase font-semibold">Multi-Object Tracker</span>
          <p className="text-lg font-bold text-emerald-400 font-mono">
            ByteTrack
          </p>
          <p className="text-[10px] text-slate-500">
            Identity association with Kalman velocity filtering
          </p>
        </div>
      </div>

      {/* Models List */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Human Model */}
        <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-xs font-semibold text-slate-200 uppercase flex items-center space-x-1.5">
              <Users className="w-4 h-4 text-blue-400" />
              <span>Human Detector</span>
            </h3>
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-bold">
              {modelStatus?.models?.human_detection?.status?.toUpperCase()}
            </span>
          </div>
          <div className="space-y-1 text-xs text-slate-300">
            <p><strong>Architecture:</strong> YOLO11 Nano</p>
            <p><strong>Base Weights:</strong> COCO Pretrained</p>
            <p><strong>Target Class:</strong> Person (ID 0)</p>
          </div>
          <div className="pt-2">
            <label className="text-[10px] text-slate-400 flex justify-between">
              <span>Confidence Threshold:</span>
              <span className="font-mono text-blue-400 font-bold">{(humanConf * 100).toFixed(0)}%</span>
            </label>
            <input
              type="range"
              min="0.10"
              max="0.95"
              step="0.05"
              value={humanConf}
              onChange={(e) => setHumanConf(parseFloat(e.target.value))}
              className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500 mt-1"
            />
          </div>
        </div>

        {/* Weapon Model */}
        <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-xs font-semibold text-slate-200 uppercase flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4 text-rose-400" />
              <span>Weapon Detector</span>
            </h3>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                modelStatus?.models?.weapon_detection?.status === 'loaded'
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : 'bg-amber-500/20 text-amber-400'
              }`}
            >
              {modelStatus?.models?.weapon_detection?.status === 'loaded' ? 'LOADED' : 'AWAITING TRAINING'}
            </span>
          </div>
          <div className="space-y-1 text-xs text-slate-300">
            <p><strong>Architecture:</strong> Custom YOLO</p>
            <p><strong>Classes:</strong> Handgun, Rifle, Shotgun, Knife</p>
            <p><strong>Weights File:</strong> models/weapon/best.pt</p>
          </div>
          <div className="pt-2">
            <label className="text-[10px] text-slate-400 flex justify-between">
              <span>Confidence Threshold:</span>
              <span className="font-mono text-rose-400 font-bold">{(weaponConf * 100).toFixed(0)}%</span>
            </label>
            <input
              type="range"
              min="0.10"
              max="0.95"
              step="0.05"
              value={weaponConf}
              onChange={(e) => setWeaponConf(parseFloat(e.target.value))}
              className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-rose-500 mt-1"
            />
          </div>
        </div>

        {/* Pose Model */}
        <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-xs font-semibold text-slate-200 uppercase flex items-center space-x-1.5">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span>Pose Estimator</span>
            </h3>
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-bold">
              {modelStatus?.models?.pose_estimation?.status?.toUpperCase()}
            </span>
          </div>
          <div className="space-y-1 text-xs text-slate-300">
            <p><strong>Architecture:</strong> YOLO11 Pose</p>
            <p><strong>Keypoints:</strong> Upper-Body + Core (17 pts)</p>
            <p><strong>Association:</strong> Spatial IoU to Human Track</p>
          </div>
          <div className="pt-2">
            <label className="text-[10px] text-slate-400 flex justify-between">
              <span>Confidence Threshold:</span>
              <span className="font-mono text-emerald-400 font-bold">{(poseConf * 100).toFixed(0)}%</span>
            </label>
            <input
              type="range"
              min="0.10"
              max="0.95"
              step="0.05"
              value={poseConf}
              onChange={(e) => setPoseConf(parseFloat(e.target.value))}
              className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-emerald-500 mt-1"
            />
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between p-4 rounded-xl bg-[#0f1420] border border-slate-800">
        <div>
          <p className="text-xs font-semibold text-slate-200">Save Threshold Adjustments</p>
          <p className="text-[10px] text-slate-400">Updates live confidence filters on video processing pipeline</p>
        </div>
        <button
          onClick={handleApplyThresholds}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition"
        >
          Apply Thresholds
        </button>
      </div>

      {message && (
        <div
          className={`p-3 rounded-lg text-xs font-medium ${
            message.type === 'success' ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-800' : 'bg-rose-950/40 text-rose-300 border border-rose-800'
          }`}
        >
          {message.text}
        </div>
      )}
    </div>
  );
}
