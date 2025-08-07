import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { type Project } from '../lib/api';
import { api } from '../lib/api';

interface ProjectsContextType {
  projects: Project[];
  loading: boolean;
  error: string | null;
  refreshProjects: () => Promise<void>;
  createProject: (data: { name: string; description: string; hasDroidDataset: boolean; linkedDataSources: string[] }) => Promise<Project>;
}

const ProjectsContext = createContext<ProjectsContextType | undefined>(undefined);

export function ProjectsProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Loading projects...');
      const data = await api.getProjects();
      console.log('Loaded projects data:', data);
      
      // Ensure data is an array before setting it
      if (Array.isArray(data)) {
        console.log('Setting projects:', data);
        console.log('Full project data:', JSON.stringify(data, null, 2));
        setProjects(data);
      } else {
        console.warn('API returned non-array data for projects:', data);
        setProjects([]);
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
      setError('Failed to load projects');
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  const createProject = async (data: { name: string; description: string; hasDroidDataset: boolean; linkedDataSources: string[] }): Promise<Project> => {
    try {
      console.log('Creating project with data:', data);
      const newProject = await api.createProject(data);
      console.log('Created project:', newProject);
      setProjects(prevProjects => {
        const updatedProjects = [newProject, ...prevProjects];
        console.log('Updated projects list:', updatedProjects);
        return updatedProjects;
      });
      return newProject;
    } catch (error) {
      console.error('Failed to create project:', error);
      throw error;
    }
  };

  useEffect(() => {
    refreshProjects();
  }, []);

  const value: ProjectsContextType = {
    projects,
    loading,
    error,
    refreshProjects,
    createProject,
  };

  return (
    <ProjectsContext.Provider value={value}>
      {children}
    </ProjectsContext.Provider>
  );
}

export function useProjects() {
  const context = useContext(ProjectsContext);
  if (context === undefined) {
    throw new Error('useProjects must be used within a ProjectsProvider');
  }
  return context;
} 