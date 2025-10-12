import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Activity, Settings as SettingsIcon, Home } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import StatusPanel from './components/StatusPanel';
import './App.css';

function App() {
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');

  useEffect(() => {
    // Check initial connection status
    const checkConnection = async () => {
      try {
        setConnectionStatus('connecting');
        const response = await fetch(`http://${window.location.hostname}:3000/api/v1/pipeline/health`);
        if (response.ok) {
          setConnectionStatus('connected');
        } else {
          setConnectionStatus('disconnected');
        }
      } catch (error) {
        console.error('Connection check failed:', error);
        setConnectionStatus('disconnected');
      }
    };

    checkConnection();

    // Check connection status periodically
    const interval = setInterval(checkConnection, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <Activity className="h-8 w-8 text-blue-600" />
                <h1 className="ml-2 text-xl font-semibold text-gray-900">
                  Jarvis Person Tracker
                </h1>
              </div>
              <StatusPanel status={connectionStatus} />
            </div>
          </div>
        </header>

        {/* Navigation */}
        <nav className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex space-x-8">
              <Link
                to="/"
                className="flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                <Home className="h-4 w-4 mr-2" />
                Dashboard
              </Link>
              <Link
                to="/settings"
                className="flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                <SettingsIcon className="h-4 w-4 mr-2" />
                Settings
              </Link>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
