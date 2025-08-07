import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { Progress } from '../ui/progress';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Play, Clock, CheckCircle, XCircle, AlertCircle, Loader2, Eye, RefreshCw } from 'lucide-react';
import { api, type TrainingJob } from '../../lib/api';
import { handleApiError } from '../../lib/errors';

interface TrainingJobListProps {
  projectId: string;
}

export function TrainingJobList({ projectId }: TrainingJobListProps) {
  const [trainingJobs, setTrainingJobs] = useState<TrainingJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isStartTrainingModalOpen, setIsStartTrainingModalOpen] = useState(false);
  const [startTrainingLoading, setStartTrainingLoading] = useState(false);
  const [startTrainingError, setStartTrainingError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<TrainingJob | null>(null);
  const [isLogsModalOpen, setIsLogsModalOpen] = useState(false);

  // Form state
  const [modelType, setModelType] = useState('vjepa2');
  const [selectedDataSources, setSelectedDataSources] = useState<string[]>([]);

  useEffect(() => {
    loadTrainingJobs();
  }, [projectId]);

  const loadTrainingJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.training.list(projectId);
      setTrainingJobs(data);
    } catch (error) {
      const apiError = handleApiError(error);
      setError(apiError.message);
      console.error('Failed to load training jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartTraining = async () => {
    if (selectedDataSources.length === 0) {
      setStartTrainingError('Please select at least one data source');
      return;
    }

    try {
      setStartTrainingLoading(true);
      setStartTrainingError(null);
      
      const newJob = await api.training.create(projectId, {
        modelType,
        hyperparameters: {
          learningRate: 0.001,
          batchSize: 32,
          epochs: 100
        },
        dataSources: selectedDataSources
      });

      setTrainingJobs([newJob, ...trainingJobs]);
      
      // Reset form
      setModelType('vjepa2');
      setSelectedDataSources([]);
      setIsStartTrainingModalOpen(false);
    } catch (error) {
      const apiError = handleApiError(error);
      setStartTrainingError(apiError.message);
      console.error('Failed to start training:', error);
    } finally {
      setStartTrainingLoading(false);
    }
  };

  const getStatusColor = (status: TrainingJob['status']) => {
    switch (status) {
      case 'preprocessing': return 'bg-blue-100 text-blue-800';
      case 'training': return 'bg-yellow-100 text-yellow-800';
      case 'validating': return 'bg-purple-100 text-purple-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: TrainingJob['status']) => {
    switch (status) {
      case 'preprocessing':
      case 'training':
      case 'validating':
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4" />;
      case 'failed':
        return <XCircle className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const formatDuration = (startedAt: string, completedAt?: string) => {
    const start = new Date(startedAt);
    const end = completedAt ? new Date(completedAt) : new Date();
    const diff = end.getTime() - start.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    return `${minutes}m`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center space-x-2 text-gray-500">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading training jobs...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-black">Training Jobs</h2>
          <p className="text-gray-600 mt-1">
            Monitor and manage your model training jobs
          </p>
        </div>
        
        <Dialog open={isStartTrainingModalOpen} onOpenChange={setIsStartTrainingModalOpen}>
          <DialogTrigger asChild>
            <Button className="bg-black text-white hover:bg-gray-800">
              <Play className="mr-2 h-4 w-4" />
              Start Training
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Start New Training Job</DialogTitle>
              <DialogDescription>
                Configure and start a new training job for your project.
              </DialogDescription>
            </DialogHeader>
            
            {startTrainingError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{startTrainingError}</AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Model Type</label>
                <select
                  value={modelType}
                  onChange={(e) => setModelType(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-md"
                >
                  <option value="vjepa2">VJEPA2 (Recommended)</option>
                  <option value="custom">Custom Model</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Data Sources</label>
                <div className="space-y-2">
                  {['robot_arm_samples', 'grasping_testset', 'manipulation_demos'].map((source) => (
                    <label key={source} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={selectedDataSources.includes(source)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedDataSources([...selectedDataSources, source]);
                          } else {
                            setSelectedDataSources(selectedDataSources.filter(s => s !== source));
                          }
                        }}
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm">{source}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                <div className="flex items-center text-sm text-blue-800 mb-2">
                  <AlertCircle className="h-4 w-4 mr-2" />
                  <span className="font-medium">Training Process:</span>
                </div>
                <p className="text-xs text-blue-700">
                  1. Preprocess video data • 2. Extract embeddings • 3. Train classifier • 4. Validate accuracy
                </p>
              </div>
            </div>

            <div className="flex justify-end space-x-2">
              <Button
                variant="outline"
                onClick={() => setIsStartTrainingModalOpen(false)}
                disabled={startTrainingLoading}
              >
                Cancel
              </Button>
              <Button
                onClick={handleStartTraining}
                disabled={selectedDataSources.length === 0 || startTrainingLoading}
                className="bg-black text-white hover:bg-gray-800"
              >
                {startTrainingLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Starting...
                  </>
                ) : (
                  'Start Training'
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error}
            <Button 
              variant="link" 
              className="p-0 h-auto text-inherit underline ml-2"
              onClick={loadTrainingJobs}
            >
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Training Jobs List */}
      {trainingJobs.length === 0 && !error ? (
        <div className="text-center py-12">
          <RefreshCw className="mx-auto h-16 w-16 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No training jobs yet</h3>
          <p className="text-gray-600 mb-4">
            Start your first training job to build robot perception models
          </p>
          <Button
            onClick={() => setIsStartTrainingModalOpen(true)}
            className="bg-black text-white hover:bg-gray-800"
          >
            <Play className="mr-2 h-4 w-4" />
            Start Training
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {trainingJobs.map((job) => (
            <Card key={job.id} className="border border-gray-200">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(job.status)}
                    <div>
                      <CardTitle className="text-lg">Training Job #{job.id.slice(-6)}</CardTitle>
                      <CardDescription>
                        Started {new Date(job.startedAt).toLocaleDateString()}
                      </CardDescription>
                    </div>
                  </div>
                  <Badge className={getStatusColor(job.status)}>
                    {job.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Progress Bar */}
                  <div>
                    <div className="flex justify-between text-sm text-gray-600 mb-2">
                      <span>Progress</span>
                      <span>{job.progress}%</span>
                    </div>
                    <Progress value={job.progress} className="h-2" />
                  </div>

                  {/* Job Details */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Duration:</span>
                      <span className="ml-2 font-medium">
                        {formatDuration(job.startedAt, job.completedAt)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Model Type:</span>
                      <span className="ml-2 font-medium">
                        {job.config?.modelType || 'VJEPA2'}
                      </span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedJob(job);
                        setIsLogsModalOpen(true);
                      }}
                    >
                      <Eye className="mr-1 h-3 w-3" />
                      View Logs
                    </Button>
                    
                    {job.status === 'completed' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {/* TODO: Create endpoint */}}
                      >
                        <CheckCircle className="mr-1 h-3 w-3" />
                        Deploy Endpoint
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Logs Modal */}
      <Dialog open={isLogsModalOpen} onOpenChange={setIsLogsModalOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Training Logs</DialogTitle>
            <DialogDescription>
              Real-time logs from the training job
            </DialogDescription>
          </DialogHeader>
          
          {selectedJob && (
            <div className="max-h-96 overflow-y-auto">
              <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm">
                {selectedJob.logs.map((log, index) => (
                  <div key={index} className="mb-1">
                    <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span> {log}
                  </div>
                ))}
                {selectedJob.status === 'preprocessing' || selectedJob.status === 'training' ? (
                  <div className="text-yellow-400 animate-pulse">
                    <span className="text-gray-500">[{new Date().toLocaleTimeString()}]</span> Processing...
                  </div>
                ) : null}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
} 