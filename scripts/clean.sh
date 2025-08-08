#!/bin/bash

set -e

echo "🧹 Cleaning build artifacts..."

# Remove SAM build artifacts
rm -rf .aws-sam/

# Remove old build directory
rm -rf lambdas-built/

# Clean Lambda layers build artifacts
echo "Cleaning Lambda layers..."
# Preserve valthera-core layer source
mv lambdas/shared/valthera-core-layer/python/valthera_core /tmp/valthera_core_backup 2>/dev/null || true
find lambdas/shared -name "python" -type d -exec rm -rf {} + 2>/dev/null || true
find lambdas/shared -name "requirements.txt" -type f -delete 2>/dev/null || true
find lambdas/shared -name "*.zip" -type f -delete 2>/dev/null || true
# Restore valthera-core layer source
mkdir -p lambdas/shared/valthera-core-layer/python
mv /tmp/valthera_core_backup lambdas/shared/valthera-core-layer/python/valthera_core 2>/dev/null || true

# Clean Poetry cache for layers
echo "Cleaning layer Poetry cache..."
cd lambdas/shared/valthera-core-layer
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