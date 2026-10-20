import React, { useState, useEffect } from 'react';
import {
  Users,
  ShieldAlert,
  Link as LinkIcon,
  Activity,
  Play,
  Square,
  Pause,
  Upload,
  Video,
  Radio,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Clock
} from 'lucide-react';
import { api } from '../services/api';

export function Overview({ telemetry, alerts, onNavigate }) {
  const [videoStatus, setVideoStatus] = useState({
    is_running: false,
    is_paused: false,
    source_type: null,
    source_target: null,
    fps: 0,
    active_humans: 0,
    weapons_flagged: 0,
    associations_count: 0
  });

  const [modelStatus, setModelStatus] = useState(null);
  const [uploadedVideos, setUploadedVideos] = useState([]);
  const [selectedFile, setSelectedFile] = useState('');
  const [rtspUrl, setRtspUrl] = useState('rtsp://');
  const [cameraIndex, setCameraIndex] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  const fetchStatus = async () => {
    try {
      const [vStat, mStat, uList] = await Promise.all([
        api.getVideoStatus(),
        api.getModelStatus(),
        api.listUploadedVideos()
      ]);
      setVideoStatus(vStat);
      setModelStatus(mStat);
      setUploadedVideos(uList.videos || []);
      if (uList.videos && uList.videos.length > 0 && !selectedFile) {
        setSelectedFile(uList.videos[0].name);
      }
    } catch (e) {
      console.error('Failed to fetch status:', e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleStartWebcam = async () => {
    try {
      await api.startWebcam(parseInt(cameraIndex, 10));
      await fetchStatus();
    } catch (e) {
      alert(`Error starting webcam: ${e.message}`);
    }
  };

  const handleStartFile = async () => {
    if (!selectedFile) return alert('Select an uploaded video file first');
    try {
      await api.startVideoFile(selectedFile);
      await fetchStatus();
    } catch (e) {
      alert(`Error starting video file: ${e.message}`);
    }
  };

  const handleStartRtsp = async () => {
    if (!rtspUrl || rtspUrl === 'rtsp://') return alert('Enter a valid RTSP stream URL');
    try {
      await api.startRtsp(rtspUrl);
      await fetchStatus();
    } catch (e) {
      alert(`Error connecting to RTSP: ${e.message}`);
    }
  };

  const handleStop = async () => {
    try {
      await api.stopVideo();
      await fetchStatus();
    } catch (e) {
      console.error(e);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    try {
      await api.uploadVideo(file);
      await fetchStatus();
      setSelectedFile(file.name);
    } catch (err) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const metrics = [
    {
      title: 'Currently Tracked People',
      value: telemetry.active_tracks?.length ?? videoStatus.active_humans ?? 0,
      icon: Users,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/20'
    },
    {
      title: 'Weapon Sightings (Review)',
      value: telemetry.weapons?.length ?? videoStatus.weapons_flagged ?? 0,
      icon: ShieldAlert,
      color: 'text-rose-400',
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/20'
    },
    {
      title: 'Probable Associations',
      value: telemetry.associations?.filter(a => a.association_status === 'PROBABLE').length ?? 0,
      icon: LinkIcon,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20'
    },
    {
      title: 'Total Alert Events',
      value: alerts?.length ?? 0,
      icon: Activity,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((m, idx) => {
          const Icon = m.icon;
          return (
            <div
              key={idx}
              className={`p-4 rounded-xl bg-[#0f1420] border ${m.border} flex items-center justify-between shadow-sm`}
            >
              <div>
                <p className="text-xs text-slate-400 uppercase tracking-wider font-medium">{m.title}</p>
                <p className="text-2xl font-bold text-slate-100 font-mono mt-1">{m.value}</p>
              </div>
              <div className={`p-3 rounded-lg ${m.bg}`}>
                <Icon className={`w-6 h-6 ${m.color}`} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Video Control Center & System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ingestion & Pipeline Controls */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                <Video className="w-4 h-4 text-blue-400" />
                <span>Video Input & Ingestion Pipeline</span>
              </h2>
              <p className="text-xs text-slate-400">Webcam, uploaded video file, or RTSP surveillance camera stream</p>
            </div>

            <div className="flex items-center space-x-2">
              {videoStatus.is_running ? (
                <button
                  onClick={handleStop}
                  className="px-3 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 rounded-lg text-xs font-medium flex items-center space-x-1.5 transition"
                >
                  <Square className="w-3.5 h-3.5" />
                  <span>Stop Stream</span>
                </button>
              ) : (
                <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-400 text-xs">
                  Pipeline Idle
                </span>
              )}
            </div>
          </div>

          {/* Input Method Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Webcam Selector */}
            <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
              <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
                <Video className="w-4 h-4 text-blue-400" />
                <span>Webcam / Local USB</span>
              </div>
              <div className="space-y-1">
                <label className="text-[10px] text-slate-400">Camera Device Index</label>
                <select
                  value={cameraIndex}
                  onChange={(e) => setCameraIndex(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700/80 rounded px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                >
                  <option value={0}>Camera 0 (Default)</option>
                  <option value={1}>Camera 1 (Secondary)</option>
                  <option value={2}>Camera 2 (USB Feed)</option>
                </select>
              </div>
              <button
                onClick={handleStartWebcam}
                className="w-full py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium flex items-center justify-center space-x-1.5 transition"
              >
                <Play className="w-3 h-3" />
                <span>Start Camera</span>
              </button>
            </div>

            {/* Video File Upload */}
            <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
              <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
                <Upload className="w-4 h-4 text-emerald-400" />
                <span>Video File Processing</span>
              </div>
              <div className="space-y-1">
                <label className="text-[10px] text-slate-400">Select File or Upload</label>
                <select
                  value={selectedFile}
                  onChange={(e) => setSelectedFile(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700/80 rounded px-2 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                >
                  {uploadedVideos.length === 0 ? (
                    <option value="">No videos uploaded</option>
                  ) : (
                    uploadedVideos.map((v) => (
                      <option key={v.name} value={v.name}>
                        {v.name} ({v.size_mb} MB)
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <label className="flex-1 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded text-xs text-center cursor-pointer transition">
                  <span>{isUploading ? 'Uploading...' : 'Upload'}</span>
                  <input
                    type="file"
                    accept=".mp4,.avi,.mov,.mkv"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>
                <button
                  onClick={handleStartFile}
                  disabled={!selectedFile}
                  className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded text-xs font-medium flex items-center justify-center space-x-1.5 transition"
                >
                  <Play className="w-3 h-3" />
                  <span>Start File</span>
                </button>
              </div>
            </div>

            {/* RTSP Stream */}
            <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
              <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
                <Radio className="w-4 h-4 text-purple-400" />
                <span>RTSP Network Stream</span>
              </div>
              <div className="space-y-1">
                <label className="text-[10px] text-slate-400">RTSP Stream URL</label>
                <input
                  type="text"
                  value={rtspUrl}
                  onChange={(e) => setRtspUrl(e.target.value)}
                  placeholder="rtsp://192.168.1.100:554/live"
                  className="w-full bg-slate-950 border border-slate-700/80 rounded px-2 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
                />
              </div>
              <button
                onClick={handleStartRtsp}
                className="w-full py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded text-xs font-medium flex items-center justify-center space-x-1.5 transition"
              >
                <Play className="w-3 h-3" />
                <span>Connect RTSP</span>
              </button>
            </div>
          </div>

          {/* Quick Preview Link */}
          {videoStatus.is_running && (
            <div className="p-3 rounded-lg bg-blue-950/30 border border-blue-800/40 flex items-center justify-between">
              <div className="flex items-center space-x-2 text-xs text-blue-300">
                <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
                <span>Active Source: <strong>{videoStatus.source_type?.toUpperCase()}</strong> ({videoStatus.source_target})</span>
              </div>
              <button
                onClick={() => onNavigate('live')}
                className="text-xs text-blue-400 hover:text-blue-300 font-semibold underline"
              >
                Open Fullscreen Live HUD &rarr;
              </button>
            </div>
          )}
        </div>

        {/* AI Modules Status Panel */}
        <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-4">
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-blue-400" />
            <span>AI Module Diagnostics</span>
          </h2>

          <div className="space-y-3">
            {/* Human Detection */}
            <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800/80 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-200">Module 1: Human Tracker</p>
                <p className="text-[10px] text-slate-400">YOLO11 COCO + ByteTrack</p>
              </div>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-semibold border border-emerald-500/30">
                ACTIVE
              </span>
            </div>

            {/* Weapon Detection */}
            <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800/80 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-200">Module 2: Weapon Detector</p>
                <p className="text-[10px] text-slate-400">Custom YOLO (Guns & Knives)</p>
              </div>
              {modelStatus?.models?.weapon_detection?.status === 'loaded' ? (
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-semibold border border-emerald-500/30">
                  WEIGHTS LOADED
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 text-[10px] font-semibold border border-amber-500/30">
                  AWAITING TRAINING
                </span>
              )}
            </div>

            {/* Association Service */}
            <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800/80 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-200">Module 3: Person Association</p>
                <p className="text-[10px] text-slate-400">Spatial Overlap & Wrist Proximity</p>
              </div>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-semibold border border-emerald-500/30">
                ACTIVE
              </span>
            </div>

            {/* Pose Estimation */}
            <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800/80 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-200">Module 4: Upper-Body Pose</p>
                <p className="text-[10px] text-slate-400">Shoulders, Elbows, Wrists</p>
              </div>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-semibold border border-emerald-500/30">
                ACTIVE
              </span>
            </div>

            {/* Movement Analytics */}
            <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800/80 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-200">Module 5: Movement Analytics</p>
                <p className="text-[10px] text-slate-400">Trajectory Velocity & HUD</p>
              </div>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-semibold border border-emerald-500/30">
                ACTIVE
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Alerts Feed */}
      <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
            <Clock className="w-4 h-4 text-amber-400" />
            <span>Latest Situational Awareness Alerts</span>
          </h2>
          <button
            onClick={() => onNavigate('history')}
            className="text-xs text-blue-400 hover:text-blue-300"
          >
            View Full Alert Log &rarr;
          </button>
        </div>

        {alerts.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-2">No alerts triggered yet. Video stream monitoring is clear.</p>
        ) : (
          <div className="space-y-2">
            {alerts.slice(0, 5).map((a, i) => (
              <div
                key={i}
                className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/70 flex items-center justify-between text-xs"
              >
                <div className="flex items-center space-x-3">
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      a.severity === 'CRITICAL'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : a.severity === 'WARNING'
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                    }`}
                  >
                    {a.severity}
                  </span>
                  <span className="text-slate-300 font-medium">{a.message}</span>
                </div>
                <span className="text-[10px] text-slate-500 font-mono">
                  {new Date(a.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
