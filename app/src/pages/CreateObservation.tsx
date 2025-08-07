import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Container, Stack, Text, TextInput, Button, Box } from '@mantine/core'
import { AltAppShell } from '../components/AltAppShell'
import { useObservations } from '../contexts/ObservationsContext'
import type { Concept } from '../lib/api'

export default function CreateObservation() {
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { observations, addObservation } = useObservations()

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Observation name is required')
      return
    }
    
    try {
      // For now, use a default project ID or get it from context/route params
      // This should be updated to get the actual project ID from the route or context
      const projectId = '1' // TODO: Get actual project ID
      const newObservation = await addObservation(projectId, name.trim())
      navigate(`/observations/${newObservation.slug}/data-manager`)
    } catch (error) {
      setError('Failed to create observation')
      console.error('Error creating observation:', error)
    }
  }

  // Prepare observations for AltAppShell (none active, all existing observations shown)
  const observationItems = observations.map((o: Concept) => ({ name: o.name, active: false }))

  // Make observations clickable
  const onSelectObservation = (name: string) => {
    console.log('Clicked observation:', name)
    const o = observations.find((o: Concept) => o.name.trim().toLowerCase() === name.trim().toLowerCase())
    console.log('Matched observation:', o)
    if (o) navigate(`/observations/${o.slug}/data-manager`)
  }

  return (
    <AltAppShell
      sidebarItems={[]}
      appName="Valthera"
      breadcrumbs={null}
      observations={observationItems}
      currentObservation={''}
      onSelectObservation={onSelectObservation}
      onNewObservation={() => {}}
    >
      <Container size="xs" py="xl">
        <Stack gap="lg">
          <Text fw={700} size="xl">Create New Observation</Text>
          <TextInput
            label="Observation Name"
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