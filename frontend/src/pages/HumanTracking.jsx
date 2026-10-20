import React, { useState, useEffect } from 'react';
import { Users, Clock, Zap, MapPin, Eye, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export function HumanTracking({ telemetry }) {
  const [activeTracks, setActiveTracks] = useState([]);
  const [selectedTrackId, setSelectedTrackId] = useState(null);
  const [trackDetail, setTrackDetail] = useState(null);

  useEffect(() => {
    const fetchActive = async () => {
      try {
        const res = await api.getActiveTracks();
        setActiveTracks(res.tracks || []);
        if (res.tracks && res.tracks.length > 0 && !selectedTrackId) {
          setSelectedTrackId(res.tracks[0].tracker_id);
        }
      } catch (e) {
        console.error(e);
      }
    };
    fetchActive();
    const interval = setInterval(fetchActive, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedTrackId) {
      api.getTrackDetail(selectedTrackId)
        .then(res => setTrackDetail(res))
        .catch(err => console.error(err));
    }
  }, [selectedTrackId]);

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-100 uppercase tracking-wider flex items-center space-x-2">
            <Users className="w-5 h-5 text-blue-400" />
            <span>Human Identification & Multi-Person Tracking</span>
          </h2>
          <p className="text-xs text-slate-400">
            ByteTrack algorithm assigns stable numerical IDs across consecutive frames with trajectory preservation.
          </p>
        </div>
        <span className="px-3 py-1 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 font-mono text-xs font-semibold">
          {activeTracks.length} Active Tracks
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Active Tracks Table */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-4">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Active Identified Humans
          </h3>

          {activeTracks.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs italic space-y-2">
              <Users className="w-8 h-8 mx-auto text-slate-600" />
              <p>No active humans currently tracked in video stream.</p>
              <p className="text-[11px] text-slate-600">Start the webcam or upload a test video from Overview to begin tracking.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="p-3">Track ID</th>
                    <th className="p-3">Confidence</th>
                    <th className="p-3">Velocity</th>
                    <th className="p-3">Frames</th>
                    <th className="p-3">Association</th>
                    <th className="p-3">First Seen</th>
                    <th className="p-3 text-right">Inspect</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {activeTracks.map((t) => (
                    <tr
                      key={t.tracker_id}
                      onClick={() => setSelectedTrackId(t.tracker_id)}
                      className={`hover:bg-slate-800/40 cursor-pointer transition ${
                        selectedTrackId === t.tracker_id ? 'bg-blue-600/10' : ''
                      }`}
                    >
                      <td className="p-3 font-bold text-blue-400">
                        #{t.tracker_id.toString().padStart(3, '0')}
                      </td>
                      <td className="p-3">
                        <span className="text-emerald-400">{(t.confidence * 100).toFixed(1)}%</span>
                      </td>
                      <td className="p-3 text-slate-300">
                        {t.velocity} px/f
                      </td>
                      <td className="p-3 text-slate-400">
                        {t.frames_tracked}
                      </td>
                      <td className="p-3">
                        {t.association_status && t.association_status !== 'NONE' ? (
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              t.association_status === 'PROBABLE'
                                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                : 'bg-orange-500/20 text-orange-300 border border-orange-500/30'
                            }`}
                          >
                            {t.association_status}
                          </span>
                        ) : (
                          <span className="text-slate-500 text-[11px]">Clear</span>
                        )}
                      </td>
                      <td className="p-3 text-slate-400 text-[10px]">
                        {new Date(t.first_seen).toLocaleTimeString()}
                      </td>
                      <td className="p-3 text-right">
                        <button className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] transition">
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right 1 Col: Selected Track Details */}
        <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-4">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
            <MapPin className="w-4 h-4 text-emerald-400" />
            <span>Track Identity #{selectedTrackId || '—'}</span>
          </h3>

          {!trackDetail ? (
            <p className="text-xs text-slate-500 italic py-6 text-center">Select a track to inspect historical movement and upper-body landmarks.</p>
          ) : (
            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Total Frames</span>
                  <span className="font-mono text-sm font-bold text-slate-200">{trackDetail.frames_tracked}</span>
                </div>
                <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Peak Velocity</span>
                  <span className="font-mono text-sm font-bold text-blue-400">{trackDetail.max_velocity} px/f</span>
                </div>
              </div>

              <div className="p-3 rounded bg-slate-900/80 border border-slate-800 space-y-2">
                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Bounding Box Coordinates</span>
                <div className="font-mono text-[11px] text-slate-300 grid grid-cols-2 gap-1">
                  <span>X1: {trackDetail.bbox[0]}px</span>
                  <span>Y1: {trackDetail.bbox[1]}px</span>
                  <span>X2: {trackDetail.bbox[2]}px</span>
                  <span>Y2: {trackDetail.bbox[3]}px</span>
                </div>
              </div>

              <div className="p-3 rounded bg-slate-900/80 border border-slate-800 space-y-2">
                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Trajectory Coordinates ({trackDetail.trajectory?.length || 0} points)</span>
                <div className="max-h-36 overflow-y-auto space-y-1 font-mono text-[10px] text-slate-400 pr-1">
                  {trackDetail.trajectory?.slice(-10).map((pt, idx) => (
                    <div key={idx} className="flex justify-between border-b border-slate-800/40 py-0.5">
                      <span>Point #{idx + 1}</span>
                      <span className="text-slate-300">({pt[0]}, {pt[1]})</span>
                    </div>
                  ))}
                </div>
              </div>

              {trackDetail.association_status !== 'NONE' && (
                <div className="p-3 rounded bg-amber-950/20 border border-amber-800/40 text-amber-300 text-xs space-y-1">
                  <p className="font-bold flex items-center space-x-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    <span>Association Flagged: {trackDetail.associated_weapon}</span>
                  </p>
                  <p className="text-[10px] text-amber-400/80">Status: {trackDetail.association_status}. Review frame visually.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
