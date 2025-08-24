import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ProjectsProvider } from './contexts/ProjectsContext'
import { FeatureFlagProvider } from './contexts/FeatureFlagsContext'
import { ThemeProvider } from './contexts/ThemeContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { PublicRoute } from './components/PublicRoute'
import { AppShell } from './components/AppShell'
import { SignIn } from './pages/SignIn'
import { SignUp } from './pages/SignUp'
import { ForgotPassword } from './pages/ForgotPassword'
import { Landing } from './pages/Landing'
import { ProjectsDashboard } from './pages/ProjectsDashboard'
import { DefineConcepts } from './pages/DefineConcepts'
import { TrainingPage } from './pages/TrainingPage'
import { EndpointsPage } from './pages/EndpointsPage'
import { ClassifiersPage } from './pages/ClassifiersPage'
import { TrainingOverviewPage } from './pages/TrainingOverviewPage'
import { EndpointsOverviewPage } from './pages/EndpointsOverviewPage'
import { ApiKeysPage } from './pages/ApiKeysPage'
import { SettingsPageNew } from './pages/SettingsPageNew'
import DepthViewer from './pages/DepthViewer'
import { DataSourcesPage } from './pages/DataSourcesPage'
import { DataSourceFolderPage } from './pages/DataSourceFolderPage'
import { ConceptDetailPage } from './pages/ConceptDetailPage'
import './App.css'

function App() {
  return (
    <ThemeProvider>
      <FeatureFlagProvider>
        <AuthProvider>
          <ProjectsProvider>
            <Router>
              <div className="App">
                <Routes>
              {/* Public Routes */}
              <Route
                path="/"
                element={
                  <PublicRoute>
                    <Landing />
                  </PublicRoute>
                }
              />
              <Route
                path="/signin"
                element={
                  <PublicRoute>
                    <SignIn />
                  </PublicRoute>
                }
              />
              <Route
                path="/signup"
                element={
                  <PublicRoute>
                    <SignUp />
                  </PublicRoute>
                }
              />
              <Route
                path="/forgot-password"
                element={
                  <PublicRoute>
                    <ForgotPassword />
                  </PublicRoute>
                }
              />

              {/* Protected Routes - Dashboard */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <ProjectsDashboard />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              
              {/* Global Overview Pages */}
              <Route
                path="/classifiers"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <ClassifiersPage />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/training"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <TrainingOverviewPage />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/endpoints"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <EndpointsPage />
                    </AppShell>
                  </ProtectedRoute>
                }
              />

              {/* Data Sources */}
              <Route
                path="/depth"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <DepthViewer />
                    </AppShell>
                  </ProtectedRoute>
                }
              />

              <Route
                path="/data-sources"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <DataSourcesPage />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/data-sources/:id"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <DataSourceFolderPage />
                    </AppShell>
                  </ProtectedRoute>
                }
              />

              {/* Project Routes */}
              <Route
                path="/projects/:projectId/concepts"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <DefineConcepts />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/projects/:projectId/concepts/:conceptId"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <ConceptDetailPage />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/projects/:projectId/training"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <TrainingPage />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/projects/:projectId/endpoints"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <EndpointsPage />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              
              {/* API Keys */}
              <Route
                path="/api-keys"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <ApiKeysPage />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              
              {/* Settings */}
              <Route
                path="/settings"
                element={
                  <ProtectedRoute>
                    <AppShell>
                      <SettingsPageNew />
                    </AppShell>
                  </ProtectedRoute>
                }
              />
              
              {/* Redirect all other routes to root */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </Router>
          </ProjectsProvider>
        </AuthProvider>
        </FeatureFlagProvider>
    </ThemeProvider>
  )
}

export default App
