import React, { useState, useEffect } from 'react';
import { History, AlertTriangle, CheckCircle2, Image, ShieldAlert, Users, Clock } from 'lucide-react';
import { api } from '../services/api';

export function DetectionHistory() {
  const [alerts, setAlerts] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [activeTab, setActiveTab] = useState('alerts'); // 'alerts' or 'sessions'
  const [severityFilter, setSeverityFilter] = useState('');
  const [previewSnapshot, setPreviewSnapshot] = useState(null);

  const fetchData = async () => {
    try {
      const [alts, sess] = await Promise.all([
        api.getAlerts(100, severityFilter || null),
        api.getSessions()
      ]);
      setAlerts(alts);
      setSessions(sess);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchData();
  }, [severityFilter]);

  const handleAcknowledge = async (alertId) => {
    try {
      await api.acknowledgeAlert(alertId);
      setAlerts(prev =>
        prev.map(a => (a.id === alertId ? { ...a, acknowledged: true } : a))
      );
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-100 uppercase tracking-wider flex items-center space-x-2">
            <History className="w-5 h-5 text-purple-400" />
            <span>Detection History & Incident Audit Log</span>
          </h2>
          <p className="text-xs text-slate-400">
            Persistent SQLite event logs recording timestamps, tracking IDs, severity levels, and camera snapshots.
          </p>
        </div>

        {/* Tab switch */}
        <div className="flex items-center space-x-1 p-1 bg-slate-900 border border-slate-800 rounded-lg">
          <button
            onClick={() => setActiveTab('alerts')}
            className={`px-3 py-1 rounded text-xs font-medium transition ${
              activeTab === 'alerts' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Alerts ({alerts.length})
          </button>
          <button
            onClick={() => setActiveTab('sessions')}
            className={`px-3 py-1 rounded text-xs font-medium transition ${
              activeTab === 'sessions' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Sessions ({sessions.length})
          </button>
        </div>
      </div>

      {activeTab === 'alerts' ? (
        <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-4">
          {/* Filter Bar */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-400">Filter by Severity:</span>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              >
                <option value="">All Severities</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
            </div>

            <button
              onClick={fetchData}
              className="text-xs text-blue-400 hover:text-blue-300 font-medium"
            >
              Refresh Log
            </button>
          </div>

          {alerts.length === 0 ? (
            <p className="text-xs text-slate-500 italic py-8 text-center">No alert events recorded yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="p-3">Severity</th>
                    <th className="p-3">Alert Type</th>
                    <th className="p-3">Track ID</th>
                    <th className="p-3">Observation Message</th>
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Snapshot</th>
                    <th className="p-3 text-right">Review Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {alerts.map((a) => (
                    <tr key={a.id} className="hover:bg-slate-800/30 transition">
                      <td className="p-3">
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
                      </td>
                      <td className="p-3 font-semibold text-slate-200">
                        {a.alert_type}
                      </td>
                      <td className="p-3 text-blue-400 font-bold">
                        {a.tracker_id ? `#${a.tracker_id.toString().padStart(3, '0')}` : '—'}
                      </td>
                      <td className="p-3 font-sans text-slate-300 max-w-xs truncate">
                        {a.message}
                      </td>
                      <td className="p-3 text-slate-400 text-[10px]">
                        {new Date(a.timestamp).toLocaleString()}
                      </td>
                      <td className="p-3">
                        {a.snapshot_url ? (
                          <button
                            onClick={() => setPreviewSnapshot(a.snapshot_url)}
                            className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-blue-400 transition"
                            title="View Snapshot"
                          >
                            <Image className="w-3.5 h-3.5" />
                          </button>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      <td className="p-3 text-right">
                        {a.acknowledged ? (
                          <span className="text-emerald-400 text-[11px] font-sans flex items-center justify-end space-x-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Reviewed</span>
                          </span>
                        ) : (
                          <button
                            onClick={() => handleAcknowledge(a.id)}
                            className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-[10px] font-sans transition"
                          >
                            Acknowledge
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="p-5 rounded-xl bg-[#0f1420] border border-slate-800 space-y-4">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Past Recorded Ingestion Sessions
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="p-3">Session ID</th>
                  <th className="p-3">Source Type</th>
                  <th className="p-3">Source Name / Target</th>
                  <th className="p-3">Started At</th>
                  <th className="p-3">Total Frames</th>
                  <th className="p-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {sessions.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-800/30 transition">
                    <td className="p-3 font-bold text-blue-400">#{s.id}</td>
                    <td className="p-3 uppercase text-slate-300">{s.source_type}</td>
                    <td className="p-3 text-slate-400">{s.source_path || '—'}</td>
                    <td className="p-3 text-slate-400 text-[10px]">{new Date(s.started_at).toLocaleString()}</td>
                    <td className="p-3">{s.total_frames}</td>
                    <td className="p-3 text-right">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px]">
                        {s.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Snapshot Preview Modal */}
      {previewSnapshot && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setPreviewSnapshot(null)}
        >
          <div
            className="bg-slate-900 p-4 rounded-xl border border-slate-700 max-w-2xl w-full space-y-3"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="text-xs font-semibold text-slate-200">Incident Snapshot Preview</span>
              <button
                onClick={() => setPreviewSnapshot(null)}
                className="text-slate-400 hover:text-white text-xs"
              >
                Close &times;
              </button>
            </div>
            <img
              src={previewSnapshot}
              alt="Snapshot"
              className="w-full h-auto rounded-lg border border-slate-800 object-contain"
            />
          </div>
        </div>
      )}
    </div>
  );
}
