import { useState, useEffect } from 'react'
import { 
  Modal, 
  TextInput, 
  Button, 
  Group, 
  Stack, 
  Chip, 
  Text, 
  Image,
  Textarea,
  Divider
} from '@mantine/core'
import { IconPlus, IconTrash } from '@tabler/icons-react'

interface FrameEditorProps {
  opened: boolean
  onClose: () => void
  frame: {
    id: string
    thumbnail: string
    timestamp: string
    labels: string[]
  } | null
  availableLabels: string[]
  onSave: (frameId: string, labels: string[], notes: string) => void
}

export function FrameEditor({ opened, onClose, frame, availableLabels, onSave }: FrameEditorProps) {
  const [labels, setLabels] = useState<string[]>([])
  const [newLabel, setNewLabel] = useState('')
  const [notes, setNotes] = useState('')

  useEffect(() => {
    if (frame) {
      setLabels(frame.labels)
      setNotes('')
    }
  }, [frame])

  const handleAddLabel = () => {
    if (newLabel.trim() && !labels.includes(newLabel.trim())) {
      setLabels([...labels, newLabel.trim()])
      setNewLabel('')
    }
  }

  const handleRemoveLabel = (labelToRemove: string) => {
    setLabels(labels.filter(label => label !== labelToRemove))
  }

  const handleSave = () => {
    if (frame) {
      onSave(frame.id, labels, notes)
      onClose()
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAddLabel()
    }
  }

  return (
    <Modal 
      opened={opened} 
      onClose={onClose}
      title="Edit Frame Labels"
      size="lg"
    >
      {frame && (
        <Stack gap="md">
          {/* Frame Preview */}
          <div>
            <Text size="sm" fw={500} mb="xs">Frame Preview</Text>
            <Image
              src={frame.thumbnail}
              height={200}
              alt={`Frame ${frame.id}`}
              style={{ borderRadius: '8px' }}
            />
            <Text size="sm" c="dimmed" mt="xs">
              Timestamp: {frame.timestamp}
            </Text>
          </div>

          <Divider />

          {/* Labels Section */}
          <div>
            <Text size="sm" fw={500} mb="xs">Labels</Text>
            
            {/* Existing Labels */}
            {labels.length > 0 && (
              <Group gap="xs" mb="md">
                {labels.map((label) => (
                  <Group key={label} gap={4}>
                    <Chip
                      checked={true}
                      variant="filled"
                      color="blue"
                    >
                      {label}
                    </Chip>
                    <IconTrash 
                      size={12} 
                      style={{ cursor: 'pointer', color: '#666' }}
                      onClick={() => handleRemoveLabel(label)}
                    />
                  </Group>
                ))}
              </Group>
            )}

            {/* Add New Label */}
            <Group gap="xs">
              <TextInput
                placeholder="Add new label..."
                value={newLabel}
                onChange={(e) => setNewLabel(e.currentTarget.value)}
                onKeyPress={handleKeyPress}
                style={{ flex: 1 }}
              />
              <Button 
                size="sm" 
                onClick={handleAddLabel}
                leftSection={<IconPlus size={14} />}
              >
                Add
              </Button>
            </Group>

            {/* Quick Add Common Labels */}
            <Text size="sm" fw={500} mt="md" mb="xs">Quick Add</Text>
            <Group gap="xs">
              {availableLabels
                .filter(label => !labels.includes(label))
                .slice(0, 8)
                .map((label) => (
                  <Chip
                    key={label}
                    variant="outline"
                    onClick={() => setLabels([...labels, label])}
                    style={{ cursor: 'pointer' }}
                  >
                    {label}
                  </Chip>
                ))}
            </Group>
          </div>

          <Divider />

          {/* Notes Section */}
          <div>
            <Text size="sm" fw={500} mb="xs">Notes</Text>
            <Textarea
              placeholder="Add any additional notes about this frame..."
              value={notes}
              onChange={(e) => setNotes(e.currentTarget.value)}
              rows={3}
            />
          </div>

          {/* Actions */}
          <Group justify="flex-end" gap="xs">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleSave}>
              Save Changes
            </Button>
          </Group>
        </Stack>
      )}
    </Modal>
  )
} 