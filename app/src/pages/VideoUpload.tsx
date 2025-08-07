import { useState, useCallback } from 'react'
import { 
  Paper, 
  Text, 
  Group, 
  Button, 
  Stack, 
  Progress, 
  Alert, 
  Box,
  Container,
  Title,
  rem,
  TextInput,
  Textarea,
  Select,
  Divider
} from '@mantine/core'
import { 
  IconUpload, 
  IconX, 
  IconVideo,
  IconCheck,
  IconAlertCircle,
  IconArrowLeft
} from '@tabler/icons-react'
import { useDropzone } from 'react-dropzone'
import { AltAppShell } from '../components/AltAppShell'
import { useNavigate } from 'react-router-dom'

interface UploadedFile {
  file: File
  id: string
  progress: number
  status: 'uploading' | 'completed' | 'error'
  error?: string
}

export function VideoUpload() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [videoTitle, setVideoTitle] = useState('')
  const [videoDescription, setVideoDescription] = useState('')
  const [videoCategory, setVideoCategory] = useState<string | null>(null)
  const navigate = useNavigate()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      progress: 0,
      status: 'uploading'
    }))
    
    setUploadedFiles(prev => [...prev, ...newFiles])
    
    // Simulate upload progress
    newFiles.forEach(file => {
      simulateUpload(file.id)
    })
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    },
    multiple: true,
    maxSize: 500 * 1024 * 1024 // 500MB max
  })

  const simulateUpload = (fileId: string) => {
    const interval = setInterval(() => {
      setUploadedFiles(prev => 
        prev.map(file => {
          if (file.id === fileId) {
            const newProgress = Math.min(file.progress + Math.random() * 20, 100)
            if (newProgress >= 100) {
              clearInterval(interval)
              return { ...file, progress: 100, status: 'completed' }
            }
            return { ...file, progress: newProgress }
          }
          return file
        })
      )
    }, 200)
  }

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId))
  }

  const handleSubmit = async () => {
    if (!videoTitle.trim()) {
      return
    }

    setUploading(true)
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    setUploading(false)
    // Reset form
    setVideoTitle('')
    setVideoDescription('')
    setVideoCategory(null)
    setUploadedFiles([])
  }

  const canSubmit = videoTitle.trim() && uploadedFiles.length > 0 && 
    uploadedFiles.every(file => file.status === 'completed')

  return (
    <AltAppShell 
      hideSidebar 
      sidebarItems={[]}
    >
      <Container size="lg" py="xl">
        <Stack gap="xl">
          <Button
            variant="subtle"
            leftSection={<IconArrowLeft size={18} />}
            onClick={() => navigate(-1)}
            mb="md"
            style={{ alignSelf: 'flex-start' }}
          >
            Back
          </Button>
          <Box>
            <Title order={1} mb="xs">Upload Video</Title>
            <Text c="dimmed" size="lg">
              Upload your video files to start training your observation models
            </Text>
          </Box>

          <Paper p="xl" radius="md" withBorder>
            <Stack gap="lg">
              {/* Video Metadata */}
              <Box>
                <Title order={3} mb="md">Video Information</Title>
                <Stack gap="md">
                  <TextInput
                    label="Video Title"
                    placeholder="Enter a descriptive title for your video"
                    value={videoTitle}
                    onChange={(e) => setVideoTitle(e.target.value)}
                    required
                  />
                  
                  <Textarea
                    label="Description"
                    placeholder="Describe what this video contains..."
                    value={videoDescription}
                    onChange={(e) => setVideoDescription(e.target.value)}
                    rows={3}
                  />
                  
                  <Select
                    label="Category"
                    placeholder="Select a category"
                    data={[
                      { value: 'human-entry', label: 'Human Entry' },
                      { value: 'human-exit', label: 'Human Exit' },
                      { value: 'object-detection', label: 'Object Detection' },
                      { value: 'activity-recognition', label: 'Activity Recognition' },
                      { value: 'other', label: 'Other' }
                    ]}
                    value={videoCategory}
                    onChange={setVideoCategory}
                  />
                </Stack>
              </Box>

              <Divider />

              {/* File Upload Area */}
              <Box>
                <Title order={3} mb="md">Upload Video Files</Title>
                
                <Box
                  {...getRootProps()}
                  style={{
                    border: `2px dashed ${isDragActive ? '#4fd1c5' : '#666'}`,
                    borderRadius: rem(8),
                    padding: rem(40),
                    textAlign: 'center',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    background: isDragActive ? 'rgba(79, 209, 197, 0.1)' : 'transparent'
                  }}
                >
                  <input {...getInputProps()} />
                  <IconUpload size={48} color={isDragActive ? '#4fd1c5' : '#666'} style={{ marginBottom: rem(16) }} />
                  <Text size="lg" fw={500} mb="xs">
                    {isDragActive ? 'Drop the files here' : 'Drag & drop video files here'}
                  </Text>
                  <Text c="dimmed" size="sm" mb="lg">
                    or click to select files
                  </Text>
                  <Text size="xs" c="dimmed">
                    Supported formats: MP4, AVI, MOV, MKV, WMV, FLV, WebM (Max 500MB per file)
                  </Text>
                </Box>
              </Box>

              {/* Uploaded Files List */}
              {uploadedFiles.length > 0 && (
                <Box>
                  <Title order={4} mb="md">Uploaded Files</Title>
                  <Stack gap="md">
                    {uploadedFiles.map((file) => (
                      <Paper key={file.id} p="md" radius="md" withBorder>
                        <Group justify="space-between" mb="xs">
                          <Group gap="sm">
                            <IconVideo size={20} color="#4fd1c5" />
                            <Box>
                              <Text fw={500} size="sm">{file.file.name}</Text>
                              <Text size="xs" c="dimmed">
                                {(file.file.size / (1024 * 1024)).toFixed(2)} MB
                              </Text>
                            </Box>
                          </Group>
                          <Group gap="xs">
                            {file.status === 'completed' && (
                              <IconCheck size={16} color="green" />
                            )}
                            {file.status === 'error' && (
                              <IconAlertCircle size={16} color="red" />
                            )}
                            <Button
                              variant="subtle"
                              color="red"
                              size="xs"
                              onClick={() => removeFile(file.id)}
                            >
                              <IconX size={14} />
                            </Button>
                          </Group>
                        </Group>
                        
                        {file.status === 'uploading' && (
                          <Box>
                            <Progress 
                              value={file.progress} 
                              color="blue" 
                              size="sm"
                            />
                            <Text size="xs" c="dimmed" mt={4}>
                              {Math.round(file.progress)}% uploaded
                            </Text>
                          </Box>
                        )}
                        
                        {file.status === 'completed' && (
                          <Text size="xs" c="green">Upload completed</Text>
                        )}
                        
                        {file.status === 'error' && (
                          <Text size="xs" c="red">{file.error}</Text>
                        )}
                      </Paper>
                    ))}
                  </Stack>
                </Box>
              )}

              {/* Submit Button */}
              <Group justify="flex-end">
                <Button
                  size="lg"
                  onClick={handleSubmit}
                  loading={uploading}
                  disabled={!canSubmit}
                  leftSection={<IconUpload size={16} />}
                >
                  {uploading ? 'Uploading...' : 'Upload Videos'}
                </Button>
              </Group>
            </Stack>
          </Paper>

          {/* Help Section */}
          <Paper p="xl" radius="md" withBorder>
            <Title order={3} mb="md">Upload Guidelines</Title>
            <Stack gap="md">
              <Alert icon={<IconAlertCircle size={16} />} color="blue">
                <Text size="sm">
                  <strong>Video Quality:</strong> For best results, use high-quality videos with clear lighting and minimal motion blur.
                </Text>
              </Alert>
              <Alert icon={<IconAlertCircle size={16} />} color="blue">
                <Text size="sm">
                  <strong>File Size:</strong> Maximum file size is 500MB per video. For larger files, consider compressing your video.
                </Text>
              </Alert>
              <Alert icon={<IconAlertCircle size={16} />} color="blue">
                <Text size="sm">
                  <strong>Processing Time:</strong> Video processing may take several minutes depending on file size and server load.
                </Text>
              </Alert>
            </Stack>
          </Paper>
        </Stack>
      </Container>
    </AltAppShell>
  )
} 