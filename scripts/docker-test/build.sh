#!/usr/bin/env bash
set -euo pipefail

# Build the Docker test image for dockvirt
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
IMAGE_NAME="${DOCKER_TEST_IMAGE:-dockvirt/test-env:latest}"

# Collect proxy args if present
BUILD_ARGS=()
for v in HTTP_PROXY HTTPS_PROXY NO_PROXY http_proxy https_proxy no_proxy; do
  if [ -n "${!v:-}" ]; then
    BUILD_ARGS+=(--build-arg "$v=${!v}")
  fi
done

echo "🐳 Building Docker test image: ${IMAGE_NAME}"

docker build "${BUILD_ARGS[@]}" -t "${IMAGE_NAME}" "${SCRIPT_DIR}" 

echo "✅ Built ${IMAGE_NAME}"
