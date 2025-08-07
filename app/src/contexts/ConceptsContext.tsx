import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import { api, type Concept } from '../lib/api'

interface ConceptsContextType {
  concepts: Concept[]
  loading: boolean
  error: string | null
  addConcept: (projectId: string, name: string) => Promise<Concept>
  loadConcepts: (projectId: string) => Promise<void>
  refreshConcepts: (projectId: string) => Promise<void>
}

const ConceptsContext = createContext<ConceptsContextType | undefined>(undefined)

export function ConceptsProvider({ children }: { children: ReactNode }) {
  const [concepts, setConcepts] = useState<Concept[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadConcepts = async (projectId: string): Promise<void> => {
    try {
      setLoading(true)
      setError(null)
      const apiConcepts = await api.concepts.list(projectId)
      
      // Convert API concepts to our interface
      const convertedConcepts: Concept[] = apiConcepts.map((c: any) => ({
        id: c.id,
        name: c.name,
        slug: c.name.toLowerCase().replace(/\s+/g, '-'),
        projectId: c.projectId,
        sampleCount: c.sampleCount,
        uploadedAt: c.uploadedAt
      }))
      
      setConcepts(convertedConcepts)
    } catch (error) {
      console.error('Failed to load concepts:', error)
      setError(error instanceof Error ? error.message : 'Failed to load concepts')
      setConcepts([])
    } finally {
      setLoading(false)
    }
  }

  const addConcept = async (projectId: string, name: string): Promise<Concept> => {
    try {
      setError(null)
      const newApiConcept = await api.concepts.create(projectId, { name })
      
      const newConcept: Concept = {
        id: newApiConcept.id,
        name: newApiConcept.name,
        slug: newApiConcept.name.toLowerCase().replace(/\s+/g, '-'),
        projectId: newApiConcept.projectId,
        sampleCount: newApiConcept.sampleCount,
        uploadedAt: newApiConcept.uploadedAt
      }
      
      setConcepts(prev => [...prev, newConcept])
      return newConcept
    } catch (error) {
      console.error('Failed to create concept:', error)
      setError(error instanceof Error ? error.message : 'Failed to create concept')
      throw error
    }
  }

  const refreshConcepts = async (projectId: string): Promise<void> => {
    await loadConcepts(projectId)
  }

  return (
    <ConceptsContext.Provider value={{ 
      concepts, 
      loading, 
      error, 
      addConcept, 
      loadConcepts, 
      refreshConcepts 
    }}>
      {children}
    </ConceptsContext.Provider>
  )
}

export function useConcepts() {
  const ctx = useContext(ConceptsContext)
  if (!ctx) throw new Error('useConcepts must be used within ConceptsProvider')
  return ctx
} 