import React, { useState, useEffect } from 'react';
import { Camera, RefreshCw, Download } from 'lucide-react';
import JarvisApiClient from '../services/api';

interface VideoFeedProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const VideoFeed: React.FC<VideoFeedProps> = ({ 
  autoRefresh = true, 
  refreshInterval = 200 
}) => {
  const [annotatedFrameUrl, setAnnotatedFrameUrl] = useState<string>('');
  const [rawFrameUrl, setRawFrameUrl] = useState<string>('');
  const [depthMapUrl, setDepthMapUrl] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const apiClient = new JarvisApiClient();

  const refreshFrame = async (type: 'annotated' | 'raw' | 'depth' = 'annotated') => {
    try {
      setIsLoading(true);
      setError('');

      let url: string;
      switch (type) {
        case 'annotated':
          url = await apiClient.getAnnotatedFrame();
          setAnnotatedFrameUrl(url);
          break;
        case 'raw':
          url = await apiClient.getRawFrame();
          setRawFrameUrl(url);
          break;
        case 'depth':
          url = await apiClient.getDepthMap();
          setDepthMapUrl(url);
          break;
      }

      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load frame');
      console.error('Error refreshing frame:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const downloadFrame = (type: 'annotated' | 'raw' | 'depth') => {
    const url = type === 'annotated' ? annotatedFrameUrl : 
                type === 'raw' ? rawFrameUrl : depthMapUrl;
    
    if (url) {
      const link = document.createElement('a');
      link.href = url;
      link.download = `frame_${type}_${Date.now()}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  useEffect(() => {
    // Initial load
    refreshFrame('annotated');

    // Auto-refresh
    if (autoRefresh) {
      const interval = setInterval(() => {
        refreshFrame('annotated');
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Camera className="h-5 w-5 text-gray-600" />
          <h2 className="text-lg font-semibold">Video Feed</h2>
          {lastUpdate && (
            <span className="text-sm text-gray-500">
              Last update: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => refreshFrame('annotated')}
            disabled={isLoading}
            className="flex items-center px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          
          <button
            onClick={() => downloadFrame('annotated')}
            disabled={!annotatedFrameUrl}
            className="flex items-center px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          >
            <Download className="h-4 w-4 mr-1" />
            Download
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Frame Display */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Annotated Frame */}
        <div className="video-container">
          <h3 className="text-sm font-medium text-white mb-2 p-2">Annotated Frame</h3>
          {annotatedFrameUrl ? (
            <img
              src={annotatedFrameUrl}
              alt="Annotated frame"
              className="w-full h-auto"
              onError={() => setError('Failed to load annotated frame')}
            />
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-400">
              {isLoading ? 'Loading...' : 'No frame available'}
            </div>
          )}
        </div>

        {/* Raw Frame */}
        <div className="video-container">
          <h3 className="text-sm font-medium text-white mb-2 p-2">Raw Frame</h3>
          {rawFrameUrl ? (
            <img
              src={rawFrameUrl}
              alt="Raw frame"
              className="w-full h-auto"
              onError={() => setError('Failed to load raw frame')}
            />
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-400">
              <button
                onClick={() => refreshFrame('raw')}
                className="text-blue-400 hover:text-blue-300"
              >
                Load Raw Frame
              </button>
            </div>
          )}
        </div>

        {/* Depth Map */}
        <div className="video-container">
          <h3 className="text-sm font-medium text-white mb-2 p-2">Depth Map</h3>
          {depthMapUrl ? (
            <img
              src={depthMapUrl}
              alt="Depth map"
              className="w-full h-auto"
              onError={() => setError('Failed to load depth map')}
            />
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-400">
              <button
                onClick={() => refreshFrame('depth')}
                className="text-blue-400 hover:text-blue-300"
              >
                Load Depth Map
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VideoFeed;
