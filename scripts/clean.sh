#!/bin/bash

set -e

echo "🧹 Cleaning build artifacts..."

# Remove SAM build artifacts
rm -rf .aws-sam/

# Remove old build directory
rm -rf lambdas-built/

# Clean Lambda layers build artifacts
echo "Cleaning Lambda layers..."
find lambdas/layers -name "python" -type d -exec rm -rf {} + 2>/dev/null || true
find lambdas/layers -name "requirements.txt" -type f -delete 2>/dev/null || true
find lambdas/layers -name "*.zip" -type f -delete 2>/dev/null || true

# Clean Poetry cache for shared packages
echo "Cleaning Poetry cache..."
cd packages/valthera-core
poetry cache clear . --all
cd ../..

# Clean Poetry cache for layers
echo "Cleaning layer Poetry cache..."
cd lambdas/layers/valthera-core
poetry cache clear . --all
cd ../../..

cd lambdas/layers/ffmpeg
poetry cache clear . --all
cd ../../..

# Remove any temporary files
rm -f .sam-api.pid

# Docker cleanup
echo "🐳 Cleaning Docker resources..."

# Stop and remove containers related to this project
echo "Stopping and removing containers..."
docker-compose down --volumes --remove-orphans 2>/dev/null || true

# Remove specific containers that might be running
docker rm -f valthera-dynamodb-local 2>/dev/null || true
docker rm -f valthera-localstack 2>/dev/null || true
docker rm -f valthera-cognito-local 2>/dev/null || true

# Remove Docker images related to this project
echo "Removing Docker images..."
docker rmi camera:latest 2>/dev/null || true
docker rmi camera:v1.0 2>/dev/null || true
docker rmi video-processor:latest 2>/dev/null || true
docker rmi video-processor:dev 2>/dev/null || true

# Remove any dangling images (unused images)
echo "Removing dangling images..."
docker image prune -f 2>/dev/null || true

# Remove unused volumes
echo "Removing unused volumes..."
docker volume prune -f 2>/dev/null || true

# Remove unused networks
echo "Removing unused networks..."
docker network prune -f 2>/dev/null || true

# Clean Docker build cache
echo "Cleaning Docker build cache..."
docker builder prune -f 2>/dev/null || true

# Remove any project-specific volumes
echo "Removing project-specific volumes..."
docker volume rm valthera-infra_dynamodb_data 2>/dev/null || true
docker volume rm valthera-infra_localstack_data 2>/dev/null || true

# Remove any .cognito-data directory created by cognito-local
rm -rf .cognito-data 2>/dev/null || true

echo "✅ Clean complete!" 