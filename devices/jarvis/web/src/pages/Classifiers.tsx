import React, { useState, useEffect } from 'react';
import { BarChart3, Play, Pause, RotateCcw, Settings } from 'lucide-react';
import JarvisApiClient from '../services/api';
import { ClassifierInfo } from '../types/api';

const Classifiers: React.FC = () => {
  const [classifiers, setClassifiers] = useState<ClassifierInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  const apiClient = new JarvisApiClient();

  useEffect(() => {
    loadClassifiers();
  }, []);

  const loadClassifiers = async () => {
    try {
      setLoading(true);
      const response = await apiClient.listClassifiers();
      setClassifiers(response.classifiers);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load classifiers');
    } finally {
      setLoading(false);
    }
  };

  const toggleClassifier = async (name: string, enabled: boolean) => {
    try {
      if (enabled) {
        await apiClient.enableClassifier(name);
      } else {
        await apiClient.disableClassifier(name);
      }
      loadClassifiers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle classifier');
    }
  };

  const initializeClassifier = async (name: string) => {
    try {
      await apiClient.initializeClassifier(name);
      loadClassifiers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize classifier');
    }
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
          <h1 className="text-2xl font-bold text-gray-900">Classifiers</h1>
          <p className="text-gray-600">Manage and configure AI classifiers</p>
        </div>
        <button
          onClick={loadClassifiers}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          <RotateCcw className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {classifiers.map((classifier) => (
          <div key={classifier.name} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <BarChart3 className="h-6 w-6 text-blue-600 mr-2" />
                <h3 className="text-lg font-semibold capitalize">{classifier.name}</h3>
              </div>
              <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                classifier.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {classifier.enabled ? 'Enabled' : 'Disabled'}
              </div>
            </div>

            <div className="space-y-2 text-sm text-gray-600 mb-4">
              <div>
                <span className="font-medium">Type:</span> {classifier.type}
              </div>
              <div>
                <span className="font-medium">Initialized:</span> {classifier.initialized ? 'Yes' : 'No'}
              </div>
              <div>
                <span className="font-medium">Total Detections:</span> {classifier.stats.total_detections}
              </div>
              <div>
                <span className="font-medium">Avg Processing Time:</span> {classifier.stats.average_processing_time_ms.toFixed(2)}ms
              </div>
            </div>

            <div className="flex space-x-2">
              <button
                onClick={() => toggleClassifier(classifier.name, !classifier.enabled)}
                className={`flex-1 flex items-center justify-center px-3 py-2 rounded text-sm font-medium ${
                  classifier.enabled
                    ? 'bg-red-100 text-red-700 hover:bg-red-200'
                    : 'bg-green-100 text-green-700 hover:bg-green-200'
                }`}
              >
                {classifier.enabled ? (
                  <>
                    <Pause className="h-4 w-4 mr-1" />
                    Disable
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-1" />
                    Enable
                  </>
                )}
              </button>

              {!classifier.initialized && (
                <button
                  onClick={() => initializeClassifier(classifier.name)}
                  className="flex items-center px-3 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm font-medium"
                >
                  <Settings className="h-4 w-4 mr-1" />
                  Init
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {classifiers.length === 0 && (
        <div className="text-center py-12">
          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Classifiers Found</h3>
          <p className="text-gray-600">No classifiers are currently available.</p>
        </div>
      )}
    </div>
  );
};

export default Classifiers;
