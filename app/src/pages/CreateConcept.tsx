import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Container, Stack, Text, TextInput, Button, Box } from '@mantine/core'
import { AltAppShell } from '../components/AltAppShell'
import { useConcepts } from '../contexts/ConceptsContext'
import type { Concept } from '../lib/api'

export default function CreateConcept() {
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { concepts, addConcept } = useConcepts()

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Concept name is required')
      return
    }
    
    try {
      // For now, use a default project ID or get it from context/route params
      // This should be updated to get the actual project ID from the route or context
      const projectId = '1' // TODO: Get actual project ID
      const newConcept = await addConcept(projectId, name.trim())
      navigate(`/concepts/${newConcept.slug}/data-manager`)
    } catch (error) {
      setError('Failed to create concept')
      console.error('Error creating concept:', error)
    }
  }

  // Prepare concepts for AltAppShell (none active, all existing concepts shown)
  const conceptItems = concepts.map((c: Concept) => ({ name: c.name, active: false }))

  // Make concepts clickable
  const onSelectConcept = (name: string) => {
    console.log('Clicked concept:', name)
    const c = concepts.find(c => c.name.trim().toLowerCase() === name.trim().toLowerCase())
    console.log('Matched concept:', c)
    if (c) navigate(`/concepts/${c.slug}/data-manager`)
  }

  return (
    <AltAppShell
      sidebarItems={[]}
      appName="Valthera"
      breadcrumbs={null}
      concepts={conceptItems}
      currentConcept={''}
      onSelectConcept={onSelectConcept}
      onNewConcept={() => {}}
    >
      <Container size="xs" py="xl">
        <Stack gap="lg">
          <Text fw={700} size="xl">Create New Concept</Text>
          <TextInput
            label="Concept Name"
            placeholder="e.g. Human Entry"
            value={name}
            onChange={e => setName(e.currentTarget.value)}
            error={error}
            required
          />
          <Box>
            <Button onClick={handleSave} fullWidth>Create & Save</Button>
          </Box>
        </Stack>
      </Container>
    </AltAppShell>
  )
} 