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
  AlertTriangle, 
  XCircle,
  Search,
  Filter,
  Play,
  Trash2,
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
  linkedToConcept: boolean;
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

export function ConceptDetailPage() {
  const { projectId, conceptId } = useParams<{ projectId: string; conceptId: string }>();
  
  const [concept, setConcept] = useState<Concept | null>(null);
  const [availableVideos, setAvailableVideos] = useState<LocalVideoFile[]>([]);
  const [linkedVideos, setLinkedVideos] = useState<LocalVideoFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [projectName, setProjectName] = useState('');
  const [previewVideo, setPreviewVideo] = useState<string | null>(null);
  const [previewVideoUrl, setPreviewVideoUrl] = useState<string | null>(null);
  const [isLinking, setIsLinking] = useState(false);

  const loadConceptDetails = useCallback(async () => {
    try {
      const conceptData = await api.concepts.get(projectId!, conceptId!);
      setConcept(conceptData);
      
      // Get project details for project name
      const project = await api.projects.get(projectId!);
      setProjectName(project.name);
    } catch (error) {
      console.error('Failed to load concept details:', error);
    }
  }, [projectId, conceptId]);

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
            linkedToConcept: false, // Will be updated by loadLinkedVideos
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
      const response = await api.concepts.getLinkedVideos(projectId!, conceptId!);
      
      // Extract the linkedVideos array from the response
      const linkedVideosData = response.linkedVideos || [];
      
      // Transform API VideoFile to LocalVideoFile format
      const transformedLinkedVideos: LocalVideoFile[] = linkedVideosData.map(video => ({
        id: video.id || video.s3Key || '',
        name: video.fileName || '',
        duration: '0:00', // Duration not available yet
        size: video.size || formatFileSize(video.fileSize || 0),
        source: video.source || '', // Now available from API
        linkedToConcept: true,
        uploadDate: new Date(video.uploadDate)
      }));
      
      setLinkedVideos(transformedLinkedVideos);
      
      // Update available videos to mark linked ones
      setAvailableVideos(prev => prev.map(video => ({
        ...video,
        linkedToConcept: transformedLinkedVideos.some(linked => linked.id === video.id)
      })));
    } catch (error) {
      console.error('Failed to load linked videos:', error);
    } finally {
      setLoading(false);
    }
  }, [projectId, conceptId]);

  useEffect(() => {
    if (projectId && conceptId) {
      loadConceptDetails();
      loadAvailableVideos();
      loadLinkedVideos();
    }
  }, [projectId, conceptId, loadConceptDetails, loadAvailableVideos, loadLinkedVideos]);

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
        await api.concepts.unlinkVideo(projectId!, conceptId!, videoId);
      } else {
        // Link video
        await api.concepts.linkVideos(projectId!, conceptId!, [videoId]);
      }
      
      // Reload linked videos
      await loadLinkedVideos();
      
      // Update concept sample count
      if (concept) {
        const newCount = linkedVideos.length + (linkedVideos.find(v => v.id === videoId) ? -1 : 1);
        setConcept({ ...concept, sampleCount: newCount });
      }
    } catch (error) {
      console.error('Failed to toggle video link:', error);
    } finally {
      setIsLinking(false);
    }
  };

  const handleVideoPreview = async (videoId: string) => {
    const video = availableVideos.find(v => v.id === videoId) || 
                  linkedVideos.find(v => v.id === videoId);
    if (video) {
      setPreviewVideo(video.id);
      
      try {
        // Get stream URL for video - URL encode the videoId since it's an S3 key
        const encodedVideoId = encodeURIComponent(videoId);
        console.log('Getting video stream URL for:', videoId, 'encoded:', encodedVideoId);
        const streamUrl = await api.concepts.getVideoStreamUrl(encodedVideoId);
        console.log('Video stream URL:', streamUrl);
        setPreviewVideoUrl(streamUrl);
      } catch (error) {
        console.error('Failed to get video stream URL:', error);
        // Don't set any fallback URL - let the user know there was an error
        alert('Failed to load video. Please try again.');
      }
    }
  };

  const closeVideoPreview = () => {
    setPreviewVideo(null);
    setPreviewVideoUrl(null);
  };

  const getTrainingStatus = (count: number) => {
    if (count < VJEPA_REQUIREMENTS.minimum) {
      return { status: 'insufficient', color: 'text-red-600', bgColor: 'bg-red-100', icon: XCircle };
    } else if (count < VJEPA_REQUIREMENTS.recommended) {
      return { status: 'minimum', color: 'text-yellow-600', bgColor: 'bg-yellow-100', icon: AlertTriangle };
    } else if (count < VJEPA_REQUIREMENTS.optimal) {
      return { status: 'good', color: 'text-green-600', bgColor: 'bg-green-100', icon: CheckCircle };
    } else {
      return { status: 'optimal', color: 'text-blue-600', bgColor: 'bg-blue-100', icon: CheckCircle };
    }
  };

  const filteredAvailableVideos = availableVideos.filter(video => {
    const matchesSearch = video.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSource = selectedSource === '' || video.source === selectedSource;
    return matchesSearch && matchesSource && !video.linkedToConcept;
  });

  const trainingStatus = getTrainingStatus(linkedVideos.length);
  const StatusIcon = trainingStatus.icon;
  const progressValue = Math.min(100, (linkedVideos.length / VJEPA_REQUIREMENTS.optimal) * 100);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading concept details...</div>
      </div>
    );
  }

  if (!concept) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500">Concept not found</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link 
            to={`/projects/${projectId}/concepts`}
            className="flex items-center space-x-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Concepts</span>
          </Link>
          <div className="h-6 w-px bg-border" />
          <div>
            <h1 className="text-2xl font-bold text-foreground">{concept.name}</h1>
            <p className="text-muted-foreground">{projectName}</p>
          </div>
        </div>
      </div>

      {/* Video Preview Modal */}
      {previewVideo && previewVideoUrl && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-background border border-border rounded-lg p-6 max-w-6xl w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Video Preview</h3>
              <Button variant="ghost" size="sm" onClick={closeVideoPreview}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="bg-gray-900 rounded-lg overflow-hidden">
              <VideoPlayer 
                src={previewVideoUrl}
                width="100%"
                height={600}
                onVideoError={(error: string) => {
                  console.error('Video playback error:', error);
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Training Status Overview */}
      <Card className={`border-l-4 ${trainingStatus.bgColor} border-l-gray-400`}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <StatusIcon className={`h-5 w-5 ${trainingStatus.color}`} />
              <span>VJEPA Training Status</span>
            </CardTitle>
            <Badge className={`${trainingStatus.bgColor} ${trainingStatus.color} border-0`}>
              {linkedVideos.length} / {VJEPA_REQUIREMENTS.optimal} videos
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Progress value={progressValue} className="h-3" />
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="text-center">
                <div className={`font-medium ${linkedVideos.length >= VJEPA_REQUIREMENTS.minimum ? 'text-green-600' : 'text-red-600'}`}>
                  {VJEPA_REQUIREMENTS.minimum}+ Required
                </div>
                <div className="text-gray-500">Minimum for training</div>
              </div>
              <div className="text-center">
                <div className={`font-medium ${linkedVideos.length >= VJEPA_REQUIREMENTS.recommended ? 'text-green-600' : 'text-yellow-600'}`}>
                  {VJEPA_REQUIREMENTS.recommended}+ Recommended
                </div>
                <div className="text-gray-500">Good performance</div>
              </div>
              <div className="text-center">
                <div className={`font-medium ${linkedVideos.length >= VJEPA_REQUIREMENTS.optimal ? 'text-blue-600' : 'text-gray-600'}`}>
                  {VJEPA_REQUIREMENTS.optimal}+ Optimal
                </div>
                <div className="text-gray-500">Best results</div>
              </div>
            </div>

            <div className="bg-gray-50 p-3 rounded text-sm text-gray-700">
              <strong>About VJEPA:</strong> {VJEPA_REQUIREMENTS.description}. More samples generally lead to better feature learning and classification accuracy.
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Linked Videos */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Video className="h-5 w-5" />
              <span>Linked Videos ({linkedVideos.length})</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {linkedVideos.length === 0 ? (
              <div className="text-center py-8">
                <Video className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500 mb-2">No videos linked to this concept</p>
                <p className="text-sm text-gray-400">Select videos from available pool →</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {linkedVideos.map((video) => (
                  <div key={video.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Video className="h-4 w-4 text-gray-600" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">{video.name}</div>
                        <div className="text-xs text-gray-500">
                          {video.source} • {video.duration} • {video.size}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="p-1"
                        onClick={() => handleVideoPreview(video.id)}
                      >
                        <Play className="h-3 w-3" />
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="p-1 text-red-600 hover:text-red-700"
                        onClick={() => handleVideoToggle(video.id)}
                        disabled={isLinking}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Available Videos */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Plus className="h-5 w-5" />
                <span>Available Videos</span>
              </div>
              <span className="text-sm font-normal text-gray-500">
                {filteredAvailableVideos.length} available
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Search and Filter */}
              <div className="flex space-x-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search videos..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <select
                  value={selectedSource}
                  onChange={(e) => setSelectedSource(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="">All sources</option>
                  <option value="robot_arm_samples">robot_arm_samples</option>
                  <option value="grasping_testset">grasping_testset</option>
                  <option value="manipulation_demos">manipulation_demos</option>
                </select>
              </div>

              {/* Available Videos List */}
              {filteredAvailableVideos.length === 0 ? (
                <div className="text-center py-8">
                  <Filter className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-500">No available videos match your filters</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {filteredAvailableVideos.map((video) => (
                    <div key={video.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                      <div className="flex items-center space-x-3">
                        <Video className="h-4 w-4 text-gray-600" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{video.name}</div>
                          <div className="text-xs text-gray-500">
                            {video.source} • {video.duration} • {video.size}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          className="p-1"
                          onClick={() => handleVideoPreview(video.id)}
                        >
                          <Play className="h-3 w-3" />
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleVideoToggle(video.id)}
                          disabled={isLinking}
                          className="text-xs"
                        >
                          Link
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}