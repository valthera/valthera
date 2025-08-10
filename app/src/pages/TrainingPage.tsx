import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../components/ui/collapsible';
import { Badge } from '../components/ui/badge';
import { 
  ArrowLeft, 
  Play, 
  Square, 
  ChevronDown, 
  ChevronRight, 
  AlertCircle, 
  CheckCircle, 
  Clock,
  Zap
} from 'lucide-react';
import { api, type TrainingJob } from '../lib/api';

export function TrainingPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  
  const [trainingJob, setTrainingJob] = useState<TrainingJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [showLogs, setShowLogs] = useState(false);

  // Auto-refresh training status
  useEffect(() => {
    let interval: number;
    
    if (trainingJob && !['completed', 'failed'].includes(trainingJob.status)) {
      interval = setInterval(async () => {
        try {
          const updatedJob = await api.getTrainingStatus(trainingJob.id);
          setTrainingJob(updatedJob);
          
          // Stop polling when training is complete
          if (['completed', 'failed'].includes(updatedJob.status)) {
            clearInterval(interval);
          }
        } catch (error) {
          console.error('Failed to update training status:', error);
        }
      }, 2000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [trainingJob]);

  const startTraining = async () => {
    if (!projectId) return;
    
    try {
      setLoading(true);
      const job = await api.startTraining(projectId);
      setTrainingJob(job);
    } catch (error) {
      console.error('Failed to start training:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusInfo = (status: TrainingJob['status']) => {
    switch (status) {
      case 'preprocessing':
        return {
          label: 'Preprocessing',
          description: 'Preparing video data and extracting VJEPA2 embeddings',
          color: 'bg-blue-100 dark:bg-blue-950/20 text-blue-800 dark:text-blue-200',
          icon: Clock
        };
      case 'training':
        return {
          label: 'Training',
          description: 'Training classifier model on behavior data',
          color: 'bg-yellow-100 dark:bg-yellow-950/20 text-yellow-800 dark:text-yellow-200',
          icon: Zap
        };
      case 'validating':
        return {
          label: 'Validating',
          description: 'Testing model accuracy and performance',
          color: 'bg-purple-100 dark:bg-purple-950/20 text-purple-800 dark:text-purple-200',
          icon: CheckCircle
        };
      case 'completed':
        return {
          label: 'Completed',
          description: 'Training finished successfully',
          color: 'bg-green-100 dark:bg-green-950/20 text-green-800 dark:text-green-200',
          icon: CheckCircle
        };
      case 'failed':
        return {
          label: 'Failed',
          description: 'Training encountered an error',
          color: 'bg-red-100 dark:bg-red-950/20 text-red-800 dark:text-red-200',
          icon: AlertCircle
        };
      default:
        return {
          label: 'Unknown',
          description: '',
          color: 'bg-muted text-muted-foreground',
          icon: Clock
        };
    }
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000);
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  const statusInfo = trainingJob ? getStatusInfo(trainingJob.status) : null;
  const StatusIcon = statusInfo?.icon;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/projects/${projectId}/behaviors`)}
            className="text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Behaviors
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-foreground">Training</h1>
            <p className="text-muted-foreground mt-1">
              Train your robot behavior classifier using VJEPA2 embeddings
            </p>
          </div>
        </div>

        {trainingJob?.status === 'completed' && (
          <Button
            onClick={() => navigate(`/projects/${projectId}/endpoints`)}
            className="bg-primary text-primary-foreground hover:bg-primary/90"
          >
            View Endpoints
          </Button>
        )}
      </div>

      {/* Training Status */}
      {!trainingJob ? (
        <Card className="border">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Play className="mr-2 h-5 w-5" />
              Start Training
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              Ready to train your behavior classifier. This will process all uploaded video samples 
              using VJEPA2 embeddings and create a classifier for each defined behavior.
            </p>
            
            <div className="bg-muted/30 p-4 rounded-lg">
              <h4 className="font-medium text-foreground mb-2">Training Process:</h4>
              <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
                <li>Preprocess video data and extract VJEPA2 embeddings</li>
                <li>Train classifier models for each behavior</li>
                <li>Validate model accuracy and performance</li>
                <li>Generate API endpoints for inference</li>
              </ol>
            </div>

            <Button
              onClick={startTraining}
              disabled={loading}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {loading ? 'Starting...' : 'Start Training'}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card className="border">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center">
                {StatusIcon && <StatusIcon className="mr-2 h-5 w-5" />}
                Training Job #{trainingJob.id}
              </div>
              {statusInfo && (
                <Badge className={statusInfo.color}>
                  {statusInfo.label}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Progress */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  {statusInfo?.description}
                </span>
                <span className="font-medium">{trainingJob.progress}%</span>
              </div>
              <Progress value={trainingJob.progress} className="h-3" />
            </div>

            {/* Timing Info */}
            <div className="flex items-center space-x-6 text-sm text-muted-foreground">
              <div>
                <span className="font-medium">Started:</span>{' '}
                {new Date(trainingJob.startedAt).toLocaleString()}
              </div>
              <div>
                <span className="font-medium">Duration:</span>{' '}
                {formatDuration(trainingJob.startedAt, trainingJob.completedAt)}
              </div>
            </div>

            {/* Logs */}
            <Collapsible open={showLogs} onOpenChange={setShowLogs}>
              <CollapsibleTrigger asChild>
                <Button variant="outline" className="w-full justify-between">
                  <span>Training Logs</span>
                  {showLogs ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-4">
                <div className="bg-foreground text-background p-4 rounded-lg font-mono text-sm max-h-60 overflow-y-auto">
                  {trainingJob.logs.map((log, index) => (
                    <div key={index} className="mb-1">
                      <span className="text-muted-foreground">
                        [{new Date().toLocaleTimeString()}]
                      </span>{' '}
                      {log}
                    </div>
                  ))}
                  {!['completed', 'failed'].includes(trainingJob.status) && (
                    <div className="animate-pulse">▊</div>
                  )}
                </div>
              </CollapsibleContent>
            </Collapsible>

            {/* Actions */}
            <div className="flex justify-between">
              {trainingJob.status === 'completed' ? (
                <Button
                  onClick={() => navigate(`/projects/${projectId}/endpoints`)}
                  className="bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  View Endpoints
                </Button>
              ) : trainingJob.status === 'failed' ? (
                <Button
                  onClick={startTraining}
                  variant="outline"
                  disabled={loading}
                >
                  Retry Training
                </Button>
              ) : (
                <Button
                  variant="outline"
                  disabled // Cancel functionality would be implemented here
                >
                  <Square className="mr-2 h-4 w-4" />
                  Cancel Training
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Status Alerts */}
      {trainingJob?.status === 'completed' && (
        <Alert className="border-green-200 dark:border-green-800/30 bg-green-50 dark:bg-green-950/20">
          <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
          <AlertDescription className="text-green-800 dark:text-green-200">
            Training completed successfully! Your behavior classifiers are now available as API endpoints.
          </AlertDescription>
        </Alert>
      )}

      {trainingJob?.status === 'failed' && (
        <Alert className="border-red-200 dark:border-red-800/30 bg-red-50 dark:bg-red-950/20">
          <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
          <AlertDescription className="text-red-800 dark:text-red-200">
            Training failed. Please check the logs above and try again. If the issue persists, 
            contact support with your training job ID.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}