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
    """Check if cloud-localds is available."""
    success, _, _ = run_command("which cloud-localds")
    return success


def check_kvm_support():
    """Check if KVM virtualization is available."""
    if is_wsl():
        return False, "KVM nie jest dostępne w WSL (używa Hyper-V)"
    
    # Check if /dev/kvm exists
    if not Path("/dev/kvm").exists():
        return False, "Brak /dev/kvm - sprawdź czy virtualizacja jest włączona w BIOS"
    
    # Check if user is in kvm group
    success, groups, _ = run_command("groups")
    if "kvm" not in groups:
        return False, "Użytkownik nie jest w grupie 'kvm'"
    
    return True, "KVM jest dostępne"


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
                "sudo dnf install -y cloud-utils",
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
            "# Po instalacji wyloguj się i zaloguj ponownie aby grupy zaczęły działać",
            "# lub uruchom: newgrp docker && newgrp libvirt && newgrp kvm",
        ])
    
    return commands


def check_system_dependencies():
    """Comprehensive system dependency check."""
    print("🔍 Sprawdzanie zależności systemu dla dockvirt...")
    print("=" * 50)
    
    # Basic system info
    os_id, os_version = get_os_info()
    wsl = is_wsl()
    
    print(f"💻 System: {os_id} {os_version}")
    if wsl:
        print("🪟 Wykryto WSL (Windows Subsystem for Linux)")
    print()
    
    # Check dependencies
    missing_deps = []
    issues = []
    
    # Docker check
    if is_docker_installed():
        print("✅ Docker: Zainstalowany i dostępny")
    else:
        print("❌ Docker: Brak lub niedostępny")
        missing_deps.append('docker')
    
    # Libvirt check  
    if is_libvirt_installed():
        print("✅ Libvirt: Zainstalowane")
    else:
        print("❌ Libvirt: Brak narzędzi (virsh, virt-install, qemu-img)")
        missing_deps.append('libvirt')
    
    # Cloud utils check
    if is_cloud_utils_installed():
        print("✅ Cloud-utils: Zainstalowane")
    else:
        print("❌ Cloud-utils: Brak cloud-localds")
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
        print("🪟 **INSTRUKCJE DLA WSL/Windows:**")
        print("1. Upewnij się że Hyper-V jest włączone w Windows")
        print("2. Uruchom PowerShell jako Administrator i wykonaj:")
        print("   Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform")
        print("3. Dockvirt będzie używał Hyper-V zamiast KVM")
        print("4. Dla najlepszej wydajności rozważ użycie Docker Desktop")
        print()
    
    # Installation commands
    if missing_deps:
        print("🔧 **KOMENDY INSTALACYJNE:**")
        install_commands = generate_install_commands(os_id, missing_deps)
        for cmd in install_commands:
            print(cmd)
        print()
    
    # Summary
    if not missing_deps and not issues:
        print("🎉 Wszystkie zależności są spełnione!")
        return True
    elif missing_deps:
        print(f"⚠️  Brakuje zależności: {', '.join(missing_deps)}")
        return False
    else:
        print("⚠️  System gotowy z drobnymi problemami")
        return True


def auto_install_dependencies():
    """Interactive auto-installation of dependencies."""
    print("🚀 Rozpoczynam auto-instalację zależności...")
    
    os_id, _ = get_os_info()
    missing_deps = []
    
    if not is_docker_installed():
        missing_deps.append('docker')
    if not is_libvirt_installed():
        missing_deps.append('libvirt')
    if not is_cloud_utils_installed():
        missing_deps.append('cloud-utils')
    
    if not missing_deps:
        print("✅ Wszystkie zależności już zainstalowane!")
        return True
    
    print(f"📦 Brakujące zależności: {', '.join(missing_deps)}")
    response = input("Czy chcesz je zainstalować automatycznie? (t/N): ")
    
    if response.lower() not in ['t', 'tak', 'y', 'yes']:
        print("Anulowano auto-instalację")
        return False
    
    install_commands = generate_install_commands(os_id, missing_deps)
    
    for cmd in install_commands:
        if cmd.startswith('#') or not cmd.strip():
            print(cmd)
            continue
        
        print(f"Wykonuję: {cmd}")
        success, stdout, stderr = run_command(cmd, capture_output=False)
        
        if not success:
            print(f"❌ Błąd wykonania: {cmd}")
            print(f"Stderr: {stderr}")
            return False
    
    print("✅ Auto-instalacja zakończona!")
    print("🔄 Wyloguj się i zaloguj ponownie aby grupy zaczęły działać")
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        auto_install_dependencies()
    else:
        check_system_dependencies()
