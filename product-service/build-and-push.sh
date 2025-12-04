#!/bin/bash
# Script to build and push Product Service Docker image to Docker Hub

set -e

# Docker Hub credentials
DOCKER_USERNAME="afsari911"
IMAGE_NAME="product-service"
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}"

echo "🔨 Building Docker image..."
cd "$(dirname "$0")"

# Build the image
docker build -t ${FULL_IMAGE_NAME}:latest .

echo "✅ Image built successfully!"
echo "📤 Pushing to Docker Hub..."

# Login to Docker Hub
echo "Please enter your Docker Hub password:"
docker login -u ${DOCKER_USERNAME}

# Push the image
docker push ${FULL_IMAGE_NAME}:latest

echo "✅ Image pushed successfully!"
echo "📍 Image location: ${FULL_IMAGE_NAME}:latest"
echo ""
echo "Next steps:"
echo "1. Update k8s/product-service/deployment.yaml to use: ${FULL_IMAGE_NAME}:latest"
echo "2. Apply the updated deployment: kubectl apply -f k8s/product-service/deployment.yaml"
