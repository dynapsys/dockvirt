import os
import subprocess
import sys
import pytest

VM_NAME = "test-dockvirt-vm"
DOMAIN = "test.dockvirt.local"


@pytest.fixture(scope="module")
def check_dependencies():
    """Skip tests if libvirt or environment variables are not available."""
    try:
        subprocess.run(["virsh", "--connect", "qemu:///system", "-v"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("libvirt/virsh is not installed or not available in PATH")

    # Use defaults if not provided by environment/Makefile
    os.environ.setdefault("DOCKVIRT_TEST_IMAGE", "nginx:latest")
    os.environ.setdefault("DOCKVIRT_TEST_OS_VARIANT", "ubuntu22.04")
    os.environ.setdefault("LIBVIRT_DEFAULT_URI", "qemu:///system")


def run_command(command):
    """Helper to run a shell command and return its output."""
    # Ensure we run against system libvirt
    env = os.environ.copy()
    env.setdefault("LIBVIRT_DEFAULT_URI", "qemu:///system")
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, check=False, env=env
    )
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
    result.raise_for_status()
    return result.stdout.strip()


def test_vm_lifecycle(check_dependencies):
    """Tests the full lifecycle of a VM: create, check, and destroy."""
    image = os.environ.get("DOCKVIRT_TEST_IMAGE", "nginx:latest")
    os_variant = os.environ.get("DOCKVIRT_TEST_OS_VARIANT", "ubuntu22.04")

    try:
        # Step 1: Create the VM
        print(f"\n🚀 Creating VM '{VM_NAME}'...")
        run_command(
            f"{sys.executable} -m dockvirt.cli up --name {VM_NAME} --domain {DOMAIN} "
            f"--image {image} --port 80 --os {os_variant}"
        )

        # Step 2: Verify the VM is running
        print(f"🔍 Verifying VM '{VM_NAME}' status...")
        output = run_command("virsh --connect qemu:///system list --all --name")
        assert VM_NAME in output

    finally:
        # Step 3: Destroy the VM
        print(f"\n🗑️ Destroying VM '{VM_NAME}'...")
        run_command(f"{sys.executable} -m dockvirt.cli down --name {VM_NAME}")

        # Step 4: Verify the VM is destroyed
        print(f"🔍 Verifying VM '{VM_NAME}' is destroyed...")
        output = run_command("virsh --connect qemu:///system list --all --name")
        assert VM_NAME not in output
