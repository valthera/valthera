import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Progress } from '../components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../components/ui/tooltip';
import { Badge } from '../components/ui/badge';
import { ArrowLeft, Plus, Play, HelpCircle, Target, Video, Link as LinkIcon, Settings, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { api, type Concept } from '../lib/api';

// Removed unused VideoFile interface

interface ConceptCardProps {
  concept: Concept;
  projectId: string;
  linkedVideoCount: number;
}

const VJEPA_REQUIREMENTS = {
  minimum: 8,
  recommended: 20,
  optimal: 50
};

function ConceptCard({ concept, projectId, linkedVideoCount }: ConceptCardProps) {
  const getTrainingStatus = (count: number) => {
    if (count < VJEPA_REQUIREMENTS.minimum) {
      return { status: 'insufficient', color: 'text-red-600', bgColor: 'bg-red-100', icon: XCircle };
    } else if (count < VJEPA_REQUIREMENTS.recommended) {
      return { status: 'minimum', color: 'text-yellow-600', bgColor: 'bg-yellow-100', icon: AlertTriangle };
    } else {
      return { status: 'good', color: 'text-green-600', bgColor: 'bg-green-100', icon: CheckCircle };
    }
  };

  const trainingStatus = getTrainingStatus(linkedVideoCount);
  const StatusIcon = trainingStatus.icon;
  const progressValue = Math.min(100, (linkedVideoCount / VJEPA_REQUIREMENTS.optimal) * 100);

  return (
    <Link to={`/projects/${projectId}/concepts/${concept.id}`}>
      <Card className="border border-gray-200 hover:border-gray-300 transition-colors cursor-pointer">
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-lg">
            <span className="text-black">{concept.name}</span>
            <div className="flex items-center space-x-2">
              <StatusIcon className={`h-4 w-4 ${trainingStatus.color}`} />
              <Settings className="h-4 w-4 text-gray-400" />
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* VJEPA Training Status */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">VJEPA Training Videos</span>
              <span className="font-medium">{linkedVideoCount}</span>
            </div>
            <Progress 
              value={progressValue} 
              className="h-2"
            />
            <p className="text-xs text-gray-500">
              {linkedVideoCount < VJEPA_REQUIREMENTS.minimum 
                ? `Need ${VJEPA_REQUIREMENTS.minimum - linkedVideoCount} more videos (minimum for VJEPA)`
                : linkedVideoCount < VJEPA_REQUIREMENTS.recommended
                ? `${linkedVideoCount}/${VJEPA_REQUIREMENTS.recommended} videos (recommended for good performance)`
                : linkedVideoCount < VJEPA_REQUIREMENTS.optimal
                ? `${linkedVideoCount}/${VJEPA_REQUIREMENTS.optimal} videos (optimal for best results)`
                : `${linkedVideoCount} videos (excellent for VJEPA training)`
              }
            </p>
          </div>

          {/* Status Summary */}
          <div className={`p-3 rounded-lg ${trainingStatus.bgColor} border`}>
            <div className="flex items-center space-x-2 text-sm">
              <StatusIcon className={`h-4 w-4 ${trainingStatus.color}`} />
              <span className={`font-medium ${trainingStatus.color}`}>
                {trainingStatus.status === 'insufficient' && 'Insufficient Videos'}
                {trainingStatus.status === 'minimum' && 'Minimum Met'}
                {trainingStatus.status === 'good' && 'Training Ready'}
              </span>
            </div>
            <p className="text-xs mt-1 text-gray-600">
              {trainingStatus.status === 'insufficient' && 'Need more videos to start VJEPA training'}
              {trainingStatus.status === 'minimum' && 'Can train, but more videos will improve accuracy'}
              {trainingStatus.status === 'good' && 'Good dataset size for reliable VJEPA training'}
            </p>
          </div>

          {/* Quick Actions */}
          <div className="flex items-center justify-between pt-2 border-t border-gray-100">
            <span className="text-xs text-gray-500">Click to manage videos</span>
            <div className="flex items-center space-x-1">
              <Video className="h-3 w-3 text-gray-400" />
              <span className="text-xs text-gray-500">{linkedVideoCount} linked</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

export function DefineConcepts() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [loading, setLoading] = useState(true);
  const [newConceptName, setNewConceptName] = useState('');
  const [addingConcept, setAddingConcept] = useState(false);
  const [linkedDataSources, setLinkedDataSources] = useState<string[]>([]);
  const [conceptVideoCounts, setConceptVideoCounts] = useState<Record<string, number>>({});

  const loadConcepts = useCallback(async () => {
    if (!projectId) return;
    
    try {
      const data = await api.concepts.list(projectId);
      setConcepts(data);
      
      // Extract video counts from concept data
      const videoCounts: Record<string, number> = {};
      data.forEach(concept => {
        videoCounts[concept.id] = concept.sampleCount || 0;
      });
      setConceptVideoCounts(videoCounts);
    } catch (error) {
      console.error('Failed to load concepts:', error);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      loadConcepts();
      loadProjectDataSources();
    }
  }, [projectId, loadConcepts]);

  const loadProjectDataSources = async () => {
    if (!projectId) {
      console.warn('No project ID available for loading data sources');
      setLinkedDataSources([]);
      return;
    }

    try {
      // Fetch project details from API
      const project = await api.projects.get(projectId);
      setLinkedDataSources(project.linkedDataSources || []);
    } catch (error) {
      console.error('Failed to load project data sources:', error);
      setLinkedDataSources([]);
    }
  };

  const addConcept = async () => {
    if (!projectId || !newConceptName.trim()) return;

    try {
      setAddingConcept(true);
      const newConcept = await api.concepts.create(projectId, { name: newConceptName });
      setConcepts([...concepts, newConcept]);
      
      // Initialize video count for new concept
      setConceptVideoCounts(prev => ({
        ...prev,
        [newConcept.id]: newConcept.sampleCount || 0
      }));
      
      setNewConceptName('');
    } catch (error) {
      console.error('Failed to add concept:', error);
    } finally {
      setAddingConcept(false);
    }
  };

  // Removed unused handleVideoSelection function

  const canStartTraining = concepts.length > 0 && concepts.some(c => c.sampleCount > 0);

  const startTraining = () => {
    if (projectId && canStartTraining) {
      navigate(`/projects/${projectId}/training`);
    }
  };

  const exampleConcepts = [
    'Pick and Place',
    'Object Grasping', 
    'Screw Assembly',
    'Wire Insertion',
    'Quality Inspection',
    'Sorting Objects'
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading concepts...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/dashboard')}
            className="text-gray-600 hover:text-black"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Projects
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-black">Define Concepts</h1>
            <p className="text-gray-600 mt-1">
              Define the visual concepts you want to classify and train
            </p>
          </div>
        </div>

        <Button
          onClick={startTraining}
          disabled={!canStartTraining}
          className="bg-black text-white hover:bg-gray-800 disabled:bg-gray-300"
        >
          <Play className="mr-2 h-4 w-4" />
          Start Training
        </Button>
      </div>

      {/* Add New Concept */}
      <Card className="border border-gray-200">
        <CardHeader>
          <CardTitle className="flex items-center text-lg">
            <Plus className="mr-2 h-5 w-5" />
            Add Concept
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className="ml-2 h-4 w-4 text-gray-400 cursor-help" />
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <p className="text-sm">
                    Examples: {exampleConcepts.slice(0, 3).join(', ')}, etc.
                    Each concept needs video samples to train the classifier.
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-2">
            <Input
              placeholder="e.g., Pick and Place"
              value={newConceptName}
              onChange={(e) => setNewConceptName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addConcept()}
              className="flex-1"
            />
            <Button
              onClick={addConcept}
              disabled={!newConceptName.trim() || addingConcept}
              className="bg-black text-white hover:bg-gray-800"
            >
              {addingConcept ? 'Adding...' : 'Add'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Concepts List */}
      {concepts.length === 0 ? (
        <div className="text-center py-12">
          <Target className="mx-auto h-16 w-16 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No concepts defined</h3>
          <p className="text-gray-600 mb-4">
            Add your first concept to start building a classifier
          </p>
          <div className="flex flex-wrap justify-center gap-2 max-w-md mx-auto">
            <span className="text-sm text-gray-500">Examples:</span>
            {exampleConcepts.map((example) => (
              <Badge
                key={example}
                variant="secondary"
                className="cursor-pointer hover:bg-gray-200"
                onClick={() => setNewConceptName(example)}
              >
                {example}
              </Badge>
            ))}
          </div>
        </div>
      ) : (
        <div>
          {/* Data Sources Info */}
          {linkedDataSources.length > 0 ? (
            <div className="mb-6 bg-green-50 p-4 rounded-lg border border-green-200">
              <div className="flex items-center text-sm text-green-800 mb-2">
                <LinkIcon className="h-4 w-4 mr-2" />
                <span className="font-medium">Linked Data Sources:</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {linkedDataSources.map((source) => (
                  <Badge key={source} variant="outline" className="bg-white">
                    📁 {source}
                  </Badge>
                ))}
              </div>
              <p className="text-xs text-green-700 mt-2">
                Select videos from these data sources for each concept.
              </p>
            </div>
          ) : (
            <div className="mb-6 bg-orange-50 p-4 rounded-lg border border-orange-200">
              <div className="flex items-center text-sm text-orange-800 mb-2">
                <LinkIcon className="h-4 w-4 mr-2" />
                <span className="font-medium">No Data Sources Linked</span>
              </div>
              <p className="text-xs text-orange-700">
                Go to project settings to link data sources first.
              </p>
            </div>
          )}

          {/* Concepts Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {concepts.map((concept) => (
              <ConceptCard
                key={concept.id}
                concept={concept}
                projectId={projectId!}
                linkedVideoCount={conceptVideoCounts[concept.id] || 0}
              />
            ))}
          </div>
        </div>
      )}

      {/* Training Status */}
      {concepts.length > 0 && (
        <Card className="border border-gray-200 bg-gray-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium text-black">Training Status</h3>
                <p className="text-sm text-gray-600">
                  {canStartTraining 
                    ? 'Ready to start training with your defined concepts'
                    : 'Add video samples to at least one concept to enable training'
                  }
                </p>
              </div>
              <Button
                onClick={startTraining}
                disabled={!canStartTraining}
                className="bg-black text-white hover:bg-gray-800 disabled:bg-gray-300"
              >
                <Play className="mr-2 h-4 w-4" />
                Start Training
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}