import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '../ui/dropdown-menu';
import { Plus, Video, Calendar, AlertCircle, Loader2, Upload, Play, Settings, Edit, Trash2 } from 'lucide-react';
import { api, type Concept } from '../../lib/api';
import { handleApiError } from '../../lib/errors';

interface ConceptListProps {
  projectId: string;
}

export function ConceptList({ projectId }: ConceptListProps) {
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);
  const [updateLoading, setUpdateLoading] = useState<string | null>(null);

  // Form state
  const [conceptName, setConceptName] = useState('');
  const [conceptDescription, setConceptDescription] = useState('');

  useEffect(() => {
    loadConcepts();
  }, [projectId]);

  const loadConcepts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.concepts.list(projectId);
      setConcepts(Array.isArray(data) ? data : (data?.concepts ?? []));
    } catch (error) {
      const apiError = handleApiError(error);
      setError(apiError.message);
      console.error('Failed to load concepts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateConcept = async () => {
    if (!conceptName.trim()) return;

    try {
      setCreateLoading(true);
      setCreateError(null);
      
      const newConcept = await api.concepts.create(projectId, {
        name: conceptName,
        description: conceptDescription
      });

      setConcepts([newConcept, ...concepts]);
      
      // Reset form
      setConceptName('');
      setConceptDescription('');
      setIsCreateModalOpen(false);
    } catch (error) {
      const apiError = handleApiError(error);
      setCreateError(apiError.message);
      console.error('Failed to create concept:', error);
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteConcept = async (conceptId: string) => {
    if (!confirm('Are you sure you want to delete this concept? This action cannot be undone.')) {
      return;
    }

    try {
      setDeleteLoading(conceptId);
      await api.concepts.delete(projectId, conceptId);
      setConcepts(concepts.filter(c => c.id !== conceptId));
    } catch (error) {
      const apiError = handleApiError(error);
      console.error('Failed to delete concept:', error);
      alert(`Failed to delete concept: ${apiError.message}`);
    } finally {
      setDeleteLoading(null);
    }
  };

  const handleUpdateConcept = async (conceptId: string, updates: { name?: string; description?: string }) => {
    try {
      setUpdateLoading(conceptId);
      const updatedConcept = await api.concepts.update(projectId, conceptId, updates);
      setConcepts(concepts.map(c => c.id === conceptId ? updatedConcept : c));
    } catch (error) {
      const apiError = handleApiError(error);
      console.error('Failed to update concept:', error);
      alert(`Failed to update concept: ${apiError.message}`);
    } finally {
      setUpdateLoading(null);
    }
  };

  const getStatusColor = (sampleCount: number) => {
    if (sampleCount === 0) return 'bg-red-100 text-red-800';
    if (sampleCount < 10) return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  const getStatusText = (sampleCount: number) => {
    if (sampleCount === 0) return 'No samples';
    if (sampleCount < 10) return 'Insufficient samples';
    return 'Ready for training';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center space-x-2 text-gray-500">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading concepts...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-black">Concepts</h2>
          <p className="text-gray-600 mt-1">
            Define and manage visual concepts for your project
          </p>
        </div>
        
        <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
          <DialogTrigger asChild>
            <Button className="bg-black text-white hover:bg-gray-800">
              <Plus className="mr-2 h-4 w-4" />
              New Concept
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Create New Concept</DialogTitle>
              <DialogDescription>
                Define a new visual concept by uploading sample videos.
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
                <Label htmlFor="name">Concept Name</Label>
                <Input
                  id="name"
                  value={conceptName}
                  onChange={(e) => setConceptName(e.target.value)}
                  placeholder="e.g., Pick and Place"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={conceptDescription}
                  onChange={(e) => setConceptDescription(e.target.value)}
                  placeholder="Describe what this concept represents..."
                  className="min-h-[80px]"
                />
              </div>

              <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                <div className="flex items-center text-sm text-blue-800 mb-2">
                  <Video className="h-4 w-4 mr-2" />
                  <span className="font-medium">Next Steps:</span>
                </div>
                <p className="text-xs text-blue-700">
                  After creating the concept, you'll be able to upload sample videos to train the model.
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
                onClick={handleCreateConcept}
                disabled={!conceptName.trim() || createLoading}
                className="bg-black text-white hover:bg-gray-800"
              >
                {createLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Concept'
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
              onClick={loadConcepts}
            >
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Concepts Grid */}
      {concepts.length === 0 && !error ? (
        <div className="text-center py-12">
          <Video className="mx-auto h-16 w-16 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No concepts yet</h3>
          <p className="text-gray-600 mb-4">
            Create your first concept to start training visual perception models
          </p>
          <Button
            onClick={() => setIsCreateModalOpen(true)}
            className="bg-black text-white hover:bg-gray-800"
          >
            <Plus className="mr-2 h-4 w-4" />
            Create Concept
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {concepts.map((concept) => (
            <Card
              key={concept.id}
              className="border border-gray-200 hover:border-gray-300 transition-colors"
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg text-black">{concept.name}</CardTitle>
                  <Badge className={getStatusColor(concept.sampleCount)}>
                    {getStatusText(concept.sampleCount)}
                  </Badge>
                </div>
                <CardDescription className="text-gray-600">
                  {concept.description || 'No description provided'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center text-sm text-gray-600">
                    <Video className="mr-2 h-4 w-4" />
                    {concept.sampleCount} sample videos
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-600">
                    <Calendar className="mr-2 h-4 w-4" />
                    Created {new Date(concept.uploadedAt).toLocaleDateString()}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex space-x-2 pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => {/* TODO: Open upload modal */}}
                    >
                      <Upload className="mr-1 h-3 w-3" />
                      Upload Samples
                    </Button>
                    
                    {concept.sampleCount >= 10 && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => {/* TODO: Start training */}}
                      >
                        <Play className="mr-1 h-3 w-3" />
                        Train
                      </Button>
                    )}
                    
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={deleteLoading === concept.id || updateLoading === concept.id}
                        >
                          <Settings className="h-3 w-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => {
                            const newName = prompt('Enter new name:', concept.name);
                            if (newName && newName.trim() && newName !== concept.name) {
                              handleUpdateConcept(concept.id, { name: newName.trim() });
                            }
                          }}
                          disabled={updateLoading === concept.id}
                        >
                          <Edit className="mr-2 h-4 w-4" />
                          Edit Name
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => {
                            const newDescription = prompt('Enter new description:', concept.description || '');
                            if (newDescription !== null && newDescription !== concept.description) {
                              handleUpdateConcept(concept.id, { description: newDescription });
                            }
                          }}
                          disabled={updateLoading === concept.id}
                        >
                          <Edit className="mr-2 h-4 w-4" />
                          Edit Description
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => handleDeleteConcept(concept.id)}
                          disabled={deleteLoading === concept.id}
                          className="text-red-600 focus:text-red-600"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          {deleteLoading === concept.id ? 'Deleting...' : 'Delete'}
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
} 