import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Plug, Plus, ArrowRight, Copy, ExternalLink } from 'lucide-react';
import { api, type Project, type Endpoint } from '../lib/api';

export function EndpointsOverviewPage() {
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

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'bg-green-100 dark:bg-green-950/20 text-green-800 dark:text-green-200';
      case 'training': return 'bg-yellow-100 dark:bg-yellow-950/20 text-yellow-800 dark:text-yellow-200';
      case 'failed': return 'bg-red-100 dark:bg-red-950/20 text-red-800 dark:text-red-200';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-muted-foreground">Loading endpoints...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Endpoints</h1>
          <p className="text-muted-foreground mt-1">
            Manage all your API endpoints across projects
          </p>
        </div>
        
        <Button asChild className="bg-primary text-primary-foreground hover:bg-primary/90">
          <Link to="/dashboard">
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Link>
        </Button>
      </div>

      {/* Endpoints Overview */}
      {endpoints.length === 0 ? (
        <Card className="border">
          <CardContent className="text-center py-12">
            <Plug className="mx-auto h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">No endpoints available</h3>
            <p className="text-muted-foreground mb-6">
              Train concept classifiers to generate API endpoints for your applications
            </p>
            
            <div className="space-y-4">
              <div className="flex items-center justify-center space-x-2 text-sm text-muted-foreground">
                <span className="flex items-center">
                  <span className="w-6 h-6 rounded-full bg-muted text-xs flex items-center justify-center mr-2">1</span>
                  Create Project
                </span>
                <ArrowRight className="h-4 w-4" />
                <span className="flex items-center">
                  <span className="w-6 h-6 rounded-full bg-muted text-xs flex items-center justify-center mr-2">2</span>
                  Define Concepts
                </span>
                <ArrowRight className="h-4 w-4" />
                <span className="flex items-center">
                  <span className="w-6 h-6 rounded-full bg-muted text-xs flex items-center justify-center mr-2">3</span>
                  Train & Deploy
                </span>
              </div>
              
              <Button asChild className="bg-primary text-primary-foreground hover:bg-primary/90">
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
            <Card className="border">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-foreground">{endpoints.length}</div>
                <div className="text-sm text-muted-foreground">Total Endpoints</div>
              </CardContent>
            </Card>
            <Card className="border">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-foreground">
                  {endpoints.filter(e => e.status === 'ready').length}
                </div>
                <div className="text-sm text-muted-foreground">Ready for Use</div>
              </CardContent>
            </Card>
            <Card className="border">
              <CardContent className="p-4">
                <div className="text-2xl font-bold text-foreground">
                  {Math.round(endpoints.filter(e => e.status === 'ready').reduce((sum, e) => sum + e.accuracy, 0) / 
                   endpoints.filter(e => e.status === 'ready').length || 0)}%
                </div>
                <div className="text-sm text-muted-foreground">Average Accuracy</div>
              </CardContent>
            </Card>
          </div>

          {/* Endpoints Table */}
          <Card className="border">
            <CardHeader>
              <CardTitle>All Endpoints</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Classifier</TableHead>
                    <TableHead>Project</TableHead>
                    <TableHead>Accuracy</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Endpoint URL</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {endpoints.map((endpoint) => {
                    const project = projects.find(p => p.id === endpoint.projectId);
                    
                    return (
                      <TableRow key={endpoint.id}>
                        <TableCell className="font-medium">
                          {endpoint.classifierName}
                        </TableCell>
                        <TableCell>
                          <Link 
                            to={`/projects/${endpoint.projectId}/endpoints`}
                            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:underline"
                          >
                            {project?.name}
                          </Link>
                        </TableCell>
                        <TableCell>
                          {endpoint.status === 'ready' && (
                            <span className="font-medium text-green-600 dark:text-green-400">
                              {endpoint.accuracy.toFixed(1)}%
                            </span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusColor(endpoint.status)}>
                            {endpoint.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2 max-w-xs">
                            <code className="text-xs bg-muted px-2 py-1 rounded truncate">
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
                            <Button
                              asChild
                              size="sm"
                              variant="outline"
                            >
                              <Link to={`/projects/${endpoint.projectId}/endpoints`}>
                                <ExternalLink className="mr-1 h-3 w-3" />
                                View
                              </Link>
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Quick Start Guide */}
          <Card className="border bg-blue-50 dark:bg-blue-950/20">
            <CardHeader>
              <CardTitle className="flex items-center">
                <ExternalLink className="mr-2 h-5 w-5" />
                API Usage
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-foreground mb-2">Authentication</h4>
                  <div className="bg-foreground text-background p-3 rounded-lg font-mono text-sm">
                    <pre>Authorization: Bearer YOUR_API_KEY</pre>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-foreground mb-2">Make a Request</h4>
                  <div className="bg-foreground text-background p-3 rounded-lg font-mono text-sm overflow-x-auto">
                    <pre>{`curl -X POST "YOUR_ENDPOINT_URL" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -F "video=@path/to/video.mp4"`}</pre>
                  </div>
                </div>

                <div className="bg-blue-100 dark:bg-blue-950/40 p-4 rounded-lg">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    <strong>Need an API key?</strong> Visit the{' '}
                    <Link to="/api-keys" className="underline font-medium">
                      API Keys page
                    </Link>{' '}
                    to generate and manage your authentication tokens.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}