#!/bin/bash

set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
REGION=${GOOGLE_CLOUD_REGION:-asia-northeast1}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: GOOGLE_CLOUD_PROJECT environment variable is not set"
    exit 1
fi

echo "Deploying Disaster Response System to project: $PROJECT_ID"

cd "$(dirname "$0")/.."

echo "Building and pushing container images..."

AGENTS=("detection" "orchestrator" "info_collector" "analyzer" "pr")

for agent in "${AGENTS[@]}"; do
    echo "Building $agent agent..."
    
    docker build -t "gcr.io/$PROJECT_ID/$agent-agent:latest" \
        --build-arg PROJECT_ID="$PROJECT_ID" \
        --build-arg REGION="$REGION" \
        "agents/$agent/"
    
    echo "Pushing $agent agent..."
    docker push "gcr.io/$PROJECT_ID/$agent-agent:latest"
done

echo "Deploying infrastructure with Terraform..."
cd infrastructure/environments/dev

terraform init
terraform plan -var="project_id=$PROJECT_ID" -var="region=$REGION"
terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION" -auto-approve

echo "Deployment completed successfully!"
echo "Service URLs:"
terraform output service_urls