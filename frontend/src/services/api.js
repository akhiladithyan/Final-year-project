const API_BASE = '/api';

export const api = {
  // Video Ingestion & Controls
  async getVideoStatus() {
    const res = await fetch(`${API_BASE}/video/status`);
    return res.json();
  },

  async startWebcam(cameraIndex = 0) {
    const res = await fetch(`${API_BASE}/video/start_webcam`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ camera_index: cameraIndex })
    });
    return res.json();
  },

  async uploadVideo(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/video/upload`, {
      method: 'POST',
      body: formData
    });
    return res.json();
  },

  async startVideoFile(filename) {
    const res = await fetch(`${API_BASE}/video/start_file`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename })
    });
    return res.json();
  },

  async startRtsp(rtspUrl) {
    const res = await fetch(`${API_BASE}/video/start_rtsp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rtsp_url: rtspUrl })
    });
    return res.json();
  },

  async pauseVideo() {
    const res = await fetch(`${API_BASE}/video/pause`, { method: 'POST' });
    return res.json();
  },

  async resumeVideo() {
    const res = await fetch(`${API_BASE}/video/resume`, { method: 'POST' });
    return res.json();
  },

  async stopVideo() {
    const res = await fetch(`${API_BASE}/video/stop`, { method: 'POST' });
    return res.json();
  },

  async listUploadedVideos() {
    const res = await fetch(`${API_BASE}/video/uploads`);
    return res.json();
  },

  // Detection & Tracking
  async getActiveTracks() {
    const res = await fetch(`${API_BASE}/tracking/active`);
    return res.json();
  },

  async getTrackDetail(trackerId) {
    const res = await fetch(`${API_BASE}/tracking/${trackerId}`);
    return res.json();
  },

  async getCurrentDetections() {
    const res = await fetch(`${API_BASE}/detection/current`);
    return res.json();
  },

  // Models & Hardware
  async getModelStatus() {
    const res = await fetch(`${API_BASE}/models/status`);
    return res.json();
  },

  async updateThresholds(thresholds) {
    const res = await fetch(`${API_BASE}/models/thresholds`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(thresholds)
    });
    return res.json();
  },

  async loadWeaponWeights(weightsPath) {
    const res = await fetch(`${API_BASE}/models/load_weapon_weights`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ weights_path: weightsPath })
    });
    return res.json();
  },

  async getAvailableWeights() {
    const res = await fetch(`${API_BASE}/models/available_weights`);
    return res.json();
  },

  // History & Alerts
  async getAlerts(limit = 50, severity = null) {
    const url = new URL(`${window.location.origin}${API_BASE}/history/alerts`);
    url.searchParams.append('limit', limit);
    if (severity) url.searchParams.append('severity', severity);
    const res = await fetch(url.toString());
    return res.json();
  },

  async acknowledgeAlert(alertId) {
    const res = await fetch(`${API_BASE}/history/alerts/${alertId}/acknowledge`, { method: 'POST' });
    return res.json();
  },

  async getSessions() {
    const res = await fetch(`${API_BASE}/history/sessions`);
    return res.json();
  },

  // Dataset & Training
  async getDatasetInfo() {
    const res = await fetch(`${API_BASE}/training/dataset_info`);
    return res.json();
  },

  async getTrainingStatus() {
    const res = await fetch(`${API_BASE}/training/status`);
    return res.json();
  },

  async startTraining(config) {
    const res = await fetch(`${API_BASE}/training/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    return res.json();
  }
};
