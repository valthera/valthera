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
    libopencv-dev \
    python3 \
    python3-pip \
    python3-dev \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Note: RealSense SDK will be installed on the host system
# For now, we'll skip RealSense installation in Docker
# and rely on the host system's installation

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

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy the jarvis module
COPY jarvis/ ./jarvis/

# Create a script to start Jarvis
RUN echo '#!/bin/bash\n\
set -e\n\
PORT="${JARVIS_HTTP_PORT:-8001}"\n\
echo "Starting Jarvis camera agent on port $PORT..."\n\
echo "Video: YOLOv8 person detection"\n\
echo "Depth: Center depth streaming"\n\
exec uvicorn jarvis.server:app --host 0.0.0.0 --port "$PORT"' > /app/start.sh && \
    chmod +x /app/start.sh

# Expose HTTP port
EXPOSE 8001

# Set the default command to run the start script
CMD ["/app/start.sh"]
