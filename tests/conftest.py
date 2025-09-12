"""
Configuration for VM tests.
"""
import os
import pytest
import subprocess
import time
import socket
from pathlib import Path
import json

# Global test configuration
VM_NAME = "test-vm-ssh"
VM_DOMAIN = "test-vm.dockvirt.dev"
VM_IMAGE = "ubuntu-22.04"
VM_PORT = "8080"
SSH_USER = "ubuntu"
SSH_PASSWORD = "ubuntu"
SSH_TIMEOUT = 30

# Use system-wide location for VM files
DOCKVIRT_ROOT = "/var/lib/libvirt/dockvirt"

# Ensure the directory exists with correct permissions
os.makedirs(DOCKVIRT_ROOT, exist_ok=True)
os.makedirs(os.path.join(DOCKVIRT_ROOT, "images"), exist_ok=True)

# Set environment variables
os.environ["DOCKVIRT_ROOT"] = DOCKVIRT_ROOT
os.environ["DOCKVIRT_IMAGES"] = f"{DOCKVIRT_ROOT}/images"

# Ensure qemu user has access
subprocess.run(["sudo", "chown", "-R", "qemu:qemu", DOCKVIRT_ROOT], check=False)
subprocess.run(["sudo", "chmod", "775", DOCKVIRT_ROOT], check=False)
subprocess.run(["sudo", "chmod", "775", os.path.join(DOCKVIRT_ROOT, "images")], check=False)

print(f"Using DOCKVIRT_ROOT: {DOCKVIRT_ROOT}")


def get_vm_ip(vm_name, max_retries=10, wait_seconds=5):
    """Get the IP address of a running VM with retries."""
    for attempt in range(max_retries):
        try:
            # Try to get IP using domifaddr
            result = subprocess.run(
                ["virsh", "domifaddr", vm_name, "--source", "lease"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                print(f"VM Network Info (attempt {attempt + 1}):\n{result.stdout}")
                for line in result.stdout.splitlines():
                    if 'ipv4' in line:
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            return parts[3].split('/')[0]
            
            # Alternative method: Check DHCP leases directly
            try:
                with open('/var/lib/libvirt/dnsmasq/virbr0.status', 'r') as f:
                    leases = json.load(f)
                    for lease in leases:
                        if lease.get('hostname') == f"{vm_name}.{VM_DOMAIN}" or lease.get('client-hostname') == vm_name:
                            return lease.get('ip-address')
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Could not read DHCP leases: {e}")
            
            # If we're here, no IP found yet
            if attempt < max_retries - 1:
                print(f"Waiting for VM to get an IP (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_seconds)
                
        except subprocess.CalledProcessError as e:
            print(f"Error getting VM IP: {e}")
            if attempt < max_retries - 1:
                time.sleep(wait_seconds)
    
    # If we get here, all retries failed
    print("Failed to get VM IP address. Debug info:")
    print("\nVM status:")
    subprocess.run(["virsh", "dominfo", vm_name])
    print("\nNetwork interfaces:")
    subprocess.run(["virsh", "domiflist", vm_name])
    print("\nNetwork status:")
    subprocess.run(["ip", "addr", "show", "virbr0"])
    print("\nDHCP leases:")
    subprocess.run(["sudo", "cat", "/var/lib/libvirt/dnsmasq/virbr0.status"], check=False)
    
    return None


def ensure_test_vm():
    """Ensure test VM is running and ready for SSH connections."""
    try:
        # Clean up any existing VM first to avoid conflicts
        cleanup_test_vm()
        
        # First ensure the default network is up
        check_default_network()
        
        # Ensure the DOCKVIRT_ROOT directory exists and has correct permissions
        os.makedirs(DOCKVIRT_ROOT, exist_ok=True)
        os.makedirs(os.path.join(DOCKVIRT_ROOT, "images"), exist_ok=True)
        
        # Check if VM is already running
        result = subprocess.run(
            ["virsh", "list", "--name"],
            capture_output=True,
            text=True
        )
        print(f"Current running VMs: {result.stdout}")
        
        vm_running = VM_NAME in result.stdout.splitlines()
        
        if not vm_running:
            print(f"Starting VM {VM_NAME}...")
            # Start test VM
            ssh_key = str(Path.home() / ".ssh" / "id_rsa.pub")
            if not os.path.exists(ssh_key):
                raise FileNotFoundError(f"SSH public key not found at {ssh_key}")
    
            # Read the SSH key contents
            try:
                with open(ssh_key, 'r') as f:
                    ssh_key_content = f.read().strip()
                print(f"Using SSH key from: {ssh_key}")
            except Exception as e:
                raise RuntimeError(f"Failed to read SSH key: {str(e)}")
    
            # Build the command with SSH key as a separate argument
            cmd = [
                "python3", "-m", "dockvirt.cli", "up",
                "--name", VM_NAME,
                "--domain", VM_DOMAIN,
                "--image", VM_IMAGE,
                "--port", VM_PORT,
                "--ssh-keys", ssh_key_content,
                "--mem", "1024",
                "--cpus", "1",
                "--debug"  # Enable debug output
            ]
    
            print(f"Starting VM with command: {' '.join(cmd[:5])} [SSH-KEY] {' '.join(cmd[6:])}")
            print(f"Using DOCKVIRT_ROOT: {DOCKVIRT_ROOT}")
    
            # Run the command with Popen to capture output in real-time
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            env["DOCKVIRT_DEBUG"] = "1"
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )
            
            # Stream output in real-time
            full_output = []
            for line in iter(process.stdout.readline, ''):
                print(line, end='')
                full_output.append(line)
                if process.poll() is not None:
                    break
            
            # Get any remaining output
            remaining_output = process.communicate()[0]
            if remaining_output:
                print(remaining_output, end='')
                full_output.append(remaining_output)
            
            # Check for errors
            if process.returncode != 0:
                error_msg = f"Failed to start test VM. Exit code: {process.returncode}\n"
                error_msg += "Last 20 lines of output:\n" + "".join(full_output[-20:])
                
                # Check VM status and logs
                check_vm_status(VM_NAME)
                
                # Check directory permissions
                print("\nChecking directory permissions:")
                subprocess.run(["ls", "-la", DOCKVIRT_ROOT])
                subprocess.run(["ls", "-la", os.path.join(DOCKVIRT_ROOT, "images")])
                
                raise RuntimeError(error_msg)
                
            # Give the VM some time to boot
            print("Waiting for VM to boot...")
            time.sleep(10)  # Initial wait for VM to start
        else:
            print(f"VM {VM_NAME} is already running")
        
        # Get VM IP address with retries
        vm_ip = get_vm_ip(VM_NAME)
        if vm_ip:
            print(f"VM IP address: {vm_ip}")
            return vm_ip
            
        raise RuntimeError("Could not determine VM IP address after multiple attempts")
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed with error: {e}"
        if hasattr(e, 'output') and e.output:
            error_msg += f"\nCommand output: {e.output}"
        if hasattr(e, 'stderr') and e.stderr:
            error_msg += f"\nError details: {e.stderr}"
        print(error_msg)
        raise RuntimeError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        raise RuntimeError(error_msg) from e


def check_default_network():
    """Ensure the default libvirt network is active."""
    try:
        # Check if the default network exists
        result = subprocess.run(
            ["virsh", "net-list", "--all"],
            capture_output=True,
            text=True
        )
        
        if "default" not in result.stdout:
            print("Default network not found, creating it...")
            # Define the default network
            network_xml = """
            <network>
              <name>default</name>
              <forward mode='nat'/>
              <bridge name='virbr0' stp='on' delay='0'/>
              <ip address='192.168.122.1' netmask='255.255.255.0'>
                <dhcp>
                  <range start='192.168.122.2' end='192.168.122.254'/>
                </dhcp>
              </ip>
            </network>
            """
            
            # Create a temporary file with the network definition
            with open("/tmp/default-network.xml", "w") as f:
                f.write(network_xml)
                
            # Define the network
            subprocess.run(
                ["sudo", "virsh", "net-define", "/tmp/default-network.xml"],
                check=True
            )
            os.remove("/tmp/default-network.xml")
        
        # Check if the network is active
        result = subprocess.run(
            ["virsh", "net-info", "default"],
            capture_output=True,
            text=True
        )
        
        if "Active:     no" in result.stdout:
            print("Starting default network...")
            subprocess.run(
                ["sudo", "virsh", "net-start", "default"],
                check=True
            )
            
            # Set autostart
            subprocess.run(
                ["sudo", "virsh", "net-autostart", "default"],
                check=True
            )
            
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to configure default network: {e}"
        if e.stderr:
            error_msg += f"\nError details: {e.stderr}"
        print(error_msg)
        raise RuntimeError("Could not set up default network. Make sure libvirt is properly installed and your user has the necessary permissions.")
    except Exception as e:
        print(f"Unexpected error configuring network: {e}")
        raise


def check_vm_status(name):
    """Check VM status and logs for debugging."""
    print("\n=== VM Status Check ===")
    
    # Check VM state
    try:
        result = subprocess.run(
            ["virsh", "domstate", name],
            capture_output=True,
            text=True
        )
        print(f"VM State: {result.stdout.strip()}")
        
        # Get VM info
        result = subprocess.run(
            ["virsh", "dominfo", name],
            capture_output=True,
            text=True
        )
        print(f"\nVM Info:\n{result.stdout}")
        
        # Get console logs if available
        try:
            result = subprocess.run(
                ["virsh", "console", name, "--force"],
                capture_output=True,
                text=True,
                timeout=5
            )
            print(f"\nConsole output (last 20 lines):\n{result.stdout.strip().splitlines()[-20:]}")
        except subprocess.TimeoutExpired:
            print("\nCould not get console output (timeout)")
        except Exception as e:
            print(f"\nError getting console: {str(e)}")
            
    except subprocess.CalledProcessError as e:
        print(f"Error checking VM status: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
    except Exception as e:
        print(f"Unexpected error checking VM status: {str(e)}")
    
    print("====================\n")


def cleanup_test_vm():
    """Clean up test VM."""
    subprocess.run(["dockvirt", "down", "--name", VM_NAME],
                  stderr=subprocess.DEVNULL,
                  stdout=subprocess.DEVNULL)


@pytest.fixture(scope="session")
def vm_ip():
    """Fixture to get VM IP address."""
    check_default_network()
    vm_ip = ensure_test_vm()
    
    yield vm_ip
    
    # Cleanup after all tests are done
    cleanup_test_vm()
