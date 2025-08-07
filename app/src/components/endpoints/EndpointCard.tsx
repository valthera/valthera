import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../ui/dialog';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Copy, Globe, Activity, AlertCircle, Loader2, Settings, TestTube } from 'lucide-react';
import { api, type APIEndpoint } from '../../lib/api';
import { handleApiError } from '../../lib/errors';

interface EndpointCardProps {
  endpoint: APIEndpoint;
  onTest?: (result: { prediction: string; confidence: number }) => void;
}

export function EndpointCard({ endpoint, onTest }: EndpointCardProps) {
  const [isTestModalOpen, setIsTestModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testError, setTestError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ prediction: string; confidence: number } | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const getStatusColor = (status: APIEndpoint['status']) => {
    switch (status) {
      case 'ready': return 'bg-green-100 text-green-800';
      case 'training': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: APIEndpoint['status']) => {
    switch (status) {
      case 'ready':
        return <Globe className="h-4 w-4" />;
      case 'training':
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Globe className="h-4 w-4" />;
    }
  };

  const handleTestEndpoint = async () => {
    if (!selectedFile) {
      setTestError('Please select a video file to test');
      return;
    }

    try {
      setTesting(true);
      setTestError(null);
      setTestResult(null);

      const result = await api.endpoints.classify(endpoint.id, selectedFile);
      setTestResult(result);
      
      if (onTest) {
        onTest(result);
      }
    } catch (error) {
      const apiError = handleApiError(error);
      setTestError(apiError.message);
      console.error('Test error:', error);
    } finally {
      setTesting(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatUsageMetrics = (metrics: APIEndpoint['usageMetrics']) => {
    return {
      totalCalls: metrics.totalCalls.toLocaleString(),
      lastUsed: metrics.lastUsed ? formatDate(metrics.lastUsed) : 'Never',
      errorRate: `${(metrics.errorRate * 100).toFixed(1)}%`
    };
  };

  const metrics = formatUsageMetrics(endpoint.usageMetrics);

  return (
    <>
      <Card className="border border-gray-200 hover:border-gray-300 transition-colors">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getStatusIcon(endpoint.status)}
              <div>
                <CardTitle className="text-lg">{endpoint.classifierName}</CardTitle>
                <CardDescription>
                  Created {formatDate(endpoint.createdAt)}
                </CardDescription>
              </div>
            </div>
            <Badge className={getStatusColor(endpoint.status)}>
              {endpoint.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Accuracy */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Accuracy</span>
              <span className="font-medium">{(endpoint.accuracy * 100).toFixed(1)}%</span>
            </div>

            {/* Usage Metrics */}
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Total Calls</span>
                <div className="font-medium">{metrics.totalCalls}</div>
              </div>
              <div>
                <span className="text-gray-500">Last Used</span>
                <div className="font-medium">{metrics.lastUsed}</div>
              </div>
              <div>
                <span className="text-gray-500">Error Rate</span>
                <div className="font-medium">{metrics.errorRate}</div>
              </div>
            </div>

            {/* API URL */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">API Endpoint</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(endpoint.url)}
                >
                  <Copy className="h-3 w-3" />
                </Button>
              </div>
              <div className="bg-gray-100 p-2 rounded text-xs font-mono break-all">
                {endpoint.url}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() => setIsTestModalOpen(true)}
                disabled={endpoint.status !== 'ready'}
              >
                <TestTube className="mr-1 h-3 w-3" />
                Test
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsSettingsModalOpen(true)}
              >
                <Settings className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Test Modal */}
      <Dialog open={isTestModalOpen} onOpenChange={setIsTestModalOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Test Endpoint</DialogTitle>
            <DialogDescription>
              Upload a video file to test the classification endpoint.
            </DialogDescription>
          </DialogHeader>
          
          {testError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{testError}</AlertDescription>
            </Alert>
          )}
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="video-file">Video File</Label>
              <Input
                id="video-file"
                type="file"
                accept="video/*,.mp4,.avi,.mov,.mkv"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              />
              <p className="text-xs text-gray-500">
                Supported formats: MP4, AVI, MOV, MKV
              </p>
            </div>

            {testResult && (
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <h4 className="font-medium text-green-800 mb-2">Test Result</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-green-700">Prediction:</span>
                    <span className="font-medium text-green-800">{testResult.prediction}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-green-700">Confidence:</span>
                    <span className="font-medium text-green-800">
                      {(testResult.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end space-x-2">
            <Button
              variant="outline"
              onClick={() => setIsTestModalOpen(false)}
              disabled={testing}
            >
              Cancel
            </Button>
            <Button
              onClick={handleTestEndpoint}
              disabled={!selectedFile || testing}
              className="bg-black text-white hover:bg-gray-800"
            >
              {testing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Testing...
                </>
              ) : (
                'Test Endpoint'
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Settings Modal */}
      <Dialog open={isSettingsModalOpen} onOpenChange={setIsSettingsModalOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Endpoint Settings</DialogTitle>
            <DialogDescription>
              Configure endpoint parameters and monitoring.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="endpoint-name">Endpoint Name</Label>
              <Input
                id="endpoint-name"
                value={endpoint.classifierName}
                readOnly
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="endpoint-url">API URL</Label>
              <Input
                id="endpoint-url"
                value={endpoint.url}
                readOnly
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="accuracy">Accuracy</Label>
                <Input
                  id="accuracy"
                  value={`${(endpoint.accuracy * 100).toFixed(1)}%`}
                  readOnly
                />
              </div>
              <div>
                <Label htmlFor="status">Status</Label>
                <Input
                  id="status"
                  value={endpoint.status}
                  readOnly
                />
              </div>
            </div>

            <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
              <div className="flex items-center text-sm text-blue-800 mb-2">
                <Activity className="h-4 w-4 mr-2" />
                <span className="font-medium">Usage Analytics</span>
              </div>
              <div className="grid grid-cols-3 gap-4 text-xs">
                <div>
                  <span className="text-blue-700">Total Calls:</span>
                  <div className="font-medium">{metrics.totalCalls}</div>
                </div>
                <div>
                  <span className="text-blue-700">Last Used:</span>
                  <div className="font-medium">{metrics.lastUsed}</div>
                </div>
                <div>
                  <span className="text-blue-700">Error Rate:</span>
                  <div className="font-medium">{metrics.errorRate}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-2">
            <Button
              variant="outline"
              onClick={() => setIsSettingsModalOpen(false)}
            >
              Close
            </Button>
            <Button
              variant="destructive"
              onClick={() => {/* TODO: Delete endpoint */}}
            >
              Delete Endpoint
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
} 