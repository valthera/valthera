import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { 
  ArrowLeft, 
  Copy, 
  TestTube, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  Video,
  ExternalLink
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { api, type Endpoint } from '../lib/api';
import { useTheme } from '../contexts/ThemeContext';

export function EndpointsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [testingEndpoint, setTestingEndpoint] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ prediction: string; confidence: number } | null>(null);
  const [testFile, setTestFile] = useState<File | null>(null);
  const { theme } = useTheme();

  useEffect(() => {
    if (projectId) {
      loadEndpoints();
    }
  }, [projectId]);

  const loadEndpoints = async () => {
    if (!projectId) return;
    
    try {
      const data = await api.getEndpoints(projectId);
      setEndpoints(data);
    } catch (error) {
      console.error('Failed to load endpoints:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const testEndpoint = async (endpointId: string) => {
    if (!testFile) return;
    
    try {
      setTestingEndpoint(endpointId);
      const result = await api.testEndpoint(endpointId, testFile);
      setTestResult(result);
    } catch (error) {
      console.error('Failed to test endpoint:', error);
    } finally {
      setTestingEndpoint(null);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.mkv']
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles[0]) {
        setTestFile(acceptedFiles[0]);
        setTestResult(null);
      }
    }
  });

  const getStatusInfo = (status: Endpoint['status']) => {
    switch (status) {
      case 'ready':
        return {
          label: 'Ready',
          color: 'bg-green-100 text-green-800',
          icon: CheckCircle
        };
      case 'training':
        return {
          label: 'Training',
          color: 'bg-yellow-100 text-yellow-800',
          icon: Clock
        };
      case 'failed':
        return {
          label: 'Failed',
          color: 'bg-red-100 text-red-800',
          icon: AlertCircle
        };
      default:
        return {
          label: 'Unknown',
          color: 'bg-gray-100 text-gray-800',
          icon: Clock
        };
    }
  };

  const generateCurlExample = (endpoint: Endpoint) => {
    return `curl -X POST "${endpoint.url}" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: multipart/form-data" \\
  -F "video=@path/to/your/video.mp4"`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading endpoints...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/projects/${projectId}/training`)}
            className="text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Training
          </Button>
          <div>
            <h1 className={`
              text-3xl font-bold
              ${theme === 'dark' ? 'text-white' : 'text-black'}
            `}>
              API Endpoints
            </h1>
            <p className={`
              mt-1 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}
            `}>
              Use these endpoints to classify robot behaviors in your applications
            </p>
          </div>
        </div>
      </div>

      {/* Endpoints Table */}
      {endpoints.length === 0 ? (
        <Card className="border border-gray-200">
          <CardContent className="text-center py-12">
            <Clock className="mx-auto h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No endpoints available</h3>
            <p className="text-gray-600 mb-4">
              Complete training to generate API endpoints for your behaviors
            </p>
            <Button
              onClick={() => navigate(`/projects/${projectId}/training`)}
              variant="outline"
            >
              Start Training
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card className="border border-gray-200">
          <CardHeader>
            <CardTitle>Available Endpoints</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Classifier</TableHead>
                  <TableHead>Accuracy</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Endpoint URL</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {endpoints.map((endpoint) => {
                  const statusInfo = getStatusInfo(endpoint.status);
                  const StatusIcon = statusInfo.icon;
                  
                  return (
                    <TableRow key={endpoint.id}>
                      <TableCell className="font-medium">
                        {endpoint.classifierName}
                      </TableCell>
                      <TableCell>
                        {endpoint.status === 'ready' && (
                          <span className="font-medium text-green-600">
                            {endpoint.accuracy.toFixed(1)}%
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge className={statusInfo.color}>
                          <StatusIcon className="mr-1 h-3 w-3" />
                          {statusInfo.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2 max-w-xs">
                          <code className="text-xs bg-gray-100 px-2 py-1 rounded truncate">
                            {endpoint.url}
                          </code>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => copyToClipboard(endpoint.url)}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          {endpoint.status === 'ready' && (
                            <Dialog>
                              <DialogTrigger asChild>
                                <Button size="sm" variant="outline">
                                  <TestTube className="mr-1 h-3 w-3" />
                                  Test
                                </Button>
                              </DialogTrigger>
                              <DialogContent className="sm:max-w-md">
                                <DialogHeader>
                                  <DialogTitle>Test Endpoint</DialogTitle>
                                  <DialogDescription>
                                    Upload a video to test the {endpoint.classifierName} classifier
                                  </DialogDescription>
                                </DialogHeader>
                                
                                <div className="space-y-4">
                                  {/* File Upload */}
                                  <div
                                    {...getRootProps()}
                                    className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                                      isDragActive 
                                        ? 'border-foreground bg-accent' 
                                        : 'border-input hover:border-border'
                                    }`}
                                  >
                                    <input {...getInputProps()} />
                                    <Video className="mx-auto h-12 w-12 text-muted-foreground mb-2" />
                                    {isDragActive ? (
                                      <p className="text-sm text-muted-foreground">Drop the video here...</p>
                                    ) : (
                                      <div>
                                        <p className="text-sm text-muted-foreground mb-1">
                                          Drag & drop a video file, or click to select
                                        </p>
                                        <p className="text-xs text-muted-foreground">
                                          MP4, AVI, MOV, MKV supported
                                        </p>
                                      </div>
                                    )}
                                  </div>

                                  {testFile && (
                                    <div className="text-sm text-muted-foreground">
                                      Selected: {testFile.name}
                                    </div>
                                  )}

                                  {/* Test Button */}
                                  <Button
                                    onClick={() => testEndpoint(endpoint.id)}
                                    disabled={!testFile || testingEndpoint === endpoint.id}
                                    className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
                                  >
                                    {testingEndpoint === endpoint.id ? 'Testing...' : 'Test Classifier'}
                                  </Button>

                                  {/* Results */}
                                  {testResult && (
                                    <div className="mt-4 p-4 bg-accent rounded-lg">
                                      <h4 className="font-medium text-foreground mb-2">Prediction Result:</h4>
                                      <div className="space-y-1">
                                        <div className="flex justify-between">
                                          <span className="text-sm text-muted-foreground">Prediction:</span>
                                          <span className="text-sm font-medium">{testResult.prediction}</span>
                                        </div>
                                        <div className="flex justify-between">
                                          <span className="text-sm text-muted-foreground">Confidence:</span>
                                          <span className="text-sm font-medium">
                                            {(testResult.confidence * 100).toFixed(1)}%
                                          </span>
                                        </div>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </DialogContent>
                            </Dialog>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Usage Examples */}
      {endpoints.length > 0 && (
        <Card className="border">
          <CardHeader>
            <CardTitle className="flex items-center">
              <ExternalLink className="mr-2 h-5 w-5" />
              Integration Examples
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-medium text-foreground mb-2">cURL Example</h4>
              <div className={`
                p-4 rounded-lg font-mono text-sm overflow-x-auto
                ${theme === 'dark' 
                  ? 'bg-gray-800 text-green-400 border border-gray-600' 
                  : 'bg-black text-green-400'
                }
              `}>
                <pre>{generateCurlExample(endpoints[0])}</pre>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-foreground mb-2">Python Example</h4>
              <div className={`
                p-4 rounded-lg font-mono text-sm overflow-x-auto
                ${theme === 'dark' 
                  ? 'bg-gray-800 text-green-400 border border-gray-600' 
                  : 'bg-black text-green-400'
                }
              `}>
                <pre>{`import requests`}</pre>
              </div>
            </div>

            <div className="bg-blue-50 dark:bg-blue-950/20 p-4 rounded-lg">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                <strong>Need an API key?</strong> Visit the{' '}
                <Button
                  variant="link"
                  className="p-0 h-auto text-blue-800 dark:text-blue-200 underline"
                  onClick={() => navigate('/api-keys')}
                >
                  API Keys page
                </Button>{' '}
                to generate and manage your authentication tokens.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}