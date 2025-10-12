# Jarvis Smart CV Pipeline

A Docker-based intelligent computer vision pipeline for Jetson Nano that provides multi-classifier support, real-time analysis, and a modern React web interface.

## 🚀 Features

- **Smart CV Pipeline**: Intelligent processing with multi-classifier support and result caching
- **Multi-Classifier Support**: Person, object, and face detection with unified API
- **Real-time Analysis**: WebSocket streaming and REST API endpoints
- **Modern Web Interface**: React-based dashboard with live visualization
- **3D Positioning**: Depth integration with RealSense camera
- **Efficient Processing**: Parallel classifier execution and result caching
- **Jetson Optimized**: Designed for efficient operation on Jetson Nano

## 🏗️ Architecture

- **Smart CV Pipeline**: Multi-classifier processing with parallel execution
- **Classifier Registry**: Dynamic classifier management and shared model loading
- **Result Cache**: TTL-based caching to avoid duplicate processing
- **Unified API**: REST and WebSocket endpoints for analysis and streaming
- **React Web App**: Modern interface served via nginx
- **Docker Services**: Separate API and web containers with networking

## ⚡ Quick Start

### 1) Setup mDNS (so it's reachable at jarvis.local)

Run on the Jetson:

```bash
bash devices/jarvis/scripts/setup-mdns.sh jarvis "Valthera Jarvis" 8001
```

### 2) Deploy Jarvis services

```bash
# Adjust REPO_DIR if your repo is not at /opt/valthera/valthera on the Jetson
export REPO_DIR=/opt/valthera/valthera
bash devices/jarvis/scripts/deploy.sh
```

### 3) Access the services

```bash
# Web interface
http://jarvis.local:3000

# API health check
curl http://jarvis.local:8001/health

# API documentation
http://jarvis.local:8001/docs
```

## 🔧 Services

### API Service (Port 8001)
- FastAPI backend with smart CV pipeline
- REST endpoints for analysis and control
- WebSocket streaming for real-time data
- Multi-classifier support (person, object, face)
- Health monitoring and logging

### Web Service (Port 3000)
- React-based dashboard with TypeScript
- Real-time visualization and detection overlay
- Classifier management interface
- Settings and debug tools
- Nginx proxy for API requests

## 📡 API Endpoints

### Core Analysis
- `POST /api/v1/analyze` - Unified analysis endpoint
- `GET /api/v1/analyze/status` - Analysis pipeline status
- `POST /api/v1/analyze/test` - Test analysis with default parameters

### WebSocket Streaming
- `WS /api/v1/stream` - Real-time analysis results
- Subscribe/unsubscribe to specific classifiers
- Live detection streaming

### Pipeline Control
- `GET /api/v1/status` - Detailed system status
- `POST /api/v1/pipeline/start` - Start CV pipeline
- `POST /api/v1/pipeline/stop` - Stop CV pipeline
- `POST /api/v1/pipeline/reset` - Reset pipeline
- `GET /api/v1/pipeline/config` - Get configuration
- `POST /api/v1/pipeline/config` - Update configuration

### Classifier Management
- `GET /api/v1/classifiers` - List all classifiers
- `GET /api/v1/classifiers/{name}` - Get classifier info
- `POST /api/v1/classifiers/{name}/config` - Configure classifier
- `POST /api/v1/classifiers/{name}/enable` - Enable classifier
- `POST /api/v1/classifiers/{name}/disable` - Disable classifier
- `POST /api/v1/classifiers/{name}/initialize` - Initialize classifier

### Frame Access
- `GET /api/v1/latest` - Latest analysis result
- `GET /api/v1/frame/annotated` - Annotated frame (JPEG)
- `GET /api/v1/frame/raw` - Raw frame (JPEG)
- `GET /api/v1/depth/map` - Depth map (JPEG)
- `GET /api/v1/depth/data` - Depth data (JSON)

## 💻 Usage Examples

### REST API Analysis

```bash
# Analyze with person detection
curl -X POST http://jarvis.local:8001/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "classifiers": ["person"],
    "options": {
      "confidence_threshold": 0.5,
      "include_depth": true,
      "include_3d_position": true
    }
  }'

# Analyze with multiple classifiers
curl -X POST http://jarvis.local:8001/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "classifiers": ["person", "object", "face"],
    "options": {
      "confidence_threshold": 0.3,
      "include_depth": true,
      "include_3d_position": true,
      "max_detections": 20
    },
    "filters": {
      "min_confidence": 0.2,
      "max_distance_mm": 5000
    }
  }'
```

### WebSocket Streaming

```javascript
const ws = new WebSocket('ws://jarvis.local:8001/api/v1/stream');

ws.onopen = () => {
  // Subscribe to person and object detection
  ws.send(JSON.stringify({
    action: 'subscribe',
    classifiers: ['person', 'object'],
    options: {
      confidence_threshold: 0.5,
      include_depth: true,
      include_3d_position: true
    }
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'analysis_result') {
    console.log('Detections:', data.detections);
    console.log('Frame ID:', data.frame_id);
    console.log('Processing time:', data.processing_time_ms + 'ms');
  }
};
```

### Pipeline Control

```bash
# Start pipeline
curl -X POST http://jarvis.local:8001/api/v1/pipeline/start

# Update configuration
curl -X POST http://jarvis.local:8001/api/v1/pipeline/config \
  -H "Content-Type: application/json" \
  -d '{
    "fps": 15,
    "confidence_threshold": 0.6,
    "max_detections": 15,
    "enabled_classifiers": ["person", "object"],
    "include_depth": true,
    "include_3d_position": true
  }'

# Get system status
curl http://jarvis.local:8001/api/v1/status
```

## 🌐 Web Interface

The React web interface provides:

### Dashboard
- Real-time detection visualization
- Live video feeds (annotated, raw, depth)
- Detection statistics and summaries
- WebSocket connection status

### Classifiers
- Manage available classifiers
- Enable/disable classifiers
- View performance statistics
- Initialize classifiers

### Settings
- Configure pipeline parameters
- Adjust processing settings
- Control output options
- Pipeline start/stop/reset

### Debug
- Developer tools and debug information
- Live detection overlay
- JSON result inspection
- System status monitoring

## 🖥️ Hardware Requirements

### Jetson Nano
- USB camera (or built-in camera)
- RealSense depth camera (D435i recommended)
- NVIDIA runtime for GPU acceleration
- At least 4GB RAM

### Development Machine
- Docker with buildx support
- Node.js for web development (optional)
- No special hardware required for testing

## 📁 Directory Structure

```
devices/jarvis/
├── docker-compose.yml              # Multi-service compose file
├── jetson.jarvis.override.yml     # Jetson-specific overrides
├── Dockerfile                      # API service container
├── pyproject.toml                  # Python dependencies
├── jarvis/                         # Python module
│   ├── __init__.py
│   ├── server.py                   # FastAPI server
│   ├── models/                     # Data models
│   │   ├── __init__.py
│   │   └── base.py                 # Unified detection models
│   ├── classifiers/                # AI classifiers
│   │   ├── __init__.py
│   │   ├── registry.py             # Classifier registry
│   │   ├── person_classifier.py    # Person detection
│   │   ├── object_classifier.py    # Object detection
│   │   └── face_classifier.py      # Face detection
│   ├── core/                       # Core functionality
│   │   ├── __init__.py
│   │   ├── cache.py                # Result caching
│   │   └── smart_pipeline.py       # Smart CV pipeline
│   ├── api/                        # API endpoints
│   │   ├── __init__.py
│   │   └── v1/                     # API v1
│   │       ├── __init__.py
│   │       ├── analyze.py          # Analysis endpoints
│   │       ├── stream.py           # WebSocket streaming
│   │       ├── pipeline.py         # Pipeline control
│   │       ├── classifiers.py      # Classifier management
│   │       └── frames.py           # Frame access
│   ├── depth_camera.py             # RealSense interface
│   └── center_depth_processor.py  # Depth processing
├── web/                            # React web application
│   ├── Dockerfile                  # Web service container
│   ├── nginx.conf                  # Nginx configuration
│   ├── package.json                # Node.js dependencies
│   ├── vite.config.ts              # Vite configuration
│   ├── tailwind.config.js          # Tailwind CSS config
│   └── src/                        # React source code
│       ├── main.tsx                # App entry point
│       ├── App.tsx                  # Main app component
│       ├── types/                   # TypeScript types
│       │   └── api.ts              # API type definitions
│       ├── services/                # API clients
│       │   ├── api.ts              # REST API client
│       │   └── websocket.ts        # WebSocket client
│       ├── components/              # React components
│       │   ├── StatusPanel.tsx     # Connection status
│       │   ├── DetectionView.tsx   # Detection visualization
│       │   └── VideoFeed.tsx       # Video feed display
│       └── pages/                   # Page components
│           ├── Dashboard.tsx        # Main dashboard
│           ├── Classifiers.tsx      # Classifier management
│           ├── Settings.tsx        # Configuration
│           └── Debug.tsx            # Debug tools
├── scripts/
│   ├── deploy.sh                   # Deployment script
│   ├── dev.sh                      # Development script
│   └── setup-mdns.sh              # mDNS setup
└── README.md
```

## 🛠️ Development

### Local Development

```bash
# Start development environment
bash devices/jarvis/scripts/dev.sh

# This will start:
# - API service on port 8001
# - Web dev server on port 3000
# - Hot reload for both services
```

### Manual Service Management

```bash
# Start all services
sudo docker compose up -d

# Start specific service
sudo docker compose up -d jarvis-api
sudo docker compose up -d jarvis-web

# Stop all services
sudo docker compose down

# View logs
sudo docker compose logs -f jarvis-api
sudo docker compose logs -f jarvis-web

# Restart services
sudo docker compose restart
```

### Building Services

```bash
# Build API service
docker build -t jarvis-api:local .

# Build web service
cd web
docker build -t jarvis-web:local .
```

### Testing Individual Components

```bash
# Test smart pipeline
docker run --rm jarvis-api:local python3 -m jarvis.core.smart_pipeline

# Test classifiers
docker run --rm jarvis-api:local python3 -m jarvis.classifiers.person_classifier
docker run --rm jarvis-api:local python3 -m jarvis.classifiers.object_classifier
docker run --rm jarvis-api:local python3 -m jarvis.classifiers.face_classifier

# Test API endpoints
curl http://jarvis.local:8001/api/v1/health
curl http://jarvis.local:8001/api/v1/classifiers
```

## ⚙️ Configuration

### Environment Variables

- `JARVIS_HTTP_PORT`: API server port (default: 8001)

### Pipeline Settings

- **FPS**: Processing frames per second (default: 10)
- **Confidence Threshold**: Minimum detection confidence (default: 0.5)
- **Max Detections**: Maximum detections per frame (default: 10)
- **Enabled Classifiers**: Active classifiers (default: ["person"])
- **Include Depth**: Enable depth information (default: true)
- **Include 3D Position**: Enable 3D positioning (default: true)

### Classifier Settings

- **Person Classifier**: YOLOv8n with person class filtering
- **Object Classifier**: YOLOv8n with all 80 COCO classes
- **Face Classifier**: YOLOv8n with face detection (placeholder for future models)

## 🔍 Troubleshooting

### Common Issues

1. **Services not starting**
   ```bash
   # Check service status
   sudo docker compose ps
   
   # View logs
   sudo docker compose logs jarvis-api
   sudo docker compose logs jarvis-web
   ```

2. **WebSocket connection failed**
   ```bash
   # Check API service
   curl http://jarvis.local:8001/health
   
   # Test WebSocket endpoint
   wscat -c ws://jarvis.local:8001/api/v1/stream
   ```

3. **No detections**
   ```bash
   # Check classifier status
   curl http://jarvis.local:8001/api/v1/classifiers
   
   # Test analysis endpoint
   curl -X POST http://jarvis.local:8001/api/v1/analyze/test
   ```

4. **Performance issues**
   - Reduce FPS in pipeline settings
   - Disable unused classifiers
   - Check GPU memory usage
   - Monitor cache hit rates

5. **404 errors on API endpoints**
   - Ensure API service is running: `sudo docker compose ps`
   - Check API health: `curl http://jarvis.local:8001/health`
   - Verify pipeline is started: `curl -X POST http://jarvis.local:8001/api/v1/pipeline/start`

### Debug Mode

```bash
# Interactive shell
sudo docker compose exec jarvis-api /bin/bash

# Check logs
sudo docker compose logs -f jarvis-api | grep -E "\[SMART_PIPELINE\]|\[CLASSIFIER\]|\[API\]"
```

## 🤖 Model Information

### YOLOv8 Models
- **Person**: yolov8n.pt (person class only)
- **Object**: yolov8n.pt (all 80 COCO classes)
- **Face**: yolov8n.pt (placeholder for dedicated face model)
- **Size**: ~6MB each
- **Downloaded**: On first run

### RealSense SDK
- **Version**: 2.54.0
- **Hardware**: D435i recommended
- **Streams**: Color + Depth
- **Alignment**: Depth-to-color

## 🔒 Security Notes

- Container runs with `--privileged` for USB device access
- No external network calls (fully offline)
- All processing happens locally
- WebSocket connections are not authenticated (local network only)
- Depth data may contain sensitive spatial information

## 📄 License

This project uses several open-source libraries:
- YOLOv8 (Ultralytics) - Object detection
- FastAPI - Web framework
- React - Web interface
- OpenCV - Computer vision
- RealSense SDK - Depth camera interface
- Tailwind CSS - Styling
- Vite - Build tool