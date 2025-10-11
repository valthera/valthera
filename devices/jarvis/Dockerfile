# Multi-architecture Dockerfile for Jarvis multi-modal agent
# Supports both x86_64 (Mac development) and ARM64 (Jetson Nano)

# Use Ubuntu 22.04 as base for better compatibility
FROM ubuntu:22.04

# Set working directory
WORKDIR /app

# Set timezone to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg2 \
    lsb-release \
    software-properties-common \
    build-essential \
    cmake \
    git \
    libssl-dev \
    libusb-1.0-0-dev \
    pkg-config \
    portaudio19-dev \
    libasound2-dev \
    alsa-utils \
    libopencv-dev \
    python3 \
    python3-pip \
    python3-dev \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Add Intel RealSense repository and install RealSense SDK
RUN curl -sSL https://librealsense.intel.com/Debian/apt-repo/conf/librealsense.pgp | apt-key add - && \
    echo 'deb https://librealsense.intel.com/Debian/apt-repo focal main' | tee /etc/apt/sources.list.d/librealsense.list && \
    apt-get update && apt-get install -y \
    librealsense2-dev \
    librealsense2-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Install poetry
RUN pip3 install poetry

# Configure poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies (skip installing the current project)
RUN poetry install --only main --no-interaction --no-ansi --no-root

# Install system dependencies for OpenCV and audio
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Download Vosk model (small model for Jetson compatibility)
RUN mkdir -p /app/jarvis/models/vosk-model-small && \
    cd /app/jarvis/models/vosk-model-small && \
    wget -q https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip && \
    unzip -q vosk-model-small-en-us-0.15.zip && \
    rm vosk-model-small-en-us-0.15.zip

# Download OpenWakeWord models
RUN python3 -c "from openwakeword.model import Model; Model()" || true

# Copy the jarvis module
COPY jarvis/ ./jarvis/

# Create a script to start Jarvis
RUN echo '#!/bin/bash\n\
set -e\n\
PORT="${JARVIS_HTTP_PORT:-8001}"\n\
echo "Starting Jarvis multi-modal agent on port $PORT..."\n\
echo "Audio: Wake word detection + speech-to-text"\n\
echo "Video: YOLOv8 person detection"\n\
exec uvicorn jarvis.server:app --host 0.0.0.0 --port "$PORT"' > /app/start.sh && \
    chmod +x /app/start.sh

# Expose HTTP port
EXPOSE 8001

# Set the default command to run the start script
CMD ["/app/start.sh"]
