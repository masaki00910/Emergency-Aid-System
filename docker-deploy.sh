#!/bin/bash

# Docker Hub経由でのデプロイ用スクリプト

# Docker Hub用のタグ
DOCKER_IMAGE="hirokiemergency/disaster-api:latest"

echo "🏗️  Building Docker image..."
docker build -t $DOCKER_IMAGE .

echo "📤 Pushing to Docker Hub..."
docker push $DOCKER_IMAGE

echo "✅ Docker image pushed to Docker Hub: $DOCKER_IMAGE"
echo "🔗 You can now deploy this image to Cloud Run manually in the console"
echo "   Image URL: $DOCKER_IMAGE"