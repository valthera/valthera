# FFmpeg Layer

This Lambda layer provides FFmpeg binaries and video processing libraries for Valthera Lambda functions.

## Contents

- **ffmpeg**: FFmpeg binary for video processing
- **ffprobe**: FFprobe binary for video metadata
- **python/**: Python dependencies for video processing

## Dependencies

This layer uses Poetry for dependency management. Dependencies include:

- opencv-python: Computer vision library
- numpy: Numerical computing
- Pillow: Image processing
- boto3: AWS SDK
- requests: HTTP client
- python-dateutil: Date utilities

## Building

To build this layer:

```bash
cd lambdas/layers/ffmpeg
poetry install
poetry export -f requirements.txt --output requirements.txt --without-hashes
pip install -r requirements.txt -t python/
```

Or use the build script:

```bash
./lambdas/shared/scripts/build-layers.sh
```

## Usage

In your Lambda function, you can use FFmpeg:

```python
import subprocess
import os

# FFmpeg binary is available in the layer
ffmpeg_path = "/opt/ffmpeg"
ffprobe_path = "/opt/ffprobe"

# Example: Get video duration
def get_video_duration(video_path):
    cmd = [ffprobe_path, "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

# Example: Convert video
def convert_video(input_path, output_path):
    cmd = [
        ffmpeg_path, "-i", input_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "medium",
        output_path
    ]
    subprocess.run(cmd, check=True)
```

## Notes

- FFmpeg binaries are copied to `/opt/` in the Lambda runtime
- The layer includes both ffmpeg and ffprobe binaries
- Python dependencies are installed in the `python/` directory 