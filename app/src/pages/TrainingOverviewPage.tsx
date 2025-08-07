import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Zap, Plus, ArrowRight, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '../lib/api';

// Training jobs overview
interface TrainingJobSummary {
  id: string;
  projectId: string;
  projectName: string;
  status: 'preprocessing' | 'training' | 'validating' | 'completed' | 'failed';
  progress: number;
  startedAt: string;
  behaviorCount: number;
}

export function TrainingOverviewPage() {
  const [trainingJobs, setTrainingJobs] = useState<TrainingJobSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Fetch all projects and their training jobs
      const projectsData = await api.getProjects();
      const allTrainingJobs: TrainingJobSummary[] = [];
      
      // Get training jobs for each project
      for (const project of projectsData) {
        try {
          const trainingJobs = await api.training.list(project.id);
          const projectTrainingJobs: TrainingJobSummary[] = trainingJobs.map(job => ({
            id: job.id,
            projectId: project.id,
            projectName: project.name,
            status: job.status,
            progress: job.progress,
            startedAt: job.startedAt,
            behaviorCount: 0 // This would need to be fetched separately if needed
          }));
          allTrainingJobs.push(...projectTrainingJobs);
        } catch (error) {
          console.error(`Failed to load training jobs for project ${project.id}:`, error);
        }
      }
      
      setTrainingJobs(allTrainingJobs);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusInfo = (status: TrainingJobSummary['status']) => {
    switch (status) {
      case 'preprocessing':
        return { label: 'Preprocessing', color: 'bg-blue-100 text-blue-800', icon: Clock };
      case 'training':
        return { label: 'Training', color: 'bg-yellow-100 text-yellow-800', icon: Zap };
      case 'validating':
        return { label: 'Validating', color: 'bg-purple-100 text-purple-800', icon: CheckCircle };
      case 'completed':
        return { label: 'Completed', color: 'bg-green-100 text-green-800', icon: CheckCircle };
      case 'failed':
        return { label: 'Failed', color: 'bg-red-100 text-red-800', icon: AlertCircle };
      default:
        return { label: 'Unknown', color: 'bg-gray-100 text-gray-800', icon: Clock };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading training overview...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-black">Training</h1>
          <p className="text-gray-600 mt-1">
            Monitor all training jobs across your projects
          </p>
        </div>
        
        <Button asChild className="bg-black text-white hover:bg-gray-800">
          <Link to="/dashboard">
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Link>
        </Button>
      </div>

      {/* Training Overview */}
      {trainingJobs.length === 0 ? (
        <Card className="border border-gray-200">
          <CardContent className="text-center py-12">
            <Zap className="mx-auto h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No training jobs yet</h3>
            <p className="text-gray-600 mb-6">
              Create a project, define behaviors, and start training to see jobs here
            </p>
            
            <div className="space-y-4">
              <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
                <span className="flex items-center">
                  <span className="w-6 h-6 rounded-full bg-gray-200 text-xs flex items-center justify-center mr-2">1</span>
                  Create Project
                </span>
                <ArrowRight className="h-4 w-4" />
                <span className="flex items-center">
                  <span className="w-6 h-6 rounded-full bg-gray-200 text-xs flex items-center justify-center mr-2">2</span>
                  Define Behaviors
                </span>
                <ArrowRight className="h-4 w-4" />
                <span className="flex items-center">
                  <span className="w-6 h-6 rounded-full bg-gray-200 text-xs flex items-center justify-center mr-2">3</span>
                  Start Training
                </span>
              </div>
              
              <Button asChild className="bg-black text-white hover:bg-gray-800">
                <Link to="/dashboard">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Your First Project
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="border border-gray-200">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-black">{trainingJobs.length}</div>
                <div className="text-sm text-gray-600">Total Jobs</div>
              </CardContent>
            </Card>
            <Card className="border border-gray-200">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-black">
                  {trainingJobs.filter(j => ['preprocessing', 'training', 'validating'].includes(j.status)).length}
                </div>
                <div className="text-sm text-gray-600">In Progress</div>
              </CardContent>
            </Card>
            <Card className="border border-gray-200">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-black">
                  {trainingJobs.filter(j => j.status === 'completed').length}
                </div>
                <div className="text-sm text-gray-600">Completed</div>
              </CardContent>
            </Card>
            <Card className="border border-gray-200">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-black">
                  {trainingJobs.filter(j => j.status === 'failed').length}
                </div>
                <div className="text-sm text-gray-600">Failed</div>
              </CardContent>
            </Card>
          </div>

          {/* Training Jobs List */}
          <Card className="border border-gray-200">
            <CardHeader>
              <CardTitle>Recent Training Jobs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {trainingJobs
                  .sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime())
                  .map((job) => {
                    const statusInfo = getStatusInfo(job.status);
                    const StatusIcon = statusInfo.icon;
                    
                    return (
                      <div key={job.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div className="flex items-center space-x-4">
                          <StatusIcon className="h-5 w-5 text-gray-600" />
                          <div>
                            <div className="font-medium text-black">{job.projectName}</div>
                            <div className="text-sm text-gray-600">
                              {job.behaviorCount} behaviors • Started {new Date(job.startedAt).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-4">
                          {job.status !== 'completed' && job.status !== 'failed' && (
                            <div className="w-32">
                              <Progress value={job.progress} className="h-2" />
                              <div className="text-xs text-gray-500 mt-1">{job.progress}%</div>
                            </div>
                          )}
                          
                          <Badge className={statusInfo.color}>
                            {statusInfo.label}
                          </Badge>
                          
                          <Button
                            asChild
                            variant="outline"
                            size="sm"
                          >
                            <Link to={`/projects/${job.projectId}/training`}>
                              View Details
                            </Link>
                          </Button>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}