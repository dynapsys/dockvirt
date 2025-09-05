#!/bin/bash
# Comprehensive installation script for dockvirt
# Supports Ubuntu/Debian, Fedora/RHEL, Arch Linux, and WSL2

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        OS=$(uname -s | tr '[:upper:]' '[:lower:]')
        OS_VERSION="unknown"
    fi
    
    # Check if WSL
    if grep -qi microsoft /proc/version 2>/dev/null; then
        WSL=true
        log_info "Detected WSL environment"
    else
        WSL=false
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Docker
install_docker() {
    log_info "Installing Docker..."
    
    if command_exists docker; then
        log_success "Docker already installed"
        return 0
    fi
    
    # Universal Docker installation
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    # Clean up
    rm -f get-docker.sh
    
    log_success "Docker installed successfully"
}

# Install libvirt based on OS
install_libvirt() {
    log_info "Installing libvirt and KVM..."
    
    case $OS in
        ubuntu|debian)
            sudo apt update
            sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils cloud-image-utils
            ;;
        fedora)
            sudo dnf install -y qemu-kvm libvirt virt-install bridge-utils cloud-utils
            ;;
        centos|rhel)
            sudo yum install -y qemu-kvm libvirt virt-install bridge-utils cloud-utils
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm qemu-full libvirt virt-install bridge-utils cloud-image-utils
            ;;
        *)
            log_error "Unsupported OS for libvirt installation: $OS"
            return 1
            ;;
    esac
    
    # Add user to groups
    sudo usermod -aG libvirt $USER
    sudo usermod -aG kvm $USER
    
    # Enable and start libvirt service
    sudo systemctl enable --now libvirtd
    
    log_success "Libvirt installed successfully"
}

# Install Python and pip
install_python() {
    log_info "Checking Python installation..."
    
    if command_exists python3 && command_exists pip3; then
        log_success "Python3 and pip3 already installed"
        return 0
    fi
    
    case $OS in
        ubuntu|debian)
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv
            ;;
        fedora)
            sudo dnf install -y python3 python3-pip
            ;;
        centos|rhel)
            sudo yum install -y python3 python3-pip
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm python python-pip
            ;;
        *)
            log_error "Unsupported OS for Python installation: $OS"
            return 1
            ;;
    esac
    
    log_success "Python installed successfully"
}

# Install dockvirt
install_dockvirt() {
    log_info "Installing dockvirt..."
    
    # Install dockvirt via pip
    pip3 install --user dockvirt
    
    # Add ~/.local/bin to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        export PATH="$HOME/.local/bin:$PATH"
        log_info "Added ~/.local/bin to PATH"
    fi
    
    log_success "Dockvirt installed successfully"
}

# Check KVM support
check_kvm() {
    if [[ $WSL == true ]]; then
        log_warning "Running in WSL - KVM not available, will use Hyper-V"
        return 0
    fi
    
    if [[ ! -e /dev/kvm ]]; then
        log_warning "/dev/kvm not found. Check if virtualization is enabled in BIOS"
        log_info "To check: grep -E '(vmx|svm)' /proc/cpuinfo"
        return 1
    fi
    
    log_success "KVM support detected"
    return 0
}

# WSL specific setup
setup_wsl() {
    if [[ $WSL != true ]]; then
        return 0
    fi
    
    log_info "Setting up WSL-specific configuration..."
    
    cat << 'EOF'

🪟 WSL SETUP INSTRUCTIONS:

1. Enable Hyper-V on Windows (run as Administrator in PowerShell):
   Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
   
2. Restart Windows after enabling Hyper-V

3. In WSL, dockvirt will automatically detect WSL and use appropriate settings

4. Consider using Docker Desktop for Windows for better integration

EOF
    
    log_success "WSL setup instructions provided"
}

# Main installation function
main() {
    echo "🚀 DockerVirt Installation Script"
    echo "================================="
    echo
    
    # Detect OS
    detect_os
    log_info "Detected OS: $OS $OS_VERSION"
    
    # Check for sudo access
    if ! sudo -n true 2>/dev/null; then
        log_info "This script requires sudo access for system package installation"
        sudo -v || { log_error "Cannot obtain sudo access"; exit 1; }
    fi
    
    # Install components
    install_python || { log_error "Failed to install Python"; exit 1; }
    install_docker || { log_error "Failed to install Docker"; exit 1; }
    
    # Skip libvirt installation in WSL by default
    if [[ $WSL != true ]]; then
        install_libvirt || { log_error "Failed to install libvirt"; exit 1; }
        check_kvm || log_warning "KVM check failed - virtualization may not work properly"
    else
        log_info "Skipping libvirt installation in WSL (using Hyper-V instead)"
    fi
    
    install_dockvirt || { log_error "Failed to install dockvirt"; exit 1; }
    
    # WSL specific setup
    setup_wsl
    
    echo
    log_success "Installation completed successfully! 🎉"
    echo
    echo "Next steps:"
    echo "1. Log out and log back in (or run: newgrp docker)"
    echo "2. Test installation: dockvirt check"
    echo "3. Try an example: cd examples/1-static-nginx-website && dockvirt up"
    echo
    
    if [[ $WSL == true ]]; then
        echo "WSL users: Follow the instructions above for Hyper-V setup"
        echo
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--help]"
        echo
        echo "Install dockvirt and all its dependencies"
        echo "Supports: Ubuntu, Debian, Fedora, CentOS, RHEL, Arch Linux, WSL2"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
