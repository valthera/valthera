import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Container, 
  Stack, 
  Group, 
  Text, 
  Button, 
  Paper, 
  Badge, 
  Card, 
  Grid,
  Modal,
  TextInput,
  Select,
  FileButton,
  Textarea
} from '@mantine/core'
import { IconUpload } from '@tabler/icons-react'
import { useObservations } from '../contexts/ObservationsContext'
import { AltAppShell } from '../components/AltAppShell'
import VideoPlayer from '../components/VideoPlayer'
import { FrameEditor } from '../components/FrameEditor'
import EmbeddingsExplorer from '../components/EmbeddingsExplorer'
import TrainAndTest from '../components/TrainAndTest'
import DeployAndMonitor from '../components/DeployAndMonitor'

const SECTIONS = [
  { slug: 'data-manager', label: 'Data Manager' },
  { slug: 'labeling', label: 'Video Labeling' },
  { slug: 'training', label: 'Training' },
  { slug: 'deployment', label: 'Deployment' }
]

interface VideoFrame {
  id: string
  thumbnail: string
  timestamp: string
  labels: string[]
  isSelected: boolean
}

interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
  label?: string
}

export function VideoLabeling() {
  const { observations } = useObservations()
  const { behavior, section } = useParams<{ behavior: string; section: string }>()
  const navigate = useNavigate()
  const [annotations, setAnnotations] = useState<Record<string, BoundingBox[]>>({})
  const [selectedFrame, setSelectedFrame] = useState<VideoFrame | null>(null)
  const [frameEditorOpened, setFrameEditorOpened] = useState(false)
  const [uploadModalOpened, setUploadModalOpened] = useState(false)
  const [videoError, setVideoError] = useState<string | null>(null)
  const videoPlayerRef = useRef<any>(null)

  // Get current video annotations
  const getCurrentVideoAnnotations = () => {
    return annotations || {}
  }

  // Set current video annotations
  const setCurrentVideoAnnotations = (newAnnotations: Record<string, BoundingBox[]>) => {
    setAnnotations(newAnnotations)
  }

  // Update annotations when behavior changes
  useEffect(() => {
    const currentAnnotations = getCurrentVideoAnnotations()
    setCurrentVideoAnnotations(currentAnnotations)
  }, [behavior])

  // Log annotations for debugging
  useEffect(() => {
    console.log('Observation annotations updated:', annotations)
  }, [annotations])

  // Observation-specific video sources
  const getVideoSourcesForObservation = (observationSlug: string) => {
    // This would typically come from an API call
    // For now, return mock data based on the observation
    const sources = {
      'human-entry': [
        { id: '1', name: 'Camera 1 - Front Door', url: 'https://example.com/video1.mp4' },
        { id: '2', name: 'Camera 2 - Back Door', url: 'https://example.com/video2.mp4' },
        { id: '3', name: 'Camera 3 - Side Entrance', url: 'https://example.com/video3.mp4' }
      ],
      'object-pickup': [
        { id: '4', name: 'Robot Arm Camera', url: 'https://example.com/robot1.mp4' },
        { id: '5', name: 'Workspace Camera', url: 'https://example.com/workspace1.mp4' }
      ],
      'movement-pattern': [
        { id: '6', name: 'Tracking Camera A', url: 'https://example.com/tracking1.mp4' },
        { id: '7', name: 'Tracking Camera B', url: 'https://example.com/tracking2.mp4' }
      ]
    }
    return sources[observationSlug as keyof typeof sources] || []
  }

  const videoSources = getVideoSourcesForObservation(behavior || '');

  // Find current observation and section
  const currentObservationObj = observations.find((o: any) => o.slug === behavior) || observations[0]
  const currentSectionObj = SECTIONS.find(s => s.slug === section) || SECTIONS[0]

  const observationItems = observations.map((o: any) => ({ name: o.name, active: o.slug === behavior }))

  // Sidebar items
  const sidebarItems = SECTIONS.map(s => ({
    label: s.label,
    active: s.slug === section,
    onClick: () => navigate(`/observations/${behavior}/${s.slug}`),
  }))

  const onSelectObservation = (name: string) => {
    // Pause the video when switching observations
    if (videoPlayerRef.current && videoPlayerRef.current.pause) {
      videoPlayerRef.current.pause();
    }
    
    const o = observations.find((o: any) => o.name === name)
    if (o) navigate(`/observations/${o.slug}/${section}`)
  }
  const onNewObservation = () => {
    navigate('/observations/new')
  }

  const handleSaveFrame = () => {
    setFrameEditorOpened(false)
    setSelectedFrame(null)
  }

  const handleAnnotationsChange = (newAnnotations: Record<string, BoundingBox[]>) => {
    setAnnotations(newAnnotations)
  }

  const handleVideoError = (error: string) => {
    setVideoError(error)
  }

  // Breadcrumbs
  const breadcrumbs = (
    <Group gap={4} align="center">
      <Text c="#aaa" size="sm">{currentObservationObj.name}</Text>
      <Text c="#aaa" size="sm">›</Text>
      <Text c="#fff" size="sm" fw={600}>{currentSectionObj.label}</Text>
    </Group>
  )

  const availableLabels = ['walking', 'running', 'sitting', 'standing', 'person', 'dog', 'car', 'parked']

  // Count total annotations
  const totalAnnotations = Object.values(annotations).reduce((sum, boxes) => sum + boxes.length, 0)

  // Handler to seek video to a specific time
  const handleSeekTo = (timestamp: string) => {
    if (videoPlayerRef.current && videoPlayerRef.current.seekTo) {
      videoPlayerRef.current.seekTo(parseFloat(timestamp));
    }
  };

  // Handler to update annotation label
  const handleUpdateLabel = (timestamp: string, boxIdx: number, newLabel: string) => {
    const updatedAnnotations = { ...annotations };
    if (updatedAnnotations[timestamp] && updatedAnnotations[timestamp][boxIdx]) {
      updatedAnnotations[timestamp][boxIdx] = { ...updatedAnnotations[timestamp][boxIdx], label: newLabel };
      setAnnotations(updatedAnnotations);
    }
  };

  // Handler to delete annotation
  const handleDeleteAnnotation = (timestamp: string, boxIdx: number) => {
    const updatedAnnotations = { ...annotations };
    if (updatedAnnotations[timestamp]) {
      updatedAnnotations[timestamp] = updatedAnnotations[timestamp].filter((_, i) => i !== boxIdx);
      if (updatedAnnotations[timestamp].length === 0) delete updatedAnnotations[timestamp];
      setAnnotations(updatedAnnotations);
    }
  };

  // Render different content based on section
  const renderSectionContent = () => {
    switch (section) {
      case 'data-manager':
        return (
          <Stack gap="lg">
            {/* Video Preview with Tracking */}
            <Stack gap="lg">
              <Group justify="space-between" align="center" mb="xs">
                <Text fw={600} size="md">Video Preview & Object Tracking</Text>
                <Group gap="xs">
                  <Badge color="blue" variant="light">
                    {totalAnnotations} annotations
                  </Badge>
                  <Button
                    size="xs"
                    variant="outline"
                    leftSection={<IconUpload size={14} />}
                    onClick={() => setUploadModalOpened(true)}
                  >
                    Upload Video
                  </Button>
                </Group>
              </Group>

              {/* Video Selector */}
              <Paper p="xs" withBorder mb="md">
                <Text size="sm" fw={500} mb="xs">Videos for {currentObservationObj.name}:</Text>
                <Group gap="xs">
                  {videoSources.map((_, index) => {
                    const videoAnnotations = annotations || {};
                    const videoAnnotationCount = Object.values(videoAnnotations).reduce((sum, boxes) => sum + boxes.length, 0);
                    return (
                      <Button
                        key={index}
                        size="xs"
                        variant={index === 0 ? "filled" : "outline"}
                        onClick={() => {
                          // setCurrentVideoIndex(index) // This line is removed as per new_code
                          setVideoError(null)
                        }}
                      >
                        Video {index + 1}
                        {videoAnnotationCount > 0 && (
                          <Badge size="xs" ml={4} color="blue">
                            {videoAnnotationCount}
                          </Badge>
                        )}
                      </Button>
                    );
                  })}
                </Group>
              </Paper>

              {videoError ? (
                <Paper p="xl" withBorder style={{ textAlign: 'center' }}>
                  <Text c="red" size="lg" mb="md">⚠️ Video Loading Error</Text>
                  <Text c="dimmed" size="sm" mb="lg">
                    {videoError}
                  </Text>
                  <Stack gap="md">
                    <Text size="sm" fw={500}>Try one of these sample videos:</Text>
                    <Group justify="center">
                      {videoSources.map((_, index) => (
                        <Button
                          key={index}
                          size="sm"
                          variant={index === 0 ? "filled" : "outline"}
                          onClick={() => {
                            // setCurrentVideoIndex(index) // This line is removed as per new_code
                            setVideoError(null)
                          }}
                        >
                          Sample Video {index + 1}
                        </Button>
                      ))}
                    </Group>
                    <Text size="xs" c="dimmed">
                      Or upload your own video using the button above
                    </Text>
                  </Stack>
                </Paper>
              ) : (
                <VideoPlayer 
                  ref={videoPlayerRef}
                  key={`${behavior}-${0}`} // This line is changed as per new_code
                  src={videoSources[0]?.url} // This line is changed as per new_code
                  height={"50%"}
                  onAnnotationsChange={handleAnnotationsChange}
                  onVideoError={handleVideoError}
                />
              )}
            </Stack>

            {/* Annotation Summary */}
            {totalAnnotations > 0 && (
              <Paper p="md" withBorder>
                <Text fw={600} size="sm" mb="xs">Annotation Summary</Text>
                <Grid>
                  {Object.entries(annotations).map(([timestamp, boxes]) => (
                    <Grid.Col key={timestamp} span={4}>
                      {boxes.map((box, boxIdx) => (
                        <Card p="xs" withBorder key={boxIdx}>
                          <Group justify="space-between" align="center">
                            <Text
                              size="xs"
                              fw={500}
                              style={{ cursor: 'pointer', textDecoration: 'underline' }}
                              onClick={() => handleSeekTo(timestamp)}
                            >
                              Time: {formatTime(parseFloat(timestamp))}
                            </Text>
                            <Button
                              size="xs"
                              color="red"
                              variant="subtle"
                              onClick={() => handleDeleteAnnotation(timestamp, boxIdx)}
                            >
                              Delete
                            </Button>
                          </Group>
                          <Group align="center" mt={4}>
                            <Text size="xs" c="dimmed">Label:</Text>
                            <input
                              type="text"
                              value={box.label || ''}
                              onChange={e => handleUpdateLabel(timestamp, boxIdx, e.target.value)}
                              style={{ fontSize: '0.9em', padding: '2px 4px', borderRadius: 4, border: '1px solid #ccc', minWidth: 60 }}
                            />
                          </Group>
                          <Text size="xs" c="dimmed" mt={4}>
                            x: {box.x.toFixed(2)}, y: {box.y.toFixed(2)}, w: {box.width.toFixed(2)}, h: {box.height.toFixed(2)}
                          </Text>
                        </Card>
                      ))}
                    </Grid.Col>
                  ))}
                </Grid>
              </Paper>
            )}
          </Stack>
        );
      case 'embeddings-explorer':
        return <EmbeddingsExplorer />;
      case 'train-test':
        return <TrainAndTest />;
      case 'deploy-monitor':
        return <DeployAndMonitor />;
      default:
        return (
          <Stack gap="lg">
            {/* Video Preview with Tracking */}
            <Stack gap="lg">
              <Group justify="space-between" align="center" mb="xs">
                <Text fw={600} size="md">Video Preview & Object Tracking</Text>
                <Group gap="xs">
                  <Badge color="blue" variant="light">
                    {totalAnnotations} annotations
                  </Badge>
                  <Button
                    size="xs"
                    variant="outline"
                    leftSection={<IconUpload size={14} />}
                    onClick={() => setUploadModalOpened(true)}
                  >
                    Upload Video
                  </Button>
                </Group>
              </Group>

              {/* Video Selector */}
              <Paper p="xs" withBorder mb="md">
                <Text size="sm" fw={500} mb="xs">Videos for {currentObservationObj.name}:</Text>
                <Group gap="xs">
                  {videoSources.map((_, index) => {
                    const videoAnnotations = annotations || {};
                    const videoAnnotationCount = Object.values(videoAnnotations).reduce((sum, boxes) => sum + boxes.length, 0);
                    return (
                      <Button
                        key={index}
                        size="xs"
                        variant={index === 0 ? "filled" : "outline"}
                        onClick={() => {
                          // setCurrentVideoIndex(index) // This line is removed as per new_code
                          setVideoError(null)
                        }}
                      >
                        Video {index + 1}
                        {videoAnnotationCount > 0 && (
                          <Badge size="xs" ml={4} color="blue">
                            {videoAnnotationCount}
                          </Badge>
                        )}
                      </Button>
                    );
                  })}
                </Group>
              </Paper>

              {videoError ? (
                <Paper p="xl" withBorder style={{ textAlign: 'center' }}>
                  <Text c="red" size="lg" mb="md">⚠️ Video Loading Error</Text>
                  <Text c="dimmed" size="sm" mb="lg">
                    {videoError}
                  </Text>
                  <Stack gap="md">
                    <Text size="sm" fw={500}>Try one of these sample videos:</Text>
                    <Group justify="center">
                      {videoSources.map((_, index) => (
                        <Button
                          key={index}
                          size="sm"
                          variant={index === 0 ? "filled" : "outline"}
                          onClick={() => {
                            // setCurrentVideoIndex(index) // This line is removed as per new_code
                            setVideoError(null)
                          }}
                        >
                          Sample Video {index + 1}
                        </Button>
                      ))}
                    </Group>
                    <Text size="xs" c="dimmed">
                      Or upload your own video using the button above
                    </Text>
                  </Stack>
                </Paper>
              ) : (
                <VideoPlayer 
                  ref={videoPlayerRef}
                  key={`${behavior}-${0}`} // This line is changed as per new_code
                  src={videoSources[0]?.url} // This line is changed as per new_code
                  height={"50%"}
                  onAnnotationsChange={handleAnnotationsChange}
                  onVideoError={handleVideoError}
                />
              )}
            </Stack>

            {/* Annotation Summary */}
            {totalAnnotations > 0 && (
              <Paper p="md" withBorder>
                <Text fw={600} size="sm" mb="xs">Annotation Summary</Text>
                <Grid>
                  {Object.entries(annotations).map(([timestamp, boxes]) => (
                    <Grid.Col key={timestamp} span={4}>
                      {boxes.map((box, boxIdx) => (
                        <Card p="xs" withBorder key={boxIdx}>
                          <Group justify="space-between" align="center">
                            <Text
                              size="xs"
                              fw={500}
                              style={{ cursor: 'pointer', textDecoration: 'underline' }}
                              onClick={() => handleSeekTo(timestamp)}
                            >
                              Time: {formatTime(parseFloat(timestamp))}
                            </Text>
                            <Button
                              size="xs"
                              color="red"
                              variant="subtle"
                              onClick={() => handleDeleteAnnotation(timestamp, boxIdx)}
                            >
                              Delete
                            </Button>
                          </Group>
                          <Group align="center" mt={4}>
                            <Text size="xs" c="dimmed">Label:</Text>
                            <input
                              type="text"
                              value={box.label || ''}
                              onChange={e => handleUpdateLabel(timestamp, boxIdx, e.target.value)}
                              style={{ fontSize: '0.9em', padding: '2px 4px', borderRadius: 4, border: '1px solid #ccc', minWidth: 60 }}
                            />
                          </Group>
                          <Text size="xs" c="dimmed" mt={4}>
                            x: {box.x.toFixed(2)}, y: {box.y.toFixed(2)}, w: {box.width.toFixed(2)}, h: {box.height.toFixed(2)}
                          </Text>
                        </Card>
                      ))}
                    </Grid.Col>
                  ))}
                </Grid>
              </Paper>
            )}
          </Stack>
        );
    }
  };

  return (
    <AltAppShell
      sidebarItems={sidebarItems}
      breadcrumbs={breadcrumbs}
      appName="Valthera"
      observations={observationItems}
      currentObservation={currentObservationObj.name}
      onSelectObservation={onSelectObservation}
      onNewObservation={onNewObservation}
    >
      <Container size="xl" py="md">
        {renderSectionContent()}
      </Container>

      {/* Upload Video Modal */}
      <Modal 
        opened={uploadModalOpened} 
        onClose={() => setUploadModalOpened(false)}
        title="Upload Video"
        size="md"
      >
        <Stack gap="md">
          <Text c="dimmed" size="sm">
            Upload a video file to extract frames for labeling. Supported formats: MP4, AVI, MOV
          </Text>
          
          <FileButton accept="video/*" onChange={(file) => console.log(file)}>
            {(props) => (
              <Button {...props} variant="outline" leftSection={<IconUpload size={16} />}>
                Choose Video File
              </Button>
            )}
          </FileButton>

          <TextInput
            label="Video Name"
            placeholder="Enter a descriptive name for this video"
          />

          <Textarea
            label="Description"
            placeholder="Optional description of the video content"
            rows={3}
          />

          <Select
            label="Extraction Settings"
            placeholder="Choose frame extraction settings"
            data={[
              { value: '1fps', label: '1 frame per second' },
              { value: '5fps', label: '5 frames per second' },
              { value: '10fps', label: '10 frames per second' },
              { value: 'custom', label: 'Custom interval' }
            ]}
          />

          <Group justify="flex-end" gap="xs">
            <Button variant="outline" onClick={() => setUploadModalOpened(false)}>
              Cancel
            </Button>
            <Button>
              Upload & Extract Frames
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Frame Editor Modal */}
      <FrameEditor
        opened={frameEditorOpened}
        onClose={() => setFrameEditorOpened(false)}
        frame={selectedFrame}
        availableLabels={availableLabels}
        onSave={handleSaveFrame}
      />
    </AltAppShell>
  )
}

// Helper function to format time
function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60)
    .toString()
    .padStart(2, '0');
  const s = Math.floor(seconds % 60)
    .toString()
    .padStart(2, '0');
  return `${m}:${s}`;
} 