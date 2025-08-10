import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Progress } from '../components/ui/progress';
import VideoPlayer from '../components/VideoPlayer';
import { 
  ArrowLeft, 
  Video, 
  CheckCircle, 
  Search,
  Filter,
  Play,
  Plus,
  X
} from 'lucide-react';
import { api, type Concept } from '../lib/api';

interface LocalVideoFile {
  id: string;
  name: string;
  duration: string;
  size: string;
  source: string;
  linkedToObservation: boolean;
  uploadDate: Date;
}

interface VJEPARequirements {
  minimum: number;
  recommended: number;
  optimal: number;
  description: string;
}

const VJEPA_REQUIREMENTS: VJEPARequirements = {
  minimum: 8,
  recommended: 20,
  optimal: 50,
  description: "VJEPA (Video Joint Embedding Predictive Architecture) requires sufficient video samples to learn robust visual representations"
};

export function ObservationDetailPage() {
  const { projectId, observationId } = useParams<{ projectId: string; observationId: string }>();
  
  const [observation, setObservation] = useState<Concept | null>(null);
  const [availableVideos, setAvailableVideos] = useState<LocalVideoFile[]>([]);
  const [linkedVideos, setLinkedVideos] = useState<LocalVideoFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [projectName, setProjectName] = useState('');
  const [previewVideo, setPreviewVideo] = useState<string | null>(null);
  const [previewVideoUrl, setPreviewVideoUrl] = useState<string | null>(null);
  const [isLinking, setIsLinking] = useState(false);

  const loadObservationDetails = useCallback(async () => {
    try {
      const observationData = await api.observations.get(projectId!, observationId!);
      setObservation(observationData);
      
      // Get project details for project name
      const project = await api.projects.get(projectId!);
      setProjectName(project.name);
    } catch (error) {
      console.error('Failed to load observation details:', error);
    }
  }, [projectId, observationId]);

  const loadAvailableVideos = useCallback(async () => {
    try {
      // Get all data sources
      const dataSources = await api.dataSources.list();
      
      // Transform data source files into LocalVideoFile format
      const allVideos: LocalVideoFile[] = [];
      dataSources.forEach(dataSource => {
        dataSource.files.forEach(file => {
          allVideos.push({
            id: file.s3Key, // Use s3Key as unique ID
            name: file.fileName,
            duration: '0:00', // Duration not available from backend yet
            size: formatFileSize(file.fileSize),
            source: dataSource.name,
            linkedToObservation: false, // Will be updated by loadLinkedVideos
            uploadDate: new Date(file.uploadDate)
          });
        });
      });

      setAvailableVideos(allVideos);
    } catch (error) {
      console.error('Failed to load available videos:', error);
    }
  }, []);

  const loadLinkedVideos = useCallback(async () => {
    try {
      const response = await api.observations.getLinkedVideos(projectId!, observationId!);
      
      // Extract the linkedVideos array from the response
      const linkedVideosData = response.linkedVideos || [];
      
      // Transform API VideoFile to LocalVideoFile format
      const transformedLinkedVideos: LocalVideoFile[] = linkedVideosData.map(video => ({
        id: video.id || video.s3Key || '',
        name: video.fileName || '',
        duration: '0:00', // Duration not available yet
        size: video.size || formatFileSize(video.fileSize || 0),
        source: video.source || '', // Now available from API
        linkedToObservation: true,
        uploadDate: new Date(video.uploadDate)
      }));
      
      setLinkedVideos(transformedLinkedVideos);
      
      // Update available videos to mark linked ones
      setAvailableVideos(prev => prev.map(video => ({
        ...video,
        linkedToObservation: transformedLinkedVideos.some(linked => linked.id === video.id)
      })));
    } catch (error) {
      console.error('Failed to load linked videos:', error);
    } finally {
      setLoading(false);
    }
  }, [projectId, observationId]);

  useEffect(() => {
    if (projectId && observationId) {
      loadObservationDetails();
      loadAvailableVideos();
      loadLinkedVideos();
    }
  }, [projectId, observationId, loadObservationDetails, loadAvailableVideos, loadLinkedVideos]);

  // Helper function to format file size
  const formatFileSize = (bytes: number): string => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const handleVideoToggle = async (videoId: string) => {
    if (isLinking) return; // Prevent multiple simultaneous operations
    
    try {
      setIsLinking(true);
      
      if (linkedVideos.find(v => v.id === videoId)) {
        // Unlink video
        await api.observations.unlinkVideo(projectId!, observationId!, videoId);
      } else {
        // Link video
        await api.observations.linkVideos(projectId!, observationId!, [videoId]);
      }
      
      // Reload linked videos
      await loadLinkedVideos();
      
      // Update observation sample count
      if (observation) {
        const newCount = linkedVideos.length + (linkedVideos.find(v => v.id === videoId) ? -1 : 1);
        setObservation({ ...observation, sampleCount: newCount });
      }
    } catch (error) {
      console.error('Failed to toggle video link:', error);
    } finally {
      setIsLinking(false);
    }
  };

  const handleVideoPreview = async (videoId: string) => {
    try {
      setPreviewVideo(videoId);
      const encodedVideoId = encodeURIComponent(videoId);
      console.log('Getting video stream URL for:', videoId, 'encoded:', encodedVideoId);
      const streamUrl = await api.observations.getVideoStreamUrl(encodedVideoId);
      console.log('Video stream URL:', streamUrl);
      setPreviewVideoUrl(streamUrl);
    } catch (error) {
      console.error('Failed to get video stream URL:', error);
    }
  };

  const closeVideoPreview = () => {
    setPreviewVideo(null);
    setPreviewVideoUrl(null);
  };

  const getTrainingStatus = (count: number) => {
    if (count >= VJEPA_REQUIREMENTS.optimal) return { status: 'optimal', color: 'green' };
    if (count >= VJEPA_REQUIREMENTS.recommended) return { status: 'ready', color: 'blue' };
    if (count >= VJEPA_REQUIREMENTS.minimum) return { status: 'minimum', color: 'yellow' };
    return { status: 'insufficient', color: 'red' };
  };

  // Filter videos based on search term and selected source
  const filteredAvailableVideos = availableVideos.filter(video => {
    const matchesSearch = video.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         video.source.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSource = !selectedSource || video.source === selectedSource;
    return matchesSearch && matchesSource && !video.linkedToObservation;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-foreground"></div>
          <p className="mt-4 text-muted-foreground">Loading observation details...</p>
        </div>
      </div>
    );
  }

  if (!observation) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-gray-500">Observation not found</div>
      </div>
    );
  }

  const trainingStatus = getTrainingStatus(linkedVideos.length);
  const uniqueSources = [...new Set(availableVideos.map(v => v.source))];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-4">
          <Link to={`/projects/${projectId}/observations`}>
            <Button variant="outline" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              <span>Back to Observations</span>
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">{observation.name}</h1>
            <p className="text-muted-foreground">{projectName}</p>
          </div>
        </div>
        <Badge variant={trainingStatus.color === 'green' ? 'default' : 'secondary'}>
          {trainingStatus.status}
        </Badge>
      </div>

      {/* Training Status */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Video className="h-5 w-5 mr-2" />
            Training Readiness
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span>Video Samples</span>
              <span className="font-semibold">{linkedVideos.length} / {VJEPA_REQUIREMENTS.optimal}</span>
            </div>
            <Progress value={(linkedVideos.length / VJEPA_REQUIREMENTS.optimal) * 100} className="w-full" />
            <div className="text-sm text-gray-600">
              {VJEPA_REQUIREMENTS.description}
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="text-center p-2 bg-red-50 rounded">
                <div className="font-semibold text-red-600">Minimum</div>
                <div>{VJEPA_REQUIREMENTS.minimum}</div>
              </div>
              <div className="text-center p-2 bg-yellow-50 rounded">
                <div className="font-semibold text-yellow-600">Recommended</div>
                <div>{VJEPA_REQUIREMENTS.recommended}</div>
              </div>
              <div className="text-center p-2 bg-green-50 rounded">
                <div className="font-semibold text-green-600">Optimal</div>
                <div>{VJEPA_REQUIREMENTS.optimal}</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Available Videos */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Available Videos</span>
              <div className="flex items-center space-x-2">
                <div className="relative">
                  <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search videos..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-8 w-48"
                  />
                </div>
                <div className="relative">
                  <Filter className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <select
                    value={selectedSource}
                    onChange={(e) => setSelectedSource(e.target.value)}
                    className="pl-8 pr-8 py-2 border border-input rounded-md bg-background text-foreground"
                  >
                    <option value="">All Sources</option>
                    {uniqueSources.map(source => (
                      <option key={source} value={source}>{source}</option>
                    ))}
                  </select>
                </div>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {filteredAvailableVideos.map((video) => (
                <div key={video.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                  <div className="flex-1">
                    <div className="font-medium">{video.name}</div>
                    <div className="text-sm text-gray-500">
                      {video.source} • {video.size} • {video.duration}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleVideoPreview(video.id)}
                    >
                      <Play className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleVideoToggle(video.id)}
                      disabled={isLinking}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
              {filteredAvailableVideos.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No available videos found
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Linked Videos */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CheckCircle className="h-5 w-5 mr-2 text-green-600" />
              Linked Videos ({linkedVideos.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {linkedVideos.map((video) => (
                <div key={video.id} className="flex items-center justify-between p-3 border rounded-lg bg-green-50">
                  <div className="flex-1">
                    <div className="font-medium">{video.name}</div>
                    <div className="text-sm text-gray-500">
                      {video.source} • {video.size} • {video.duration}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleVideoPreview(video.id)}
                    >
                      <Play className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleVideoToggle(video.id)}
                      disabled={isLinking}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
              {linkedVideos.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  No videos linked to this observation
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Video Preview Modal */}
      {previewVideo && previewVideoUrl && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-background border border-border rounded-lg p-4 max-w-4xl w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Video Preview</h3>
              <Button variant="outline" size="sm" onClick={closeVideoPreview}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <VideoPlayer src={previewVideoUrl} />
          </div>
        </div>
      )}
    </div>
  );
}