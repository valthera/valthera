# Jarvis Web Application

A modern React-based web interface for the Jarvis Smart CV Pipeline, providing real-time visualization, classifier management, and system control.

## Features

- **Real-time Dashboard**: Live detection visualization and statistics
- **Classifier Management**: Enable/disable and configure AI classifiers
- **Settings Panel**: Configure pipeline parameters and options
- **Debug Tools**: Developer tools and system monitoring
- **Responsive Design**: Works on desktop and mobile devices
- **WebSocket Integration**: Real-time data streaming
- **Modern UI**: Built with React, TypeScript, and Tailwind CSS

## Technology Stack

- **React 18**: Modern React with hooks
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API requests
- **Socket.IO Client**: WebSocket communication
- **Lucide React**: Modern icon library

## Development Setup

### Prerequisites

- Node.js 18+ 
- npm or pnpm
- Access to Jarvis API (running on port 8001)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Development Server

The development server runs on port 3000 with:
- Hot module replacement
- API proxy to `http://localhost:8001`
- TypeScript compilation
- Tailwind CSS processing

## Project Structure

```
src/
├── main.tsx                 # App entry point
├── App.tsx                  # Main app component with routing
├── App.css                  # Global styles and Tailwind imports
├── types/
│   └── api.ts              # TypeScript API type definitions
├── services/
│   ├── api.ts              # REST API client
│   └── websocket.ts        # WebSocket client
├── components/
│   ├── StatusPanel.tsx     # Connection status indicator
│   ├── DetectionView.tsx   # Detection visualization component
│   └── VideoFeed.tsx       # Video feed display component
└── pages/
    ├── Dashboard.tsx        # Main dashboard page
    ├── Classifiers.tsx      # Classifier management page
    ├── Settings.tsx         # Configuration page
    └── Debug.tsx            # Debug tools page
```

## Components

### StatusPanel
Displays connection status to the API service with visual indicators.

### DetectionView
Visualizes detections with:
- Bounding box overlay
- Detection details panel
- Summary statistics
- Interactive selection

### VideoFeed
Displays video feeds with:
- Annotated frame
- Raw frame
- Depth map
- Download functionality
- Auto-refresh controls

## Pages

### Dashboard
Main interface showing:
- Real-time detection statistics
- Live detection visualization
- Video feeds
- Latest analysis results

### Classifiers
Classifier management interface:
- List all available classifiers
- Enable/disable classifiers
- View performance statistics
- Initialize classifiers

### Settings
Configuration panel for:
- Pipeline settings (FPS, confidence, etc.)
- Classifier selection
- Output options
- Pipeline control (start/stop/reset)

### Debug
Developer tools including:
- Live detection overlay
- System status monitoring
- JSON result inspection
- Debug controls

## API Integration

### REST API Client
The `JarvisApiClient` provides methods for:
- Analysis requests
- Pipeline control
- Classifier management
- Frame access
- System status

### WebSocket Client
The `JarvisWebSocketClient` handles:
- Real-time streaming
- Connection management
- Subscription management
- Message handling

## Styling

The app uses Tailwind CSS with:
- Custom color scheme
- Responsive design
- Component-specific styles
- Status indicators
- Detection overlays

## Building and Deployment

### Production Build

```bash
# Build the application
npm run build

# Output will be in dist/ directory
```

### Docker Deployment

The web app is containerized with:
- Multi-stage build (Node.js + nginx)
- Optimized production build
- Nginx configuration for serving React app
- API proxy configuration

### Environment Configuration

The app can be configured via environment variables:
- `VITE_API_BASE_URL`: API base URL (default: `/api/v1`)
- `VITE_WS_URL`: WebSocket URL (default: `ws://localhost:8001/api/v1/stream`)

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- Lazy loading of components
- Optimized bundle splitting
- Efficient re-rendering with React hooks
- WebSocket connection pooling
- Image optimization

## Security

- No sensitive data stored locally
- API requests use HTTPS in production
- WebSocket connections are local network only
- No authentication (local network assumption)

## Contributing

1. Follow TypeScript best practices
2. Use Tailwind CSS for styling
3. Maintain component documentation
4. Test with real API endpoints
5. Follow React hooks patterns

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check if Jarvis API is running on port 8001
   - Verify network connectivity
   - Check CORS settings

2. **WebSocket Connection Failed**
   - Ensure WebSocket endpoint is available
   - Check firewall settings
   - Verify WebSocket URL configuration

3. **Build Errors**
   - Clear node_modules and reinstall
   - Check TypeScript configuration
   - Verify all dependencies are installed

4. **Styling Issues**
   - Ensure Tailwind CSS is properly configured
   - Check for CSS conflicts
   - Verify responsive breakpoints
