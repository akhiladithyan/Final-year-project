import React, { useState, useEffect } from 'react';
import { Activity, Users, Crosshair, TrendingUp } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { api } from '../services/api';

export function PoseTracking({ telemetry }) {
  const [activeTracks, setActiveTracks] = useState([]);
  const [selectedTrackId, setSelectedTrackId] = useState(null);
  const [trackDetail, setTrackDetail] = useState(null);
  const [velocityHistory, setVelocityHistory] = useState([]);

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
        .then(res => {
          setTrackDetail(res);
          // Append to velocity chart history
          setVelocityHistory(prev => {
            const newPt = {
              time: new Date().toLocaleTimeString(),
              velocity: res.current_velocity || 0,
              max: res.max_velocity || 0
            };
            const updated = [...prev, newPt];
            return updated.slice(-20); // Keep last 20 ticks
          });
        })
        .catch(err => console.error(err));
    }
  }, [selectedTrackId, telemetry.frame_number]);

  const kps = trackDetail?.pose_keypoints || {};

  const upperBodyKeypoints = [
    { label: 'Left Shoulder', data: kps.left_shoulder },
    { label: 'Right Shoulder', data: kps.right_shoulder },
    { label: 'Left Elbow', data: kps.left_elbow },
    { label: 'Right Elbow', data: kps.right_elbow },
    { label: 'Left Wrist', data: kps.left_wrist },
    { label: 'Right Wrist', data: kps.right_wrist },
    { label: 'Nose', data: kps.nose },
    { label: 'Left Hip', data: kps.left_hip },
    { label: 'Right Hip', data: kps.right_hip },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-100 uppercase tracking-wider flex items-center space-x-2">
            <Activity className="w-5 h-5 text-emerald-400" />
            <span>Upper-Body Pose Landmark & Wrist Tracking</span>
          </h2>
          <p className="text-xs text-slate-400">
            Real-time keypoint extraction for shoulders, elbows, and wrists mapped directly to persistent Tracking IDs.
          </p>
        </div>

        {/* Track Selector */}
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400">Inspect Person ID:</span>
          <select
            value={selectedTrackId || ''}
            onChange={(e) => setSelectedTrackId(parseInt(e.target.value, 10))}
            className="bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 font-mono font-bold focus:outline-none focus:border-blue-500"
          >
            {activeTracks.map((t) => (
              <option key={t.tracker_id} value={t.tracker_id}>
                ID #{t.tracker_id.toString().padStart(3, '0')} ({(t.confidence * 100).toFixed(0)}%)
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Keypoints Coordinates Table */}
        <div className="lg:col-span-2 p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-4">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
            <Crosshair className="w-4 h-4 text-blue-400" />
            <span>Extracted Anatomical Keypoints (Track ID #{selectedTrackId || '—'})</span>
          </h3>

          {!trackDetail ? (
            <p className="text-xs text-slate-500 italic py-8 text-center">
              No person selected or active in stream.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="p-3">Keypoint Name</th>
                    <th className="p-3">X Coordinate (px)</th>
                    <th className="p-3">Y Coordinate (px)</th>
                    <th className="p-3">Confidence</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {upperBodyKeypoints.map((item, idx) => {
                    const isAvailable = Boolean(item.data);
                    const conf = item.data?.conf || 0;
                    return (
                      <tr key={idx} className="hover:bg-slate-800/30 transition">
                        <td className="p-3 font-semibold text-slate-200">
                          {item.label}
                        </td>
                        <td className="p-3 text-slate-300">
                          {isAvailable ? `${Math.round(item.data.x)} px` : '—'}
                        </td>
                        <td className="p-3 text-slate-300">
                          {isAvailable ? `${Math.round(item.data.y)} px` : '—'}
                        </td>
                        <td className="p-3">
                          {isAvailable ? (
                            <span className="text-emerald-400 font-bold">{(conf * 100).toFixed(0)}%</span>
                          ) : (
                            '—'
                          )}
                        </td>
                        <td className="p-3">
                          {isAvailable && conf > 0.4 ? (
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                              Tracked
                            </span>
                          ) : (
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-500">
                              Occluded
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Right 1 Col: Trajectory & Velocity Chart */}
        <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-4">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <span>Velocity Trajectory (Recharts)</span>
          </h3>

          <div className="h-60 w-full pt-2">
            {velocityHistory.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-500 italic">
                Awaiting velocity telemetry...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={velocityHistory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="time" stroke="#64748b" fontSize={9} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={9} tickLine={false} unit="px" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="velocity"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={false}
                    name="Current Velocity"
                  />
                  <Line
                    type="monotone"
                    dataKey="max"
                    stroke="#10b981"
                    strokeWidth={1}
                    strokeDasharray="4 4"
                    dot={false}
                    name="Peak Velocity"
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 space-y-1 text-xs text-slate-400">
            <p className="font-semibold text-slate-300">Wrist History Buffer</p>
            <p className="text-[11px]">
              Left Wrist buffer: {trackDetail?.wrist_history_left?.length || 0} pts | Right Wrist buffer: {trackDetail?.wrist_history_right?.length || 0} pts
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
