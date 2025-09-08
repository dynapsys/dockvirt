#!/usr/bin/env bash
set -euo pipefail

# Build the Docker test image for dockvirt
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
IMAGE_NAME="${DOCKER_TEST_IMAGE:-dockvirt/test-env:latest}"

echo "🐳 Building Docker test image: ${IMAGE_NAME}"

docker build -t "${IMAGE_NAME}" "${SCRIPT_DIR}" 

echo "✅ Built ${IMAGE_NAME}"
