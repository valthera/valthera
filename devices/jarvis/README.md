# Jarvis Multi-Modal Agent

A Docker-based multi-modal agent for Jetson Nano that processes audio (microphone) and video (camera) streams using local models without internet connectivity.

## Features

- **Wake Word Detection**: Listens for "Jarvis" using Porcupine (offline)
- **Speech-to-Text**: Transcribes speech using Vosk (offline, local models)
- **Person Detection**: Counts people in camera feed using YOLOv8n (offline)
- **Real-time Logging**: All outputs accessible via logs and HTTP endpoints
- **Jetson Optimized**: Designed for efficient operation on Jetson Nano

## Architecture

- **Audio Processing**: Porcupine wake word detection + Vosk speech-to-text
- **Video Processing**: YOLOv8n person detection (counting people > 0)
- **Deployment**: Docker container with USB device access (mic/camera)
- **Logging**: All outputs to docker logs and `/tmp/jarvis.log`

## Quick Start

### 1) Setup mDNS (so it's reachable at jarvis.local)

Run on the Jetson:

```bash
bash devices/naomi/scripts/setup-mdns.sh naomi "Valthera Naomi" 8001
```

### 2) Deploy Naomi service

```bash
# Adjust REPO_DIR if your repo is not at /opt/valthera/valthera on the Jetson
export REPO_DIR=/opt/valthera/valthera
bash devices/naomi/scripts/deploy.sh
```

### 3) Test from your laptop

```bash
ping -c 3 naomi.local
curl http://naomi.local:8001/health
```

## Usage

### Wake Word Detection

Naomi continuously listens for "Hey Naomi". When detected:

1. Records audio for 3 seconds
2. Transcribes using Vosk
3. Logs the transcription

Example log output:
```
[2025-10-11 15:23:45] [AUDIO] Wake word detected!
[2025-10-11 15:23:48] [AUDIO] Transcription: "what is the weather today"
```

### Person Detection

Naomi continuously processes camera feed:

1. Runs YOLOv8n inference every 0.1 seconds
2. Counts detected people (confidence > 50%)
3. Logs when count changes

Example log output:
```
[2025-10-11 15:23:10] [VIDEO] Detected 2 person(s) in frame
[2025-10-11 15:24:15] [VIDEO] Detected 1 person(s) in frame
```

## API Endpoints

- `GET /` - Basic info about Naomi
- `GET /health` - Health status of audio/video processors
- `GET /status` - Detailed status including person count
- `GET /logs` - Recent log entries (last 100 lines)

## Hardware Requirements

### Jetson Nano
- USB microphone (or built-in mic)
- USB camera (or built-in camera)
- NVIDIA runtime for GPU acceleration
- At least 4GB RAM

### Development Machine
- Docker with buildx support
- No special hardware required for testing

## Directory Structure

```
devices/naomi/
├── docker-compose.yml           # Base compose file
├── jetson.naomi.override.yml    # Jetson-specific overrides
├── Dockerfile                   # Multi-arch with dependencies
├── pyproject.toml               # Python dependencies
├── naomi/                       # Python module
│   ├── __init__.py
│   ├── audio_processor.py       # Wake word + transcription
│   ├── video_processor.py       # YOLOv8 person detection
│   ├── server.py                # FastAPI server
│   └── models/                  # Local model storage
│       ├── porcupine_params/    # Wake word model
│       └── vosk-model-small/    # Speech-to-text model
├── scripts/
│   ├── deploy.sh                # Deployment script
│   └── setup-mdns.sh            # mDNS setup
└── README.md
```

## Development

### Local Testing (without GPU)

```bash
# Build the container
docker build -t naomi:local .

# Run without GPU acceleration
docker run --rm -p 8001:8001 \
  --device /dev/snd:/dev/snd \
  --device /dev/video0:/dev/video0 \
  naomi:local
```

### Testing Individual Components

```bash
# Test audio processor
docker run --rm --device /dev/snd:/dev/snd naomi:local python3 -m naomi.audio_processor

# Test video processor
docker run --rm --device /dev/video0:/dev/video0 naomi:local python3 -m naomi.video_processor
```

### View Logs

```bash
# Docker logs
docker logs -f <container_id>

# HTTP endpoint
curl http://naomi.local:8001/logs
```

## Configuration

### Environment Variables

- `NAOMI_HTTP_PORT`: HTTP server port (default: 8001)

### Audio Settings

- Sample rate: 16kHz
- Wake word: "Hey Naomi"
- Recording duration: 3 seconds after wake word
- Confidence threshold: 50%

### Video Settings

- Resolution: 640x480
- Processing rate: 10 FPS
- Model: YOLOv8n (nano)
- Person class: 0 (COCO dataset)
- Confidence threshold: 50%

## Troubleshooting

### Common Issues

1. **No microphone detected**
   ```bash
   # Check audio devices
   docker run --rm --device /dev/snd:/dev/snd naomi:local python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)['name']}') for i in range(p.get_device_count())]"
   ```

2. **No camera detected**
   ```bash
   # Check video devices
   docker run --rm --device /dev/video0:/dev/video0 naomi:local python3 -c "import cv2; print([i for i in range(5) if cv2.VideoCapture(i).isOpened()])"
   ```

3. **Models not loading**
   - Check if Vosk model downloaded during build
   - Verify model paths in logs

4. **Performance issues on Jetson**
   - Reduce video processing rate in `video_processor.py`
   - Use smaller YOLO model variant
   - Check GPU memory usage

### Debug Mode

```bash
# Interactive shell
docker run -it --rm --device /dev/snd:/dev/snd --device /dev/video0:/dev/video0 naomi:local /bin/bash

# Check logs
docker logs <container_id> 2>&1 | grep -E "\[AUDIO\]|\[VIDEO\]"
```

## Model Information

### Vosk Model
- **Model**: vosk-model-small-en-us-0.15
- **Size**: ~40MB
- **Language**: English (US)
- **Downloaded**: During Docker build

### YOLOv8 Model
- **Model**: yolov8n.pt
- **Size**: ~6MB
- **Classes**: 80 (COCO dataset)
- **Person class**: 0
- **Downloaded**: On first run

### Porcupine
- **Wake word**: "Hey Naomi"
- **Model**: Built-in (no download needed)
- **Offline**: Yes

## Security Notes

- Container runs with `--privileged` for USB device access
- No external network calls (fully offline)
- All processing happens locally
- Logs may contain transcribed speech (consider privacy)

## License

This project uses several open-source libraries:
- Porcupine (Picovoice) - Wake word detection
- Vosk - Speech-to-text
- YOLOv8 (Ultralytics) - Object detection
- FastAPI - Web framework
- OpenCV - Computer vision