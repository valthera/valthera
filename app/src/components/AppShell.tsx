import type { ReactNode } from 'react';
import { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { 
  FolderOpen, 
  Target, 
  Zap, 
  Plug, 
  Key, 
  Settings, 
  LogOut,
  ChevronDown,
  ChevronRight,
  FileText,
  Plus,
  Menu,
  X,
  Brain,
  Database
} from 'lucide-react';
import { cn } from '../lib/utils';
import { useProjects } from '../contexts/ProjectsContext';
import { AIAssistantWrapper } from './AIAssistantWrapper';
import { FeatureFlagToggle } from './FeatureFlagToggle';
import { useFeatureFlag } from '../contexts/FeatureFlagsContext';
import { useTheme } from '../contexts/ThemeContext';
import { ThemeToggle } from './ThemeToggle';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const { user, signOut } = useAuth();
  const { projects, loading } = useProjects();
  const { theme } = useTheme();
  const location = useLocation();
  const [projectsExpanded, setProjectsExpanded] = useState(false);
  const isAIAssistantEnabled = useFeatureFlag('aiResearchAssistant');
  const prevAIAssistantEnabledRef = useRef(isAIAssistantEnabled);
  

  
  // Layout state management
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chatOpen, setChatOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [chatWidth, setChatWidth] = useState(320); // Default width in pixels
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    // Auto-expand projects if we're in a project-specific route
    if (location.pathname.startsWith('/projects/')) {
      setProjectsExpanded(true);
    }
  }, [location.pathname]);

  // Media query effect for mobile detection
  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    
    checkIsMobile();
    window.addEventListener('resize', checkIsMobile);
    return () => window.removeEventListener('resize', checkIsMobile);
  }, []);

  // Mobile responsive behavior
  useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false);
      setChatOpen(false);
    } else {
      // Restore from localStorage or defaults
      const savedSidebar = localStorage.getItem('sidebar-open');
      const savedChat = localStorage.getItem('chat-open');
      const savedChatWidth = localStorage.getItem('chat-width');
      setSidebarOpen(savedSidebar !== null ? JSON.parse(savedSidebar) : true);
      // Only restore chat state if AI Assistant is enabled
      setChatOpen(isAIAssistantEnabled && (savedChat !== null ? JSON.parse(savedChat) : true));
      setChatWidth(savedChatWidth !== null ? JSON.parse(savedChatWidth) : 320);
    }
  }, [isMobile, isAIAssistantEnabled]);

  // When the feature flag is toggled ON (e.g., via URL), auto-open the panel
  useEffect(() => {
    const wasEnabled = prevAIAssistantEnabledRef.current;
    if (!isMobile && isAIAssistantEnabled && !wasEnabled) {
      setChatOpen(true);
    }
    prevAIAssistantEnabledRef.current = isAIAssistantEnabled;
  }, [isMobile, isAIAssistantEnabled]);

  // Persist state to localStorage
  useEffect(() => {
    if (!isMobile) {
      localStorage.setItem('sidebar-open', JSON.stringify(sidebarOpen));
    }
  }, [sidebarOpen, isMobile]);

  useEffect(() => {
    if (!isMobile && isAIAssistantEnabled) {
      localStorage.setItem('chat-open', JSON.stringify(chatOpen));
    }
  }, [chatOpen, isMobile, isAIAssistantEnabled]);

  useEffect(() => {
    if (!isMobile && isAIAssistantEnabled) {
      localStorage.setItem('chat-width', JSON.stringify(chatWidth));
    }
  }, [chatWidth, isMobile, isAIAssistantEnabled]);

  // Chat resize functionality
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (isResizing) {
        const newWidth = window.innerWidth - e.clientX;
        if (newWidth >= 200 && newWidth <= 600) {
          setChatWidth(newWidth);
        }
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const handleSignOut = async () => {
    await signOut();
  };

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const isProjectActive = (projectId: string) => {
    return location.pathname.includes(`/projects/${projectId}`);
  };

  const mainNavItems = [
    { path: '/classifiers', label: 'Classifiers', icon: Target },
    { path: '/training', label: 'Training', icon: Zap },
    { path: '/endpoints', label: 'Endpoints', icon: Plug },
    { path: '/data-sources', label: 'Data Sources', icon: Database },
  ];

  const bottomNavItems = [
    { path: '/api-keys', label: 'API Keys', icon: Key },
    { path: '/settings', label: 'Settings', icon: Settings },
  ];

  // Calculate dynamic layout dimensions
  const contentMarginLeft = sidebarOpen && !isMobile ? '256px' : '0px';
  const contentMarginRight = (chatOpen && !isMobile && isAIAssistantEnabled) ? `${chatWidth}px` : '0px';
  const headerLeft = sidebarOpen && !isMobile ? '256px' : '0px';
  const headerRight = (chatOpen && !isMobile && isAIAssistantEnabled) ? `${chatWidth}px` : '0px';

  return (
    <div className={cn(
      "min-h-screen relative transition-colors duration-200",
      theme === 'dark' ? 'bg-gray-900' : 'bg-white'
    )}>
      {/* Mobile Overlay */}
      {isMobile && (sidebarOpen || (chatOpen && isAIAssistantEnabled)) && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => {
            setSidebarOpen(false);
            setChatOpen(false);
          }}
        />
      )}

      {/* Sidebar */}
      <div 
        className={cn(
          "fixed inset-y-0 left-0 transition-transform duration-300 z-50 border-r",
          isMobile ? "w-full md:w-64" : "w-64",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
          theme === 'dark' 
            ? 'bg-gray-800 border-gray-700' 
            : 'bg-white border-gray-200'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className={cn(
            "px-6 h-16 border-b",
            theme === 'dark' ? 'border-gray-700' : 'border-gray-200'
          )}>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <img src="/logo.svg" alt="Valthera" className="h-14 w-14 logo-invert" />
                <span className={cn(
                  "text-xl font-semibold",
                  theme === 'dark' ? 'text-white' : 'text-black'
                )}>Valthera</span>
              </div>
              {isMobile && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSidebarOpen(false)}
                  className="p-1"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>

          {/* Main Navigation */}
          <div className="flex-1 p-4">
            <nav className="space-y-1">
              {/* Projects Section */}
              <div>
                <button
                  onClick={() => setProjectsExpanded(!projectsExpanded)}
                  className={cn(
                    'flex items-center w-full px-3 py-2 text-sm font-medium transition-colors',
                    (isActive('/dashboard') || location.pathname.startsWith('/projects/'))
                      ? theme === 'dark' 
                        ? 'bg-gray-700 text-white' 
                        : 'bg-black text-white'
                      : theme === 'dark'
                        ? 'text-gray-300 hover:bg-gray-700'
                        : 'text-gray-700 hover:bg-gray-100'
                  )}
                  style={{ borderRadius: '4px' }}
                >
                  <FolderOpen className="mr-3 h-4 w-4" />
                  Projects
                  {projectsExpanded ? (
                    <ChevronDown className="ml-auto h-4 w-4" />
                  ) : (
                    <ChevronRight className="ml-auto h-4 w-4" />
                  )}
                </button>
                
                {/* Projects Subtree */}
                {projectsExpanded && (
                  <div className="ml-4 mt-1 space-y-1">
                    <Link
                      to="/dashboard"
                      className={cn(
                        'flex items-center px-3 py-2 text-sm transition-colors',
                        location.pathname === '/dashboard'
                          ? theme === 'dark'
                            ? 'bg-gray-700 text-white font-medium'
                            : 'bg-gray-100 text-black font-medium'
                          : theme === 'dark'
                            ? 'text-gray-400 hover:bg-gray-700'
                            : 'text-gray-600 hover:bg-gray-50'
                      )}
                      style={{ borderRadius: '4px' }}
                    >
                      <Plus className="mr-2 h-3 w-3" />
                      All Projects
                    </Link>
                    
                    {!loading && Array.isArray(projects) && projects.length > 0 &&
                      projects.map((project) => (
                        <Link
                          key={project.id}
                          to={`/projects/${project.id}/concepts`}
                          className={cn(
                            'flex items-center px-3 py-2 text-sm transition-colors',
                            isProjectActive(project.id)
                              ? theme === 'dark'
                                ? 'bg-gray-700 text-white font-medium'
                                : 'bg-gray-100 text-black font-medium'
                              : theme === 'dark'
                                ? 'text-gray-400 hover:bg-gray-700'
                                : 'text-gray-600 hover:bg-gray-50'
                          )}
                          style={{ borderRadius: '4px' }}
                        >
                          <FileText className="mr-2 h-3 w-3" />
                          {project.name}
                        </Link>
                      ))}
                  </div>
                )}
              </div>

              {/* Other Main Nav Items */}
              {mainNavItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      'flex items-center px-3 py-2 text-sm font-medium transition-colors',
                      isActive(item.path)
                        ? theme === 'dark'
                          ? 'bg-gray-700 text-white'
                          : 'bg-black text-white'
                        : theme === 'dark'
                          ? 'text-gray-300 hover:bg-gray-700'
                          : 'text-gray-700 hover:bg-gray-100'
                    )}
                    style={{ borderRadius: '4px' }}
                  >
                    <Icon className="mr-3 h-4 w-4" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Bottom Navigation */}
          <div className={cn(
            "p-4 border-t",
            theme === 'dark' ? 'border-gray-700' : 'border-gray-200'
          )}>
            <nav className="space-y-1">
              {bottomNavItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      'flex items-center px-3 py-2 text-sm font-medium transition-colors',
                      isActive(item.path)
                        ? theme === 'dark'
                          ? 'bg-gray-700 text-white'
                          : 'bg-black text-white'
                        : theme === 'dark'
                          ? 'text-gray-300 hover:bg-gray-700'
                          : 'text-gray-700 hover:bg-gray-100'
                    )}
                    style={{ borderRadius: '4px' }}
                  >
                    <Icon className="mr-3 h-4 w-4" />
                    {item.label}
                  </Link>
                );
              })}
              <Button
                variant="ghost"
                className={cn(
                  "w-full justify-start px-3 py-2 transition-colors",
                  theme === 'dark'
                    ? 'text-gray-300 hover:bg-gray-700'
                    : 'text-gray-700 hover:bg-gray-100'
                )}
                onClick={handleSignOut}
                style={{ borderRadius: '4px' }}
              >
                <LogOut className="mr-3 h-4 w-4" />
                Sign out
              </Button>
            </nav>
          </div>
        </div>
      </div>

      {/* Header */}
      <div 
        className={cn(
          "fixed top-0 h-16 z-30 transition-all duration-300 border-b",
          theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        )}
        style={{
          left: headerLeft,
          right: headerRight
        }}
      >
        <div className="flex items-center justify-between h-full px-6">
          {/* Left side - Mobile menu */}
          <div className="flex items-center space-x-4">
            {(!sidebarOpen || isMobile) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(true)}
                className="p-2"
              >
                <Menu className="h-4 w-4" />
              </Button>
            )}
            {isMobile && (
              <div className="flex items-center space-x-2">
                <img src="/logo.svg" alt="Valthera" className="h-12 w-12 logo-invert" />
                <span className={cn(
                  "text-lg font-semibold",
                  theme === 'dark' ? 'text-white' : 'text-black'
                )}>Valthera</span>
              </div>
            )}
          </div>

          {/* Right side - User info, theme toggle, and chat toggle */}
          <div className="flex items-center space-x-3">
            <span className={cn(
              "text-sm hidden sm:inline",
              theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
            )}>{user?.email}</span>
            
            {/* Theme Toggle */}
            <ThemeToggle />
            
            {isAIAssistantEnabled && (!chatOpen || isMobile) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setChatOpen(true)}
                className="p-2"
              >
                <Brain className="h-4 w-4" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSignOut}
              className="p-2"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div 
        className="pt-16 transition-all duration-300"
        style={{
          marginLeft: contentMarginLeft,
          marginRight: contentMarginRight
        }}
      >
        <div className="min-h-screen p-6">
          {children}
        </div>
      </div>

      {/* AI Assistant Panel */}
      {isAIAssistantEnabled && (
        <AIAssistantWrapper
          isOpen={chatOpen}
          onClose={() => setChatOpen(false)}
          width={chatWidth}
          isMobile={isMobile}
          onResize={handleMouseDown}
        />
      )}

      {/* Feature Flag Toggle (Development Only) */}
      {import.meta.env.DEV && (
        <div
          className="fixed bottom-4 z-50"
          style={{
            right: chatOpen && !isMobile && isAIAssistantEnabled ? `${chatWidth + 16}px` : '16px'
          }}
        >
          <FeatureFlagToggle />
        </div>
      )}
    </div>
  );
}