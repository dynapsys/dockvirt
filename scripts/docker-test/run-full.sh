#!/usr/bin/env bash
set -euo pipefail

# Run the full test suite (including e2e and examples) in a clean Docker environment.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
IMAGE_NAME="${DOCKER_TEST_IMAGE:-dockvirt/test-env:latest}"

# 1. Build the test environment image
"${SCRIPT_DIR}/build.sh"

# 2. Determine if KVM is available and set docker args
DEV_KVM_ARGS=""
if [ -e /dev/kvm ]; then
  DEV_KVM_ARGS="--device=/dev/kvm"
fi

# 3. Run the full test suite inside the container
# The entrypoint script will handle starting libvirtd.
# We run as the 'dev' user created in the Dockerfile.
docker run --rm -it --privileged --network=host \
  -v "${PROJECT_DIR}":/workspace -w /workspace \
  -e SKIP_HOST_BUILD=1 \
  -e DOCKVIRT_TEST_OS_VARIANT=ubuntu22.04 \
  ${DEV_KVM_ARGS} \
  "${IMAGE_NAME}" bash -lc 'su - dev -c "cd /workspace && \\
    echo \"\⚙️ Setting up Python venv...\" && \\
    python3 -m venv --system-site-packages .venv-3.13 && \\
    source .venv-3.13/bin/activate && \\
    pip install -U pip setuptools wheel && \\
    pip install -e .[dev] && \\
    echo \"\🚀 Running Full SDLC...\" && \\
    python scripts/sdlc.py full --fix --skip-host-build"'

echo "✅ Full test run complete."
