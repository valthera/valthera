# Camera Docker Container with RealSense Support

This is a multi-architecture Docker container for the camera device with RealSense camera support. 
It can run on both x86_64 (Mac development) and ARM64 (Jetson Nano deployment).

## Install & Use on Jetson Nano (Recommended)

These steps let you reach the camera at a stable name (`http://jetson.local:8000`) without knowing its IP each time.

### 1) Find the Jetson's IP to SSH in (first-time only)

Pick any one method:

- Router/DHCP: open your router's admin page or app and look for the Jetson device to get its IP
- HDMI + keyboard: on the Jetson, run `hostname -I` and note the IP
- Mac (Bonjour/mDNS present): try `ping jetson.local` or `dns-sd -B _workstation._tcp`
- Linux (from another machine): `avahi-browse -art | grep -i jetson`

Then SSH in:

```bash
ssh <user>@<jetson-ip>
```

### 2) Enable mDNS broadcast (so it’s always reachable at jetson.local)

Run on the Jetson:

```bash
bash devices/camera/scripts/setup-mdns.sh jetson "Valthera Camera" 8000
```

This sets hostname, installs Avahi, and advertises an HTTP service on port 8000. After this, the device should be reachable at `jetson.local` on your LAN.

### 3) Deploy the camera service (Docker Compose)

The deploy script installs Docker + Compose plugin + NVIDIA runtime, then brings up the camera service with Jetson overrides (USB, runtime, port 8000). Compose files are local to this folder, so no `edge/` dependency:

```bash
# Adjust REPO_DIR if your repo is not at /opt/valthera/valthera on the Jetson
export REPO_DIR=/opt/valthera/valthera
bash devices/camera/scripts/deploy.sh
```

This builds from `devices/camera/Dockerfile` and starts the container via `edge/compose/docker-compose.yml` with the Jetson override `devices/camera/jetson.camera.override.yml`.

### 4) Test from your laptop

```bash
ping -c 3 jetson.local
curl http://jetson.local:8000/health
```

In your React app, call `http://jetson.local:8000/health` (or your feed endpoint) from clients on the same LAN.

> Note: If your web app runs over HTTPS, the browser will block plain HTTP calls. For production, proxy via your backend or add HTTPS on the Jetson.

## Quick Start

### Using the build script (recommended)

```bash
# Build and run the container (single architecture)
./build.sh

# Build multi-architecture image (Mac + Jetson Nano)
./build_multiarch.sh
```

### Manual Docker commands

```bash
# Build the Docker image
docker build -t camera:latest .

# Run the container (Mac)
docker run --rm camera:latest

# Run the container (Jetson Nano with RealSense)
docker run --rm --runtime nvidia --gpus all \
  --privileged -v /dev/bus/usb:/dev/bus/usb \
  camera:latest

# Run in interactive mode
docker run -it --rm camera:latest /bin/bash
```

## Container Structure

- **Base Image**: Multi-architecture (NVIDIA L4T for Jetson, CUDA for x86)
- **Working Directory**: `/app`
- **Main Script**: `camera/hello_world.py` (with RealSense fallback)
- **RealSense Support**: `camera/realsense_camera.py`
- **Package Manager**: Poetry
- **RealSense SDK**: librealsense2 + pyrealsense2

## Development

### Adding new camera functionality

1. Add your camera-related code to the `camera/` directory
2. Update the `CMD` in the Dockerfile to run your new script
3. Rebuild the container

### RealSense Camera Development

The container includes RealSense SDK support:

```python
# camera/your_realsense_script.py
import pyrealsense2 as rs

def main():
    # Configure RealSense pipeline
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    
    # Start streaming
    profile = pipeline.start(config)
    
    # Process frames
    while True:
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        
        # Your processing logic here
        # ...

if __name__ == "__main__":
    main()
```

### Example: Adding a new camera script

```python
# camera/camera_controller.py
def main():
    print("Camera controller initialized")
    # Add your camera logic here

if __name__ == "__main__":
    main()
```

Then update the Dockerfile:
```dockerfile
CMD ["python3", "camera/camera_controller.py"]
```

## Docker Commands Reference

```bash
# Build with a specific tag
docker build -t camera:v1.0 .

# Build multi-architecture image
docker buildx build --platform linux/amd64,linux/arm64 -t camera:latest .

# Run with environment variables
docker run -e CAMERA_ID=001 camera:latest

# Run with volume mounting (for development)
docker run -v $(pwd)/camera:/app/camera camera:latest

# Run on Jetson Nano with RealSense
docker run --rm --runtime nvidia --gpus all \
  --privileged -v /dev/bus/usb:/dev/bus/usb \
  -e CAMERA_ID=001 camera:latest

# View container logs
docker logs <container_id>

# Stop running container
docker stop <container_id>
```

## Troubleshooting

### Common Issues

1. **Permission denied**: Make sure the build script is executable
   ```bash
   chmod +x build.sh
   chmod +x build_multiarch.sh
   ```

2. **Docker not found**: Install Docker Desktop or Docker Engine

3. **Build fails**: Check that all files are in the correct locations

4. **RealSense not detected**: On Jetson Nano, ensure:
   - Container is run with `--privileged` flag
   - USB devices are mounted: `-v /dev/bus/usb:/dev/bus/usb`
   - RealSense camera is properly connected

5. **Multi-architecture build fails**: Ensure Docker buildx is available:
   ```bash
   docker buildx version
   ```

### Debug Mode

To run the container in debug mode with a shell:

```bash
# For Mac development
docker run -it --rm camera:latest /bin/bash

# For Jetson Nano with RealSense
docker run -it --rm --runtime nvidia --gpus all \
  --privileged -v /dev/bus/usb:/dev/bus/usb \
  camera:latest /bin/bash
```

This will give you an interactive shell inside the container where you can explore and debug.

### RealSense Testing

To test RealSense functionality:

```bash
# Test RealSense devices
docker run --rm --privileged -v /dev/bus/usb:/dev/bus/usb \
  camera:latest rs-enumerate-devices

# Test RealSense Python script
docker run --rm --privileged -v /dev/bus/usb:/dev/bus/usb \
  camera:latest python3 camera/realsense_camera.py
```
