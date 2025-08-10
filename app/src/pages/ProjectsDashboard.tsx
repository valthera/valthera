import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Plus, Calendar, Video, Database, Link as LinkIcon, FolderOpen, AlertCircle, Loader2 } from 'lucide-react';
import { useProjects } from '../contexts/ProjectsContext';
import { useTheme } from '../contexts/ThemeContext';
import { type Project } from '../lib/api';
import { handleApiError } from '../lib/errors';
import { cn } from '../lib/utils';
import * as api from '../lib/api';

export function ProjectsDashboard() {
  const { projects, loading, error, createProject } = useProjects();
  const { theme } = useTheme();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Debug logging
  console.log('ProjectsDashboard - projects:', projects);
  console.log('ProjectsDashboard - loading:', loading);
  console.log('ProjectsDashboard - error:', error);
  console.log('ProjectsDashboard - projects.length:', projects?.length);
  console.log('ProjectsDashboard - Array.isArray(projects):', Array.isArray(projects));

  // Form state
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [includeDroidDataset, setIncludeDroidDataset] = useState(true);
  const [selectedDataSources, setSelectedDataSources] = useState<string[]>([]);
  const [availableFolders, setAvailableFolders] = useState<Array<{id: string, name: string, videoCount: number, size: string}>>([]);

  useEffect(() => {
    loadDataSources();
  }, []);

  const loadDataSources = async () => {
    try {
      // @ts-ignore - dataSources property exists in the API object
      const dataSources = await (api as any).api?.dataSources?.list?.() ?? (api as any).dataSources?.list?.();
      const convertedFolders = dataSources.map((ds: any) => ({
        id: ds.id,
        name: ds.name,
        videoCount: ds.videoCount || 0,
        size: formatBytes(ds.totalSize || 0)
      }));
      setAvailableFolders(convertedFolders);
    } catch (error) {
      console.error('Failed to load data sources:', error);
      setAvailableFolders([]);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };


  const handleCreateProject = async () => {
    if (!projectName.trim()) return;

    try {
      setCreateLoading(true);
      setCreateError(null);
      
      await createProject({
        name: projectName,
        description: projectDescription,
        hasDroidDataset: includeDroidDataset,
        linkedDataSources: selectedDataSources
      });
      
      // Reset form
      setProjectName('');
      setProjectDescription('');
      setIncludeDroidDataset(true);
      setSelectedDataSources([]);
      setIsCreateModalOpen(false);
    } catch (error) {
      const apiError = handleApiError(error);
      setCreateError(apiError.message);
      console.error('Failed to create project:', error);
    } finally {
      setCreateLoading(false);
    }
  };

  const getSelectedFolderInfo = (folderId: string) => {
    return availableFolders.find(folder => folder.id === folderId);
  };

  const handleDataSourceToggle = (dataSourceId: string) => {
    setSelectedDataSources(prev => 
      prev.includes(dataSourceId)
        ? prev.filter(id => id !== dataSourceId)
        : [...prev, dataSourceId]
    );
  };

  const getTotalVideosFromSelected = () => {
    return selectedDataSources.reduce((total, sourceId) => {
      const folder = getSelectedFolderInfo(sourceId);
      return total + (folder?.videoCount || 0);
    }, 0);
  };

  const getStatusColor = (status: Project['status']) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'training': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center space-x-2 text-gray-500">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading projects...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn(
            "text-3xl font-bold",
            theme === 'dark' ? 'text-white' : 'text-black'
          )}>Projects</h1>
          <p className={cn(
            "mt-1",
            theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
          )}>
            Manage your robot perception projects and datasets
          </p>
        </div>
        
        <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
          <DialogTrigger asChild>
            <Button className={cn(
              "hover:bg-gray-800",
              theme === 'dark' ? 'bg-white text-black hover:bg-gray-200' : 'bg-black text-white'
            )}>
              <Plus className="mr-2 h-4 w-4" />
              New Project
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Create New Project</DialogTitle>
              <DialogDescription>
                Set up a new robot perception project. All videos will be embedded using VJEPA2.
              </DialogDescription>
            </DialogHeader>
            
            {createError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{createError}</AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Project Name</Label>
                <Input
                  id="name"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="e.g., Assembly Line Detection"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={projectDescription}
                  onChange={(e) => setProjectDescription(e.target.value)}
                  placeholder="Describe your project goals and use case..."
                  className="min-h-[80px]"
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="droid-dataset"
                  checked={includeDroidDataset}
                  onCheckedChange={setIncludeDroidDataset}
                />
                <Label htmlFor="droid-dataset" className="text-sm">
                  Include DROID dataset (150 robot manipulation videos)
                </Label>
              </div>

              {/* Data Sources Selection */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Data Sources to Link</Label>
                  <span className={cn(
                    "text-xs",
                    theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                  )}>
                    {selectedDataSources.length} selected • {getTotalVideosFromSelected()} videos total
                  </span>
                </div>
                
                <div className={cn(
                  "border p-3 max-h-48 overflow-y-auto",
                  theme === 'dark' 
                    ? 'border-gray-600 bg-gray-800' 
                    : 'border-gray-200 bg-gray-50'
                )}>
                  {availableFolders.length === 0 ? (
                    <div className="text-center py-4">
                      <FolderOpen className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                      <p className={cn(
                        "text-sm",
                        theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                      )}>No data sources available</p>
                      <Link 
                        to="/data-sources" 
                        className="text-xs text-blue-600 hover:text-blue-800 underline"
                        target="_blank"
                      >
                        Create your first data source
                      </Link>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {availableFolders.map((folder) => (
                        <div key={folder.id} className={cn(
                          "flex items-center space-x-3 p-2 transition-colors",
                          theme === 'dark'
                            ? 'hover:bg-gray-700'
                            : 'hover:bg-white'
                        )}>
                          <input
                            type="checkbox"
                            checked={selectedDataSources.includes(folder.id)}
                            onChange={() => handleDataSourceToggle(folder.id)}
                            className="rounded border-gray-300"
                          />
                          <FolderOpen className="h-4 w-4 text-gray-600" />
                          <div className="flex-1">
                            <div className={cn(
                              "text-sm font-medium",
                              theme === 'dark' ? 'text-white' : 'text-gray-900'
                            )}>{folder.name}</div>
                            <div className={cn(
                              "text-xs",
                              theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                            )}>
                              {folder.videoCount} videos • {folder.size}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Selected Data Sources Summary */}
                {selectedDataSources.length > 0 && (
                  <div className={cn(
                    "p-3 border",
                    theme === 'dark'
                      ? 'bg-green-900/20 border-green-700'
                      : 'bg-green-50 border-green-200'
                  )}>
                    <div className={cn(
                      "flex items-center text-sm mb-2",
                      theme === 'dark' ? 'text-green-300' : 'text-green-800'
                    )}>
                      <LinkIcon className="h-4 w-4 mr-2" />
                      <span className="font-medium">Selected Data Sources:</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {selectedDataSources.map((sourceId) => {
                        const folder = getSelectedFolderInfo(sourceId);
                        return (
                          <Badge key={sourceId} variant="outline" className={cn(
                            "text-xs",
                            theme === 'dark' ? 'bg-gray-800 text-white' : 'bg-white'
                          )}>
                            📁 {folder?.name} ({folder?.videoCount} videos)
                          </Badge>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              {/* Link to Data Sources */}
              <div className={cn(
                "p-3 border",
                theme === 'dark'
                  ? 'bg-blue-900/20 border-blue-700'
                  : 'bg-blue-50 border-blue-200'
              )}>
                <div className={cn(
                  "flex items-center text-sm mb-2",
                  theme === 'dark' ? 'text-blue-300' : 'text-blue-800'
                )}>
                  <LinkIcon className="h-4 w-4 mr-2" />
                  <span className="font-medium">Need to upload videos?</span>
                </div>
                <p className={cn(
                  "text-xs mb-2",
                  theme === 'dark' ? 'text-blue-300' : 'text-blue-700'
                )}>
                  Upload video files to Data Sources first, then link them to projects.
                </p>
                <Link 
                  to="/data-sources" 
                  className="text-xs text-blue-600 hover:text-blue-800 underline"
                  target="_blank"
                >
                  → Go to Data Sources
                </Link>
              </div>

              <div className={cn(
                "p-3",
                theme === 'dark' ? 'bg-gray-800' : 'bg-gray-50'
              )}>
                <p className={cn(
                  "text-xs",
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-600'
                )}>
                  <strong>Embedding Model:</strong> All videos will be processed using VJEPA2 for consistent feature extraction.
                </p>
              </div>
            </div>

            <div className="flex justify-end space-x-2">
              <Button
                variant="outline"
                onClick={() => setIsCreateModalOpen(false)}
                disabled={createLoading}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreateProject}
                disabled={!projectName.trim() || createLoading}
                className={cn(
                  "hover:bg-gray-800",
                  theme === 'dark' ? 'bg-white text-black hover:bg-gray-200' : 'bg-black text-white'
                )}
              >
                {createLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Project'
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
              onClick={() => window.location.reload()}
            >
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Projects Grid */}
      {(() => {
        const shouldShowEmpty = Array.isArray(projects) && projects.length === 0 && !error;
        console.log('ProjectsDashboard - shouldShowEmpty:', shouldShowEmpty);
        console.log('ProjectsDashboard - condition breakdown:', {
          isArray: Array.isArray(projects),
          length: projects?.length,
          error: error,
          condition: Array.isArray(projects) && projects.length === 0 && !error
        });
        
        return shouldShowEmpty ? (
          <div className="text-center py-12">
            <Database className="mx-auto h-16 w-16 text-gray-400 mb-4" />
            <h3 className={cn(
              "text-lg font-medium mb-2",
              theme === 'dark' ? 'text-white' : 'text-gray-900'
            )}>No projects yet</h3>
            <p className={cn(
              "mb-4",
              theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
            )}>
              Create your first project to start building robot perception models
            </p>
            <Button
              onClick={() => setIsCreateModalOpen(true)}
              className={cn(
                "hover:bg-gray-800",
                theme === 'dark' ? 'bg-white text-black hover:bg-gray-200' : 'bg-black text-white'
              )}
            >
              <Plus className="mr-2 h-4 w-4" />
              Create Project
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.isArray(projects) && projects.map((project) => {
              console.log('ProjectsDashboard - rendering project:', project);
              return (
                <Card
                  key={project.id}
                  className={cn(
                    "border transition-colors cursor-pointer",
                    theme === 'dark'
                      ? 'border-gray-600 hover:border-gray-500'
                      : 'border-gray-200 hover:border-gray-300'
                  )}
                >
                  <Link to={`/projects/${project.id}/concepts`}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className={cn(
                          "text-lg",
                          theme === 'dark' ? 'text-white' : 'text-black'
                        )}>{project.name}</CardTitle>
                        <Badge className={getStatusColor(project.status)}>
                          {project.status}
                        </Badge>
                      </div>
                      <CardDescription className={cn(
                        theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                      )}>
                        {project.description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className={cn(
                          "flex items-center text-sm",
                          theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                        )}>
                          <Calendar className="mr-2 h-4 w-4" />
                          Created {new Date(project.createdAt).toLocaleDateString()}
                        </div>
                        
                        <div className={cn(
                          "flex items-center text-sm",
                          theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                        )}>
                          <Video className="mr-2 h-4 w-4" />
                          {project.videoCount} videos
                        </div>

                        {project.hasDroidDataset && (
                          <div className={cn(
                            "flex items-center text-sm",
                            theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                          )}>
                            <Database className="mr-2 h-4 w-4" />
                            Includes DROID dataset
                          </div>
                        )}

                        {/* Linked Data Sources */}
                        {project.linkedDataSources && project.linkedDataSources.length > 0 && (
                          <div className="space-y-1">
                            <div className={cn(
                              "flex items-center text-sm",
                              theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                            )}>
                              <LinkIcon className="mr-2 h-4 w-4" />
                              Linked Data Sources:
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {project.linkedDataSources.map((source) => (
                                <Badge key={source} variant="outline" className="text-xs">
                                  📁 {source}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Link>
                </Card>
              );
            })}
          </div>
        );
      })()}
    </div>
  );
}