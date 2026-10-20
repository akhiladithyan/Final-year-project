import React, { useState, useEffect } from 'react';
import { Database, Play, BookOpen, AlertCircle, CheckCircle2, FileText, Terminal, Layers } from 'lucide-react';
import { api } from '../services/api';

export function DatasetTraining() {
  const [datasetInfo, setDatasetInfo] = useState(null);
  const [trainingStatus, setTrainingStatus] = useState(null);
  const [epochs, setEpochs] = useState(50);
  const [batchSize, setBatchSize] = useState(16);
  const [imgSize, setImgSize] = useState(640);
  const [modelSize, setModelSize] = useState('yolo11n.pt');
  const [message, setMessage] = useState(null);

  const fetchStatus = async () => {
    try {
      const [dInfo, tStat] = await Promise.all([
        api.getDatasetInfo(),
        api.getTrainingStatus()
      ]);
      setDatasetInfo(dInfo);
      setTrainingStatus(tStat);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleStartTraining = async () => {
    setMessage(null);
    try {
      const res = await api.startTraining({
        epochs: parseInt(epochs, 10),
        batch_size: parseInt(batchSize, 10),
        imgsz: parseInt(imgSize, 10),
        model_size: modelSize
      });
      setMessage({ type: 'success', text: res.message });
      await fetchStatus();
    } catch (e) {
      setMessage({ type: 'error', text: e.message || 'Failed to start training' });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-base font-bold text-slate-100 uppercase tracking-wider flex items-center space-x-2">
          <Database className="w-5 h-5 text-amber-400" />
          <span>Dataset Preparation & Custom Weapon Model Training</span>
        </h2>
        <p className="text-xs text-slate-400">
          Complete guide, annotation workflow, dataset verification, and Ultralytics training runner for custom weapon classes.
        </p>
      </div>

      {/* Dataset Counts Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#0f1420] border border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-semibold">Total Annotated Images</span>
          <p className="text-2xl font-bold text-slate-100 font-mono mt-1">
            {datasetInfo?.total_images || 0}
          </p>
          <span className="text-[10px] text-slate-500">Across train, val, and test</span>
        </div>

        <div className="p-4 rounded-xl bg-[#0f1420] border border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-semibold">Training Set</span>
          <p className="text-2xl font-bold text-blue-400 font-mono mt-1">
            {datasetInfo?.counts?.train_images || 0}
          </p>
          <span className="text-[10px] text-slate-500">{datasetInfo?.counts?.train_labels || 0} label files (.txt)</span>
        </div>

        <div className="p-4 rounded-xl bg-[#0f1420] border border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-semibold">Validation Set</span>
          <p className="text-2xl font-bold text-emerald-400 font-mono mt-1">
            {datasetInfo?.counts?.val_images || 0}
          </p>
          <span className="text-[10px] text-slate-500">{datasetInfo?.counts?.val_labels || 0} label files (.txt)</span>
        </div>

        <div className="p-4 rounded-xl bg-[#0f1420] border border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-semibold">Testing Set</span>
          <p className="text-2xl font-bold text-purple-400 font-mono mt-1">
            {datasetInfo?.counts?.test_images || 0}
          </p>
          <span className="text-[10px] text-slate-500">{datasetInfo?.counts?.test_labels || 0} label files (.txt)</span>
        </div>
      </div>

      {/* Complete Step-by-Step Training Guide Accordion / Panel */}
      <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-4">
        <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
          <BookOpen className="w-4 h-4 text-blue-400" />
          <span>Full Workflow: How to Train the Weapon Detection Model</span>
        </h3>

        <div className="space-y-3 text-xs text-slate-300">
          {/* Step 1 */}
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1.5">
            <div className="flex items-center space-x-2 text-blue-400 font-bold">
              <span className="w-5 h-5 rounded-full bg-blue-500/20 flex items-center justify-center text-[11px] border border-blue-500/30">1</span>
              <span>Dataset Acquisition & Negative Samples</span>
            </div>
            <p className="text-slate-400 pl-7 text-[11px] leading-relaxed">
              Acquire weapon datasets in YOLO format (Roboflow Universe, Kaggle, Open Images V7) with classes:
              <strong className="text-slate-200"> 0: Handgun, 1: Rifle, 2: Shotgun, 3: Knife</strong>.
              <br />
              <strong className="text-amber-400">Critical Requirement:</strong> Include 10–15% background/negative images containing humans holding everyday objects (wallets, phones, drills, bottles, umbrellas) with empty label files to eliminate false weapon triggers.
            </p>
          </div>

          {/* Step 2 */}
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1.5">
            <div className="flex items-center space-x-2 text-emerald-400 font-bold">
              <span className="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center text-[11px] border border-emerald-500/30">2</span>
              <span>Directory Structure & data.yaml</span>
            </div>
            <p className="text-slate-400 pl-7 text-[11px] leading-relaxed">
              Place images and <code>.txt</code> annotations into:
              <code className="text-slate-200 block my-1 font-mono bg-slate-950 p-1.5 rounded">
                training/datasets/weapons/train/images & labels<br />
                training/datasets/weapons/val/images & labels<br />
                training/datasets/weapons/data.yaml
              </code>
            </p>
          </div>

          {/* Step 3 */}
          <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1.5">
            <div className="flex items-center space-x-2 text-purple-400 font-bold">
              <span className="w-5 h-5 rounded-full bg-purple-500/20 flex items-center justify-center text-[11px] border border-purple-500/30">3</span>
              <span>Execute Training Script via Terminal or UI</span>
            </div>
            <p className="text-slate-400 pl-7 text-[11px] leading-relaxed">
              You can execute training directly via terminal:
              <code className="text-slate-200 block my-1 font-mono bg-slate-950 p-1.5 rounded">
                python training/scripts/train_weapon.py --epochs 50 --batch 16 --imgsz 640
              </code>
              Training will use your RTX 4050 GPU (CUDA), log validation mAP50, mAP50-95, and automatically output best weights to <code>models/weapon/best.pt</code>.
            </p>
          </div>
        </div>
      </div>

      {/* Training Configuration Panel */}
      <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-4">
        <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
          <Layers className="w-4 h-4 text-amber-400" />
          <span>Training Execution Configuration</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <label className="text-[10px] text-slate-400 uppercase font-semibold">Epochs</label>
            <input
              type="number"
              value={epochs}
              onChange={(e) => setEpochs(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] text-slate-400 uppercase font-semibold">Batch Size</label>
            <select
              value={batchSize}
              onChange={(e) => setBatchSize(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
            >
              <option value={8}>8 (Low VRAM)</option>
              <option value={16}>16 (Standard / RTX 4050 6GB)</option>
              <option value={32}>32 (High VRAM)</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] text-slate-400 uppercase font-semibold">Image Size (imgsz)</label>
            <select
              value={imgSize}
              onChange={(e) => setImgSize(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
            >
              <option value={640}>640 x 640 (Recommended)</option>
              <option value={480}>480 x 480 (Faster)</option>
              <option value={1280}>1280 x 1280 (High Detail)</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] text-slate-400 uppercase font-semibold">Base Model</label>
            <select
              value={modelSize}
              onChange={(e) => setModelSize(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
            >
              <option value="yolo11n.pt">YOLO11 Nano (Fastest inference)</option>
              <option value="yolo11s.pt">YOLO11 Small (Balanced)</option>
              <option value="yolo11m.pt">YOLO11 Medium (Higher precision)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          <p className="text-[11px] text-slate-400">
            Training runs as a non-blocking background task. You can monitor loss and validation mAP curves.
          </p>
          <button
            onClick={handleStartTraining}
            disabled={trainingStatus?.is_training}
            className="px-5 py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white rounded-lg text-xs font-bold flex items-center space-x-2 transition"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{trainingStatus?.is_training ? 'Training in Progress...' : 'Start Training Job'}</span>
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
    </div>
  );
}
