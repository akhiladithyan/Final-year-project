import React, { useState } from 'react';
import { DashboardLayout } from './layouts/DashboardLayout';
import { useTelemetryWebSocket } from './hooks/useTelemetryWebSocket';

// Pages
import { Overview } from './pages/Overview';
import { LiveDetection } from './pages/LiveDetection';
import { HumanTracking } from './pages/HumanTracking';
import { WeaponDetection } from './pages/WeaponDetection';
import { PoseTracking } from './pages/PoseTracking';
import { DetectionHistory } from './pages/DetectionHistory';
import { ModelManagement } from './pages/ModelManagement';
import { DatasetTraining } from './pages/DatasetTraining';
import { Settings } from './pages/Settings';

export function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const { telemetry, alerts, setAlerts, isConnected } = useTelemetryWebSocket();

  const renderActivePage = () => {
    switch (activeTab) {
      case 'overview':
        return <Overview telemetry={telemetry} alerts={alerts} onNavigate={setActiveTab} />;
      case 'live':
        return <LiveDetection telemetry={telemetry} alerts={alerts} />;
      case 'tracking':
        return <HumanTracking telemetry={telemetry} />;
      case 'weapons':
        return <WeaponDetection telemetry={telemetry} />;
      case 'pose':
        return <PoseTracking telemetry={telemetry} />;
      case 'history':
        return <DetectionHistory />;
      case 'models':
        return <ModelManagement />;
      case 'training':
        return <DatasetTraining />;
      case 'settings':
        return <Settings />;
      default:
        return <Overview telemetry={telemetry} alerts={alerts} onNavigate={setActiveTab} />;
    }
  };

  return (
    <DashboardLayout
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      isConnected={isConnected}
      fps={telemetry.fps || 0}
      device={telemetry.device || 'CPU'}
      activeTracksCount={telemetry.active_tracks?.length || telemetry.humans?.length || 0}
      weaponsCount={telemetry.weapons?.length || 0}
    >
      {renderActivePage()}
    </DashboardLayout>
  );
}

export default App;

