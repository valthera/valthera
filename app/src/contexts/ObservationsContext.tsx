import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { api, type Concept } from '../lib/api';

// Alias Observation as Concept for backward compatibility
type Observation = Concept;

interface ObservationsContextType {
  observations: Observation[];
  loading: boolean;
  error: string | null;
  addObservation: (projectId: string, name: string) => Promise<Observation>;
  updateObservation: (projectId: string, observationId: string, data: Partial<Observation>) => Promise<Observation>;
  deleteObservation: (projectId: string, observationId: string) => Promise<void>;
  refreshObservations: (projectId: string) => Promise<void>;
}

const ObservationsContext = createContext<ObservationsContextType | undefined>(undefined);

interface ObservationsProviderProps {
  children: ReactNode;
  projectId?: string;
}

export function ObservationsProvider({ children, projectId }: ObservationsProviderProps) {
  const [observations, setObservations] = useState<Observation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshObservations = async (pid: string) => {
    if (!pid) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const concepts = await api.concepts.list(pid);
      setObservations(concepts);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load observations');
      console.error('Error loading observations:', err);
    } finally {
      setLoading(false);
    }
  };

  const addObservation = async (pid: string, name: string): Promise<Observation> => {
    try {
      const newConcept = await api.concepts.create(pid, { name });
      setObservations(prev => [...prev, newConcept]);
      return newConcept;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create observation';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  const updateObservation = async (pid: string, observationId: string, data: Partial<Observation>): Promise<Observation> => {
    try {
      const updatedConcept = await api.concepts.update(pid, observationId, data);
      setObservations(prev => prev.map(o => o.id === observationId ? updatedConcept : o));
      return updatedConcept;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update observation';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  const deleteObservation = async (pid: string, observationId: string): Promise<void> => {
    try {
      await api.concepts.delete(pid, observationId);
      setObservations(prev => prev.filter(o => o.id !== observationId));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete observation';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  // Load observations when projectId changes
  useEffect(() => {
    if (projectId) {
      refreshObservations(projectId);
    }
  }, [projectId]);

  const value: ObservationsContextType = {
    observations,
    loading,
    error,
    addObservation,
    updateObservation,
    deleteObservation,
    refreshObservations,
  };

  return (
    <ObservationsContext.Provider value={value}>
      {children}
    </ObservationsContext.Provider>
  );
}

export function useObservations(): ObservationsContextType {
  const context = useContext(ObservationsContext);
  if (context === undefined) {
    throw new Error('useObservations must be used within an ObservationsProvider');
  }
  return context;
} 