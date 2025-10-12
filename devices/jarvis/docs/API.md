# Jarvis Smart CV Pipeline API Documentation

## Overview

The Jarvis Smart CV Pipeline provides a unified API for intelligent computer vision processing with multi-classifier support, real-time streaming, and comprehensive system control.

## Base URL

- **Development**: `http://localhost:8001`
- **Production**: `http://jarvis.local:8001`

## Authentication

No authentication is required for local network access.

## API Versioning

All endpoints are prefixed with `/api/v1/`.

## Response Format

All responses are JSON with the following structure:

```json
{
  "data": "...",
  "timestamp": 1697034190.123,
  "status": "success|error"
}
```

## Core Endpoints

### Health Check

```http
GET /health
```

Returns system health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1697034190.123,
  "version": "2.0.0",
  "center_depth_processor": {
    "running": true,
    "available": true
  },
  "smart_cv_pipeline": {
    "running": true,
    "available": true
  }
}
```

## Analysis Endpoints

### Unified Analysis

```http
POST /api/v1/analyze
```

Main analysis endpoint supporting multiple classifiers and options.

**Request Body:**
```json
{
  "classifiers": ["person", "object", "face"],
  "options": {
    "confidence_threshold": 0.5,
    "include_depth": true,
    "include_3d_position": true,
    "include_annotated_frame": false,
    "max_detections": 10
  },
  "filters": {
    "min_confidence": 0.3,
    "max_distance_mm": 5000,
    "classes": ["person", "car"]
  },
  "frame_id": 123,
  "client_id": "web-app"
}
```

**Response:**
```json
{
  "frame_id": 123,
  "timestamp": 1697034190.123,
  "processing_time_ms": 45.2,
  "detections": {
    "person": [
      {
        "bbox": [100, 50, 200, 300],
        "confidence": 0.85,
        "class_id": 0,
        "class_name": "person",
        "classifier_type": "person",
        "depth_mm": 1500.0,
        "position_3d": {
          "x": 0.1,
          "y": -0.2,
          "z": 1.5
        },
        "attributes": null,
        "processing_time_ms": 15.2,
        "model_version": "8.0"
      }
    ],
    "object": []
  },
  "frame_resolution": [640, 480],
  "pipeline_info": {
    "classifiers_used": ["person"],
    "total_detections": 1,
    "frame_metadata": {
      "frame_id": 123,
      "timestamp": 1697034190.123,
      "resolution": [640, 480],
      "camera_intrinsics": {
        "fx": 615.0,
        "fy": 615.0,
        "ppx": 320.0,
        "ppy": 240.0
      },
      "processing_pipeline": ["person"]
    }
  },
  "cache_hit": false,
  "detection_count": 1
}
```

### Analysis Status

```http
GET /api/v1/analyze/status
```

Get current analysis pipeline status.

### Test Analysis

```http
POST /api/v1/analyze/test
```

Run test analysis with default parameters.

## WebSocket Streaming

### Connection

```javascript
const ws = new WebSocket('ws://jarvis.local:8001/api/v1/stream');
```

### Subscribe to Classifiers

```javascript
ws.send(JSON.stringify({
  action: 'subscribe',
  classifiers: ['person', 'object'],
  options: {
    confidence_threshold: 0.5,
    include_depth: true,
    include_3d_position: true
  },
  filters: {
    min_confidence: 0.3,
    max_distance_mm: 5000
  }
}));
```

### Unsubscribe

```javascript
ws.send(JSON.stringify({
  action: 'unsubscribe'
}));
```

### Ping/Pong

```javascript
ws.send(JSON.stringify({
  action: 'ping'
}));

// Response:
{
  "action": "pong",
  "timestamp": 1697034190.123
}
```

### Analysis Result Messages

```json
{
  "type": "analysis_result",
  "frame_id": 123,
  "timestamp": 1697034190.123,
  "processing_time_ms": 45.2,
  "detections": {
    "person": [...],
    "object": [...]
  },
  "frame_resolution": [640, 480],
  "pipeline_info": {...},
  "cache_hit": false,
  "detection_count": 2
}
```

## Pipeline Control

### System Status

```http
GET /api/v1/status
```

Get detailed system status including pipeline info, classifier stats, and performance metrics.

### Start Pipeline

```http
POST /api/v1/pipeline/start
```

Start the CV pipeline.

### Stop Pipeline

```http
POST /api/v1/pipeline/stop
```

Stop the CV pipeline.

### Reset Pipeline

```http
POST /api/v1/pipeline/reset
```

Reset the CV pipeline (stop and restart).

### Get Configuration

```http
GET /api/v1/pipeline/config
```

Get current pipeline configuration.

### Update Configuration

```http
POST /api/v1/pipeline/config
```

Update pipeline configuration.

**Request Body:**
```json
{
  "fps": 15,
  "confidence_threshold": 0.6,
  "max_detections": 15,
  "enabled_classifiers": ["person", "object"],
  "include_depth": true,
  "include_3d_position": true,
  "include_annotated_frame": false,
  "include_raw_frame": false
}
```

## Classifier Management

### List Classifiers

```http
GET /api/v1/classifiers
```

Get list of all available classifiers.

**Response:**
```json
{
  "classifiers": [
    {
      "name": "person",
      "type": "PersonClassifier",
      "enabled": true,
      "initialized": true,
      "stats": {
        "name": "person",
        "is_enabled": true,
        "is_initialized": true,
        "total_detections": 1250,
        "last_detection_time": 1697034190.123,
        "average_processing_time_ms": 12.5,
        "model_version": "8.0",
        "config": {
          "model_type": "yolo",
          "confidence_threshold": 0.5,
          "classes": [0]
        }
      }
    }
  ],
  "total_count": 3,
  "enabled_count": 2,
  "timestamp": 1697034190.123
}
```

### Get Classifier Info

```http
GET /api/v1/classifiers/{name}
```

Get detailed information about a specific classifier.

### Configure Classifier

```http
POST /api/v1/classifiers/{name}/config
```

Configure a specific classifier.

**Request Body:**
```json
{
  "confidence_threshold": 0.6,
  "enabled": true,
  "model_version": "8.0"
}
```

### Enable Classifier

```http
POST /api/v1/classifiers/{name}/enable
```

Enable a specific classifier.

### Disable Classifier

```http
POST /api/v1/classifiers/{name}/disable
```

Disable a specific classifier.

### Initialize Classifier

```http
POST /api/v1/classifiers/{name}/initialize
```

Initialize a specific classifier.

### Classifier Statistics

```http
GET /api/v1/classifiers/stats
```

Get comprehensive classifier statistics.

### Available Classifier Types

```http
GET /api/v1/classifiers/types
```

Get list of available classifier types.

## Frame Access

### Latest Result

```http
GET /api/v1/latest
```

Get the latest analysis result.

### Annotated Frame

```http
GET /api/v1/frame/annotated
```

Get the latest annotated frame as JPEG image.

### Raw Frame

```http
GET /api/v1/frame/raw
```

Get the latest raw frame as JPEG image.

### Depth Map

```http
GET /api/v1/depth/map
```

Get the latest depth map as JPEG image (colormapped).

### Depth Data

```http
GET /api/v1/depth/data
```

Get the latest depth data as JSON.

**Response:**
```json
{
  "frame_id": 123,
  "timestamp": 1697034190.123,
  "resolution": [640, 480],
  "intrinsics": {
    "fx": 615.0,
    "fy": 615.0,
    "ppx": 320.0,
    "ppy": 240.0
  },
  "has_color_frame": true,
  "has_depth_frame": true
}
```

### Frame Information

```http
GET /api/v1/frame/info
```

Get information about the latest frame.

## Error Handling

### Error Response Format

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "timestamp": 1697034190.123
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service not available

## Rate Limiting

No rate limiting is currently implemented. Consider implementing if needed for production use.

## WebSocket Connection Management

- Connections are automatically cleaned up on disconnect
- Reconnection is handled by the client
- Maximum concurrent connections: 100 (configurable)

## Performance Considerations

- Analysis requests are cached to avoid duplicate processing
- Parallel classifier execution improves performance
- WebSocket streaming reduces latency for real-time applications
- GPU acceleration is used when available

## Examples

### Complete Analysis Workflow

```bash
# 1. Check system health
curl http://jarvis.local:8001/health

# 2. Start pipeline
curl -X POST http://jarvis.local:8001/api/v1/pipeline/start

# 3. Configure classifiers
curl -X POST http://jarvis.local:8001/api/v1/classifiers/person/config \
  -H "Content-Type: application/json" \
  -d '{"confidence_threshold": 0.6, "enabled": true}'

# 4. Run analysis
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

# 5. Get annotated frame
curl http://jarvis.local:8001/api/v1/frame/annotated -o annotated.jpg
```

### WebSocket Client Example

```javascript
class JarvisClient {
  constructor(url = 'ws://jarvis.local:8001/api/v1/stream') {
    this.url = url;
    this.ws = null;
    this.connected = false;
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        this.connected = true;
        resolve();
      };
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      };
      
      this.ws.onclose = () => {
        this.connected = false;
      };
      
      this.ws.onerror = reject;
    });
  }

  subscribe(classifiers, options = {}) {
    this.ws.send(JSON.stringify({
      action: 'subscribe',
      classifiers,
      options
    }));
  }

  handleMessage(data) {
    if (data.type === 'analysis_result') {
      console.log('New detections:', data.detections);
      // Handle detection data
    }
  }
}

// Usage
const client = new JarvisClient();
await client.connect();
client.subscribe(['person', 'object'], {
  confidence_threshold: 0.5,
  include_depth: true
});
```
