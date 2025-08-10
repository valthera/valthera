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
      case 'active': return 'bg-green-100 text-green-800';
      case 'training': return 'bg-blue-100 text-blue-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-muted-foreground">Loading classifiers...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">Classifiers</h1>
        <p className="text-muted-foreground mt-1">
          Manage and monitor your trained classification models
        </p>
      </div>

      {/* No Classifiers State */}
      {endpoints.length === 0 ? (
        <Card className="border">
          <CardContent className="text-center py-12">
            <Target className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">No classifiers yet</h3>
            <p className="text-muted-foreground mb-6">
              Train your first classifier to start classifying videos
            </p>
            <div className="flex items-center justify-center space-x-2 text-sm text-muted-foreground">
              <span>Start by:</span>
              <Link to="/training" className="text-primary hover:underline">
                Training a model
              </Link>
              <span>or</span>
              <Link to="/endpoints" className="text-primary hover:underline">
                Creating an endpoint
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="border">
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-foreground">{endpoints.length}</div>
                <div className="text-sm text-muted-foreground">Total Classifiers</div>
              </CardContent>
            </Card>
            
            <Card className="border">
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-foreground">
                  {endpoints.filter(e => e.status === 'active').length}
                </div>
                <div className="text-sm text-muted-foreground">Ready for Use</div>
              </CardContent>
            </Card>
            
            <Card className="border">
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-foreground">
                  {averageAccuracy.toFixed(1)}%
                </div>
                <div className="text-sm text-muted-foreground">Average Accuracy</div>
              </CardContent>
            </Card>
          </div>

          {/* Classifiers List */}
          <div className="space-y-4">
            {endpoints.map((endpoint) => (
              <Card key={endpoint.id} className="border hover:border-border/60 transition-colors">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg text-foreground">
                        {endpoint.name}
                      </CardTitle>
                      <div className="mt-2 space-y-2">
                        <div className="text-sm text-muted-foreground">
                          <span className="font-medium">Project:</span> {endpoint.project_name}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          <span className="font-medium">Status:</span>{' '}
                          <Badge className={getStatusColor(endpoint.status)}>
                            {endpoint.status}
                          </Badge>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          <span className="text-muted-foreground">Accuracy: </span>
                          <span className="font-medium">{endpoint.accuracy?.toFixed(1) || 'N/A'}%</span>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          <span className="font-medium">Created:</span>{' '}
                          {new Date(endpoint.created_at * 1000).toLocaleDateString()}
                        </div>
                      </div>
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
            ))}
          </div>
        </>
      )}
    </div>
  );
}