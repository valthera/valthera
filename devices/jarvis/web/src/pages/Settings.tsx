import React, { useState, useEffect } from 'react';
import { Save, RotateCcw } from 'lucide-react';
import JarvisApiClient from '../services/api';

const Settings: React.FC = () => {
  const [config, setConfig] = useState({
    fps: 10,
    confidence_threshold: 0.5,
    max_detections: 10,
    enabled_classifiers: ['person'], // Always person only
    include_depth: true,
    include_3d_position: true,
    include_annotated_frame: false,
    include_raw_frame: false
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>('');

  const apiClient = new JarvisApiClient();

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getPipelineConfig();
      setConfig(response.config);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    try {
      setSaving(true);
      await apiClient.updatePipelineConfig(config);
      setError('');
      // Show success message
      alert('Configuration saved successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Person Detection Settings</h1>
          <p className="text-gray-600">Configure person tracking pipeline</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={loadConfig}
            className="flex items-center px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </button>
          <button
            onClick={saveConfig}
            disabled={saving}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            <Save className="h-4 w-4 mr-2" />
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Processing Settings */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Person Detection Settings</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                FPS (Frames Per Second)
              </label>
              <input
                type="number"
                min="1"
                max="30"
                value={config.fps}
                onChange={(e) => handleInputChange('fps', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Confidence Threshold
              </label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={config.confidence_threshold}
                onChange={(e) => handleInputChange('confidence_threshold', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Detections
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={config.max_detections}
                onChange={(e) => handleInputChange('max_detections', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Output Settings */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Output Settings</h2>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.include_depth}
                onChange={(e) => handleInputChange('include_depth', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm font-medium text-gray-700">
                Include Depth Information
              </span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.include_3d_position}
                onChange={(e) => handleInputChange('include_3d_position', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm font-medium text-gray-700">
                Include 3D Position
              </span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.include_annotated_frame}
                onChange={(e) => handleInputChange('include_annotated_frame', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm font-medium text-gray-700">
                Include Annotated Frame
              </span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.include_raw_frame}
                onChange={(e) => handleInputChange('include_raw_frame', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm font-medium text-gray-700">
                Include Raw Frame
              </span>
            </label>
          </div>
        </div>

        {/* Pipeline Control */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Pipeline Control</h2>
          <div className="space-y-3">
            <button
              onClick={async () => {
                try {
                  await apiClient.startPipeline();
                  alert('Pipeline started successfully!');
                } catch (err) {
                  alert('Failed to start pipeline');
                }
              }}
              className="w-full flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Start Pipeline
            </button>

            <button
              onClick={async () => {
                try {
                  await apiClient.stopPipeline();
                  alert('Pipeline stopped successfully!');
                } catch (err) {
                  alert('Failed to stop pipeline');
                }
              }}
              className="w-full flex items-center justify-center px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Stop Pipeline
            </button>

            <button
              onClick={async () => {
                try {
                  await apiClient.resetPipeline();
                  alert('Pipeline reset successfully!');
                } catch (err) {
                  alert('Failed to reset pipeline');
                }
              }}
              className="w-full flex items-center justify-center px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
            >
              Reset Pipeline
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
