# Multi-architecture Dockerfile for RealSense camera support
# Supports both x86_64 (Mac development) and ARM64 (Jetson Nano)

# Use Ubuntu 22.04 as base for better compatibility
FROM ubuntu:22.04

# Set working directory
WORKDIR /app

# Install system dependencies and RealSense
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg2 \
    lsb-release \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install RealSense SDK (conditional based on architecture)
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    cmake \
    git \
    libssl-dev \
    libusb-1.0-0-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Try to install RealSense from package, fall back to source if needed
RUN apt-get update && \
    (apt-get install -y librealsense2-utils librealsense2-dev || \
     echo "RealSense packages not available for this architecture - will install from source") && \
    rm -rf /var/lib/apt/lists/*

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

# Install pyrealsense2 for Python RealSense support
RUN pip3 install pyrealsense2

# Copy the camera module
COPY camera/ ./camera/

# Create a script to check RealSense devices and start HTTP server
RUN echo '#!/bin/bash\n\
echo "Checking RealSense devices..."\n\
if command -v rs-enumerate-devices >/dev/null 2>&1; then\n\
    rs-enumerate-devices\n\
else\n\
    echo "Warning: rs-enumerate-devices not found (librealsense2-utils not installed or not available for this architecture)"\n\
fi\n\
echo "Starting camera HTTP service on :8000..."\n\
exec python3 camera/http_server.py' > /app/start.sh && \
    chmod +x /app/start.sh

# Expose HTTP port for health/feed
EXPOSE 8000

# Set the default command to run the start script
CMD ["/app/start.sh"]