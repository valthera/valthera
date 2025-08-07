import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Target, Plus, ArrowRight } from 'lucide-react';
import { api, type Project, type Endpoint } from '../lib/api';

export function ClassifiersPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const projectsData = await api.getProjects();
      
      // Load endpoints for all projects
      const allEndpoints: Endpoint[] = [];
      for (const project of projectsData) {
        const projectEndpoints = await api.getEndpoints(project.id);
        allEndpoints.push(...projectEndpoints);
      }
      
      setProjects(projectsData);
      setEndpoints(allEndpoints);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'bg-green-100 text-green-800';
      case 'training': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading classifiers...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-black">Classifiers</h1>
          <p className="text-gray-600 mt-1">
            Manage all your trained behavior classifiers across projects
          </p>
        </div>
        
        <Button asChild className="bg-black text-white hover:bg-gray-800">
          <Link to="/dashboard">
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Link>
        </Button>
      </div>

      {/* Classifiers Overview */}
      {endpoints.length === 0 ? (
        <Card className="border border-gray-200">
          <CardContent className="text-center py-12">
            <Target className="mx-auto h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No classifiers yet</h3>
            <p className="text-gray-600 mb-6">
              Create a project and train behaviors to generate classifiers
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
                  Train Models
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="border border-gray-200">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-black">{endpoints.length}</div>
                <div className="text-sm text-gray-600">Total Classifiers</div>
              </CardContent>
            </Card>
            <Card className="border border-gray-200">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-black">
                  {endpoints.filter(e => e.status === 'ready').length}
                </div>
                <div className="text-sm text-gray-600">Ready for Use</div>
              </CardContent>
            </Card>
            <Card className="border border-gray-200">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-black">
                  {endpoints.filter(e => e.status === 'ready').reduce((sum, e) => sum + e.accuracy, 0) / 
                   endpoints.filter(e => e.status === 'ready').length || 0}%
                </div>
                <div className="text-sm text-gray-600">Average Accuracy</div>
              </CardContent>
            </Card>
          </div>

          {/* Classifiers Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {endpoints.map((endpoint) => {
              const project = projects.find(p => p.id === endpoint.projectId);
              
              return (
                <Card key={endpoint.id} className="border border-gray-200 hover:border-gray-300 transition-colors">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg text-black">
                        {endpoint.classifierName}
                      </CardTitle>
                      <Badge className={getStatusColor(endpoint.status)}>
                        {endpoint.status}
                      </Badge>
                    </div>
                    <div className="text-sm text-gray-600">
                      Project: {project?.name}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {endpoint.status === 'ready' && (
                        <div className="text-sm">
                          <span className="text-gray-600">Accuracy: </span>
                          <span className="font-medium text-green-600">
                            {endpoint.accuracy.toFixed(1)}%
                          </span>
                        </div>
                      )}
                      
                      <div className="text-sm text-gray-600">
                        Created {new Date(endpoint.createdAt).toLocaleDateString()}
                      </div>

                      <Button
                        asChild
                        variant="outline"
                        className="w-full"
                        disabled={endpoint.status !== 'ready'}
                      >
                        <Link to={`/projects/${endpoint.projectId}/endpoints`}>
                          View Details
                        </Link>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}