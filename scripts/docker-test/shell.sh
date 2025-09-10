#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
IMAGE_NAME="${DOCKER_TEST_IMAGE:-dockvirt/test-env:latest}"

"${SCRIPT_DIR}/build.sh"

DEV_KVM_ARGS=""
if [ -e /dev/kvm ]; then
  DEV_KVM_ARGS="--device=/dev/kvm"
fi

echo "🐚 Opening shell in ${IMAGE_NAME}..."

docker run --rm -it --privileged --network=host \
  -v "${PROJECT_DIR}":/workspace -w /workspace \
  ${DEV_KVM_ARGS} \
  "${IMAGE_NAME}" bash
