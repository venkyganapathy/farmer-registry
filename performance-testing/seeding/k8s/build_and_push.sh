#!/bin/bash
# Build and push the seeding Docker image

set -e

# Configuration
IMAGE_NAME="${IMAGE_NAME:-vin0dkhichar/farmer-registry-seeding}"
IMAGE_TAG="${IMAGE_TAG:-v3}"
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEEDING_DIR="$(dirname "$SCRIPT_DIR")"

echo "Building Docker image: ${FULL_IMAGE}"
echo "Seeding directory: ${SEEDING_DIR}"

# Build the image
docker build -t "${FULL_IMAGE}" -f "${SCRIPT_DIR}/Dockerfile" "${SEEDING_DIR}"

echo "Pushing Docker image: ${FULL_IMAGE}"
docker push "${FULL_IMAGE}"

echo "Image built and pushed successfully: ${FULL_IMAGE}"