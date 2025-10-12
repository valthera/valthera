import React, { useState, useEffect } from 'react';
import { Activity, Users, Eye } from 'lucide-react';
import DetectionView from '../components/DetectionView';
import VideoFeed from '../components/VideoFeed';
import JarvisWebSocketClient from '../services/websocket';
import { AnalysisResult, UnifiedDetection } from '../types/api';

const Dashboard: React.FC = () => {
  const [latestResult, setLatestResult] = useState<AnalysisResult | null>(null);
  const [allDetections, setAllDetections] = useState<UnifiedDetection[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [stats, setStats] = useState({
    totalPeople: 0,
    peopleInView: 0,
    averageConfidence: 0,
    lastUpdate: null as Date | null
  });

  const wsClient = new JarvisWebSocketClient();

  useEffect(() => {
    // Initialize WebSocket connection
    const initWebSocket = async () => {
      try {
        await wsClient.connect();
        setIsConnected(true);

        // Subscribe to person classifier only
        wsClient.subscribe(['person'], {
          confidence_threshold: 0.5,
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

          // Update stats for person tracking only
          const personDetections = allDetections.filter(d => d.classifier_type === 'person');
          const avgConfidence = personDetections.length > 0 
            ? personDetections.reduce((sum, d) => sum + d.confidence, 0) / personDetections.length 
            : 0;
          
          setStats({
            totalPeople: personDetections.length,
            peopleInView: personDetections.length,
            averageConfidence: avgConfidence,
            lastUpdate: new Date(result.timestamp * 1000)
          });
        });

      } catch (error) {
        console.error('WebSocket connection failed:', error);
        setIsConnected(false);
      }
    };

    initWebSocket();

    // Cleanup on unmount
    return () => {
      wsClient.disconnect();
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Person Tracking Dashboard</h1>
          <p className="text-gray-600">Real-time person detection and tracking</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-600">
            {isConnected ? 'Live' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Stats Cards - Person Tracking Only */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Users className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">People in View</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.peopleInView}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Activity className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Detected</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.totalPeople}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Eye className="h-8 w-8 text-orange-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Avg Confidence</p>
              <p className="text-2xl font-semibold text-gray-900">{(stats.averageConfidence * 100).toFixed(1)}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Detection View */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Live Person Detection</h2>
          <DetectionView 
            detections={allDetections.filter(d => d.classifier_type === 'person')}
            frameWidth={640}
            frameHeight={480}
          />
        </div>

        {/* Video Feed */}
        <div className="bg-white rounded-lg shadow p-6">
          <VideoFeed 
            autoRefresh={isConnected}
            refreshInterval={500}
          />
        </div>
      </div>

      {/* Latest Result Details */}
      {latestResult && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Latest Analysis Result</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="font-medium">Frame ID:</span> {latestResult.frame_id}
            </div>
            <div>
              <span className="font-medium">Processing Time:</span> {latestResult.processing_time_ms.toFixed(2)}ms
            </div>
            <div>
              <span className="font-medium">Cache Hit:</span> {latestResult.cache_hit ? 'Yes' : 'No'}
            </div>
            <div>
              <span className="font-medium">Resolution:</span> {latestResult.frame_resolution.join('x')}
            </div>
          </div>
          
          {stats.lastUpdate && (
            <div className="mt-4 text-sm text-gray-600">
              Last updated: {stats.lastUpdate.toLocaleString()}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Dashboard;
