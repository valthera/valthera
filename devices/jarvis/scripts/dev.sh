#!/bin/bash

# Development script for Jarvis Smart CV Pipeline
# Starts both API and web services for local development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_PORT=8001
WEB_PORT=3000
API_CONTAINER_NAME="jarvis-api-dev"
WEB_CONTAINER_NAME="jarvis-web-dev"

echo -e "${BLUE}🚀 Starting Jarvis Development Environment${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping development services...${NC}"
    
    # Stop containers
    docker stop $API_CONTAINER_NAME 2>/dev/null || true
    docker stop $WEB_CONTAINER_NAME 2>/dev/null || true
    
    # Remove containers
    docker rm $API_CONTAINER_NAME 2>/dev/null || true
    docker rm $WEB_CONTAINER_NAME 2>/dev/null || true
    
    echo -e "${GREEN}✅ Development services stopped${NC}"
    exit 0
}

# Set up cleanup trap
trap cleanup SIGINT SIGTERM

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Build API service
echo -e "${BLUE}🔨 Building API service...${NC}"
docker build -t jarvis-api:dev .

# Start API service
echo -e "${BLUE}🚀 Starting API service on port $API_PORT...${NC}"
docker run -d \
    --name $API_CONTAINER_NAME \
    --device /dev/video0:/dev/video0 \
    -p $API_PORT:$API_PORT \
    -e JARVIS_HTTP_PORT=$API_PORT \
    jarvis-api:dev

# Wait for API service to be ready
echo -e "${YELLOW}⏳ Waiting for API service to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:$API_PORT/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ API service is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ API service failed to start${NC}"
        cleanup
        exit 1
    fi
    sleep 1
done

# Check if web directory exists and has package.json
if [ ! -f "web/package.json" ]; then
    echo -e "${RED}❌ Web directory not found or package.json missing${NC}"
    echo "Please ensure the web directory exists with a valid React app"
    cleanup
    exit 1
fi

# Check if Node.js is available
if ! command -v node >/dev/null 2>&1; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    echo "Please install Node.js to run the web development server"
    cleanup
    exit 1
fi

# Install web dependencies if needed
if [ ! -d "web/node_modules" ]; then
    echo -e "${BLUE}📦 Installing web dependencies...${NC}"
    cd web
    npm install
    cd ..
fi

# Start web development server
echo -e "${BLUE}🌐 Starting web development server on port $WEB_PORT...${NC}"
cd web
npm run dev &
WEB_PID=$!
cd ..

# Wait for web server to be ready
echo -e "${YELLOW}⏳ Waiting for web server to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:$WEB_PORT >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Web server is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Web server failed to start${NC}"
        cleanup
        exit 1
    fi
    sleep 1
done

echo ""
echo -e "${GREEN}🎉 Development environment is ready!${NC}"
echo ""
echo -e "${BLUE}📱 Web Interface:${NC} http://localhost:$WEB_PORT"
echo -e "${BLUE}🔌 API Endpoint:${NC} http://localhost:$API_PORT"
echo -e "${BLUE}📊 API Health:${NC} http://localhost:$API_PORT/health"
echo -e "${BLUE}📚 API Docs:${NC} http://localhost:$API_PORT/docs"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "  - The web interface will auto-reload on changes"
echo "  - API service runs in Docker with hot reload"
echo "  - Check logs with: docker logs $API_CONTAINER_NAME"
echo "  - Press Ctrl+C to stop all services"
echo ""

# Monitor services
echo -e "${BLUE}👀 Monitoring services...${NC}"
while true; do
    # Check API service
    if ! docker ps | grep -q $API_CONTAINER_NAME; then
        echo -e "${RED}❌ API service stopped unexpectedly${NC}"
        cleanup
        exit 1
    fi
    
    # Check web service
    if ! kill -0 $WEB_PID 2>/dev/null; then
        echo -e "${RED}❌ Web service stopped unexpectedly${NC}"
        cleanup
        exit 1
    fi
    
    sleep 5
done
