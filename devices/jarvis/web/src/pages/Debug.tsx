import React, { useState, useEffect } from 'react';
import { Activity, Database, Cpu } from 'lucide-react';
import VideoFeed from '../components/VideoFeed';
import DetectionView from '../components/DetectionView';
import JarvisApiClient from '../services/api';
import JarvisWebSocketClient from '../services/websocket';
import { AnalysisResult, UnifiedDetection } from '../types/api';

const Debug: React.FC = () => {
  const [latestResult, setLatestResult] = useState<AnalysisResult | null>(null);
  const [allDetections, setAllDetections] = useState<UnifiedDetection[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [debugInfo, setDebugInfo] = useState<any>(null);
  const [error, setError] = useState<string>('');

  const apiClient = new JarvisApiClient();
  const wsClient = new JarvisWebSocketClient();

  useEffect(() => {
    // Initialize WebSocket connection
    const initWebSocket = async () => {
      try {
        await wsClient.connect();
        setIsConnected(true);

        // Subscribe to all classifiers
        wsClient.subscribe(['person', 'object', 'face'], {
          confidence_threshold: 0.3,
          include_depth: true,
          include_3d_position: true
        });

        // Handle analysis results
        wsClient.onAnalysisResult((result: AnalysisResult) => {
          setLatestResult(result);
          
          // Flatten all detections
          const allDetections: UnifiedDetection[] = [];
          Object.values(result.detections).forEach(detections => {
            allDetections.push(...detections);
          });
          setAllDetections(allDetections);
        });

      } catch (error) {
        console.error('WebSocket connection failed:', error);
        setIsConnected(false);
      }
    };

    initWebSocket();
    loadDebugInfo();

    // Cleanup on unmount
    return () => {
      wsClient.disconnect();
    };
  }, []);

  const loadDebugInfo = async () => {
    try {
      const [status, classifierStats] = await Promise.all([
        apiClient.getStatus(),
        apiClient.getClassifierStats()
      ]);
      
      setDebugInfo({
        status,
        classifierStats
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load debug info');
    }
  };

  const testAnalysis = async () => {
    try {
      const result = await apiClient.testAnalysis();
      setLatestResult(result);
      
      // Flatten all detections
      const allDetections: UnifiedDetection[] = [];
      Object.values(result.detections).forEach(detections => {
        allDetections.push(...detections);
      });
      setAllDetections(allDetections);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run test analysis');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Debug</h1>
          <p className="text-gray-600">Developer tools and debug information</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-600">
            {isConnected ? 'Live' : 'Disconnected'}
          </span>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Debug Controls */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Debug Controls</h2>
        <div className="flex space-x-4">
          <button
            onClick={testAnalysis}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <Activity className="h-4 w-4 mr-2" />
            Test Analysis
          </button>
          <button
            onClick={loadDebugInfo}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            <Database className="h-4 w-4 mr-2" />
            Refresh Debug Info
          </button>
        </div>
      </div>

      {/* Debug Information */}
      {debugInfo && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pipeline Status */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <Cpu className="h-5 w-5 mr-2" />
              Pipeline Status
            </h2>
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium">Status:</span> 
                <span className={`ml-2 px-2 py-1 rounded text-xs ${
                  debugInfo.status.pipeline_info.is_running ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {debugInfo.status.pipeline_info.is_running ? 'Running' : 'Stopped'}
                </span>
              </div>
              <div>
                <span className="font-medium">FPS:</span> {debugInfo.status.pipeline_info.config.fps}
              </div>
              <div>
                <span className="font-medium">Confidence Threshold:</span> {debugInfo.status.pipeline_info.config.confidence_threshold}
              </div>
              <div>
                <span className="font-medium">Enabled Classifiers:</span> {debugInfo.status.pipeline_info.config.enabled_classifiers.join(', ')}
              </div>
              <div>
                <span className="font-medium">Frame Count:</span> {debugInfo.status.pipeline_info.frame_count}
              </div>
              <div>
                <span className="font-medium">Depth Camera:</span> {debugInfo.status.pipeline_info.depth_camera_available ? 'Available' : 'Not Available'}
              </div>
            </div>
          </div>

          {/* Classifier Stats */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <Database className="h-5 w-5 mr-2" />
              Classifier Statistics
            </h2>
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium">Total Classifiers:</span> {debugInfo.classifierStats.registry_stats.total_classifiers}
              </div>
              <div>
                <span className="font-medium">Enabled Classifiers:</span> {debugInfo.classifierStats.registry_stats.enabled_classifiers}
              </div>
              <div>
                <span className="font-medium">Available Types:</span> {debugInfo.classifierStats.registry_stats.available_types.join(', ')}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Live Detections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Live Detections</h2>
          <DetectionView 
            detections={allDetections}
            frameWidth={640}
            frameHeight={480}
          />
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <VideoFeed 
            autoRefresh={isConnected}
            refreshInterval={200}
          />
        </div>
      </div>

      {/* Latest Result JSON */}
      {latestResult && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Latest Result (JSON)</h2>
          <pre className="bg-gray-100 p-4 rounded text-xs overflow-auto max-h-96">
            {JSON.stringify(latestResult, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default Debug;
