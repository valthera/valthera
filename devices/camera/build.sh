#!/bin/bash

# Build and run script for Camera Docker container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building Camera Docker container...${NC}"

# Build the Docker image
docker build -t camera:latest .

echo -e "${GREEN}Build completed successfully!${NC}"

echo -e "${YELLOW}Running Camera container...${NC}"

# Run the container
docker run --rm camera:latest

echo -e "${GREEN}Container execution completed!${NC}" 