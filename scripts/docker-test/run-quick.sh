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

docker run --rm -it --privileged --network=host \
  -v "${PROJECT_DIR}":/workspace -w /workspace \
  -e SKIP_HOST_BUILD=1 \
  ${DEV_KVM_ARGS} \
  "${IMAGE_NAME}" bash -lc 'su - dev -c "cd /workspace && \
    python3 -m venv --system-site-packages .venv-3.13 && \
    source .venv-3.13/bin/activate && \
    pip install -U pip setuptools wheel && \
    pip install -e .[dev] --no-deps && \
    pip install jinja2 click pyyaml && \
    make doctor && \
    PIP_NO_DEPS=1 make install && \
    PIP_NO_DEPS=1 make test-commands && \
    PIP_NO_DEPS=1 make test-quick && \
    make build"'
