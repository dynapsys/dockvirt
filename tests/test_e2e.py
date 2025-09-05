import os
import subprocess
import pytest

VM_NAME = "test-dockvirt-vm"
DOMAIN = "test.dockvirt.local"
IMAGE = "hello-world"


@pytest.fixture(scope="module")
def check_dependencies():
    """Skip tests if libvirt or environment variables are not available."""
    try:
        subprocess.run(["virsh", "-v"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("libvirt/virsh is not installed or not available in PATH")

    if "DOCKVIRT_TEST_IMAGE" not in os.environ:
        pytest.skip("DOCKVIRT_TEST_IMAGE environment variable is not set")

    if "DOCKVIRT_TEST_OS_VARIANT" not in os.environ:
        pytest.skip("DOCKVIRT_TEST_OS_VARIANT environment variable is not set")


def run_command(command):
    """Helper to run a shell command and return its output."""
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
    result.raise_for_status()
    return result.stdout.strip()


def test_vm_lifecycle(check_dependencies):
    """Tests the full lifecycle of a VM: create, check, and destroy."""
    base_image = os.environ["DOCKVIRT_TEST_IMAGE"]
    os_variant = os.environ["DOCKVIRT_TEST_OS_VARIANT"]

    try:
        # Step 1: Create the VM
        print(f"\n🚀 Creating VM '{VM_NAME}'...")
        run_command(
            f"dockvirt up --name {VM_NAME} --domain {DOMAIN} "
            f"--image {IMAGE} --port 80 --base-image {base_image} "
            f"--os-variant {os_variant}"
        )

        # Step 2: Verify the VM is running
        print(f"🔍 Verifying VM '{VM_NAME}' status...")
        output = run_command(f"virsh list --all --name")
        assert VM_NAME in output

    finally:
        # Step 3: Destroy the VM
        print(f"\n🗑️ Destroying VM '{VM_NAME}'...")
        run_command(f"dockvirt down --name {VM_NAME}")

        # Step 4: Verify the VM is destroyed
        print(f"🔍 Verifying VM '{VM_NAME}' is destroyed...")
        output = run_command(f"virsh list --all --name")
        assert VM_NAME not in output
