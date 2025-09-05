#!/usr/bin/env python3
"""
System dependency checker and auto-installer for dockvirt.
Detects missing dependencies and provides installation instructions.
"""

import subprocess
import sys
import platform
from pathlib import Path


def run_command(cmd, capture_output=True):
    """Run shell command and return result."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=capture_output, text=True
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def is_wsl():
    """Check if running under WSL."""
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower()
    except FileNotFoundError:
        return False


def is_docker_installed():
    """Check if Docker is installed and accessible."""
    success, _, _ = run_command("docker --version")
    if not success:
        return False
    
    # Check if docker daemon is accessible
    success, _, _ = run_command("docker ps")
    return success


def is_libvirt_installed():
    """Check if libvirt tools are installed."""
    commands = ["virsh", "virt-install", "qemu-img"]
    for cmd in commands:
        success, _, _ = run_command(f"which {cmd}")
        if not success:
            return False
    return True


def is_cloud_utils_installed():
    """Checks if the cloud-localds tool is available."""
    success, _, _ = run_command("which cloud-localds")
    return success


def check_kvm_support():
    """Check if KVM virtualization is available."""
    if is_wsl():
        return False, "KVM is not available in WSL (uses Hyper-V)"
    
    # Check if /dev/kvm exists
    if not Path("/dev/kvm").exists():
        return False, "/dev/kvm not found - check if virtualization is enabled in BIOS"
    
    # Check if user is in kvm group
    success, groups, _ = run_command("groups")
    if "kvm" not in groups:
        return False, "User is not in the 'kvm' group"
    
    return True, "KVM is available"


def get_os_info():
    """Get operating system information."""
    try:
        with open('/etc/os-release', 'r') as f:
            os_release = {}
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os_release[key] = value.strip('"')
        return os_release.get('ID', 'unknown'), os_release.get('VERSION_ID', 'unknown')
    except FileNotFoundError:
        return platform.system().lower(), platform.release()


def generate_install_commands(os_id, missing_deps):
    """Generate installation commands based on OS and missing dependencies."""
    commands = []
    
    if os_id in ['ubuntu', 'debian']:
        if 'docker' in missing_deps:
            commands.extend([
                "# Install Docker",
                "curl -fsSL https://get.docker.com -o get-docker.sh",
                "sudo sh get-docker.sh",
                "sudo usermod -aG docker $USER",
            ])
        
        if 'libvirt' in missing_deps:
            commands.extend([
                "# Install libvirt and KVM",
                "sudo apt update",
                "sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils",
                "sudo usermod -aG libvirt $USER",
                "sudo usermod -aG kvm $USER",
            ])
        
        if 'cloud-utils' in missing_deps:
            commands.extend([
                "# Install cloud-image-utils",
                "sudo apt install -y cloud-image-utils",
            ])
    
    elif os_id in ['fedora', 'centos', 'rhel']:
        if 'docker' in missing_deps:
            commands.extend([
                "# Install Docker",
                "curl -fsSL https://get.docker.com -o get-docker.sh",
                "sudo sh get-docker.sh",
                "sudo usermod -aG docker $USER",
            ])
        
        if 'libvirt' in missing_deps:
            commands.extend([
                "# Install libvirt and KVM",
                "sudo dnf install -y qemu-kvm libvirt virt-install bridge-utils",
                "sudo usermod -aG libvirt $USER",
                "sudo usermod -aG kvm $USER",
            ])
        
        if 'cloud-utils' in missing_deps:
            commands.extend([
                "# Install cloud-utils",
                "sudo dnf install -y cloud-utils-growpart",
            ])
    
    elif os_id == 'arch':
        if 'docker' in missing_deps:
            commands.extend([
                "# Install Docker",
                "sudo pacman -S docker",
                "sudo usermod -aG docker $USER",
            ])
        
        if 'libvirt' in missing_deps:
            commands.extend([
                "# Install libvirt and KVM", 
                "sudo pacman -S qemu-full libvirt virt-install bridge-utils",
                "sudo usermod -aG libvirt $USER",
                "sudo usermod -aG kvm $USER",
            ])
        
        if 'cloud-utils' in missing_deps:
            commands.extend([
                "# Install cloud-image-utils",
                "sudo pacman -S cloud-image-utils",
            ])
    
    if commands:
        commands.extend([
            "",
            "# After installation, log out and log back in for group changes to take effect",
            "# or run: newgrp docker && newgrp libvirt && newgrp kvm",
        ])
    
    return commands


def check_system_dependencies():
    """Comprehensive system dependency check."""
    print("🔍 Checking system dependencies for dockvirt...")
    print("=" * 50)
    
    # Basic system info
    os_id, os_version = get_os_info()
    wsl = is_wsl()
    
    print(f"💻 System: {os_id} {os_version}")
    if wsl:
        print("🪟 WSL (Windows Subsystem for Linux) detected")
    print()
    
    # Check dependencies
    missing_deps = []
    issues = []
    
    # Docker check
    if is_docker_installed():
        print("✅ Docker: Installed and available")
    else:
        print("❌ Docker: Not found or inaccessible")
        missing_deps.append('docker')
    
    # Libvirt check  
    if is_libvirt_installed():
        print("✅ Libvirt: Installed")
    else:
        print("❌ Libvirt: Tools not found (virsh, virt-install, qemu-img)")
        missing_deps.append('libvirt')
    
    # Cloud utils check
    if is_cloud_utils_installed():
        print("✅ Cloud-utils: Installed")
    else:
        print("❌ Cloud-utils: cloud-localds not found")
        missing_deps.append('cloud-utils')
    
    # KVM check
    kvm_ok, kvm_msg = check_kvm_support()
    if kvm_ok:
        print(f"✅ KVM: {kvm_msg}")
    else:
        print(f"⚠️  KVM: {kvm_msg}")
        issues.append(kvm_msg)
    
    print()
    
    # WSL specific instructions
    if wsl:
        print("🪟 **INSTRUCTIONS FOR WSL/Windows:**")
        print("1. Make sure Hyper-V is enabled in Windows Features")
        print("2. Run PowerShell as Administrator and execute:")
        print("   Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform")
        print("3. Dockvirt will use Hyper-V instead of KVM")
        print("4. For best performance, consider using Docker Desktop")
        print()
    
    # Installation commands
    if missing_deps:
        print("🔧 **INSTALLATION COMMANDS:**")
        install_commands = generate_install_commands(os_id, missing_deps)
        for cmd in install_commands:
            print(cmd)
        print()
    
    # Summary
    if not missing_deps and not issues:
        print("🎉 All dependencies are met!")
        return True
    elif missing_deps:
        print(f"⚠️  Missing dependencies: {', '.join(missing_deps)}")
        return False
    else:
        print("⚠️  System ready with minor issues")
        return True


def auto_install_dependencies():
    """Interactive auto-installation of dependencies."""
    print("🚀 Starting automatic dependency installation...")
    
    os_id, _ = get_os_info()
    missing_deps = []
    
    if not is_docker_installed():
        missing_deps.append('docker')
    if not is_libvirt_installed():
        missing_deps.append('libvirt')
    if not is_cloud_utils_installed():
        missing_deps.append('cloud-utils')
    
    if not missing_deps:
        print("✅ All dependencies are already installed!")
        return True
    
    print(f"📦 Missing dependencies: {', '.join(missing_deps)}")
    response = input("Do you want to install them automatically? (y/N): ")
    
    if response.lower() not in ['y', 'yes']:
        print("Auto-installation cancelled")
        return False
    
    install_commands = generate_install_commands(os_id, missing_deps)
    
    for cmd in install_commands:
        if cmd.startswith('#') or not cmd.strip():
            print(cmd)
            continue
        
        print(f"Executing: {cmd}")
        success, stdout, stderr = run_command(cmd, capture_output=False)
        
        if not success:
            print(f"❌ Error executing: {cmd}")
            print(f"Stderr: {stderr}")
            return False
    
    print("✅ Auto-installation finished!")
    print("🔄 Please log out and log back in for group changes to take effect")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        auto_install_dependencies()
    else:
        check_system_dependencies()
