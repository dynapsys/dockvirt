#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${DOCKER_TEST_IMAGE:-dockvirt/test-env:latest}"

echo "🧹 Cleaning docker test artifacts..."
# No local build cache to remove; optionally remove image
if docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  docker rmi "${IMAGE_NAME}" || true
fi

echo "✅ Clean complete"
