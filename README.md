# dockvirt

[![PyPI version](https://badge.fury.io/py/dockvirt.svg)](https://badge.fury.io/py/dockvirt)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Create lightweight, isolated development environments with a single command.**

`dockvirt` is a CLI tool that automates the process of creating virtual machines (VMs) using libvirt/KVM. It allows you to instantly run applications in Docker containers, with a pre-configured Caddy reverse proxy, fully isolated from your host operating system.

---

## 🤔 Why dockvirt?

The idea for `dockvirt` was born from the daily problems of developers working on their workstations. The main challenges it solves are:

### 🚫 Problem: Port Conflicts on Your Workstation
```bash
# A typical developer situation
docker run -p 3000:3000 frontend-app    # Port 3000 is busy
docker run -p 8080:8080 backend-app     # Port 8080 is busy  
docker run -p 5432:5432 postgres        # Port 5432 is busy
# Local services on your system also use ports!
```

### ✅ Solution: Full Isolation in a VM
```bash
# With dockvirt, each application gets its own VM
dockvirt up --name frontend --domain frontend.local --image nginx:latest --port 80
dockvirt up --name backend --domain backend.local --image httpd:latest --port 80  
dockvirt up --name db --domain db.local --image postgres:latest --port 5432
# Each VM has its own port space - zero conflicts!
```

### 🎯 Key Advantages of the Solution:

*   **Eliminates Port Conflicts**: Each application runs in a separate VM with its own network space.
*   **Isolates Environments**: Different versions of Node.js, Python, and databases without dependency conflicts.
*   **Protects the Host System**: Experiments in a VM do not affect the stability of your workstation.
*   **Simplifies Networking**: Precise domains instead of memorizing ports.
*   **Allows Easy Switching**: Quickly bring different projects `up` or `down`.
*   **It's Lightweight and Fast**: Cloud-init + automatic images = a quick start.
*   **Gives You Full Control**: Based on libvirt for advanced configuration possibilities.

## 🆚 Comparison with Other Tools

| Tool              | Key Advantages                                      | Key Disadvantages                                       |
| ----------------- | --------------------------------------------------- | ------------------------------------------------------- |
| **dockvirt**      | Full isolation (VM), simplicity, automation         | Requires KVM (Linux only)                               |
| **Docker Compose**| Speed, simplicity, high popularity                  | No full isolation from the host system                  |
| **Vagrant**       | Support for multiple providers, flexibility         | Slower start, more complex configuration              |
| **Multipass**     | Very simple to use, good integration with Ubuntu    | Limited control, strong ties to Canonical             |

## 🚀 Key Features

*   **End-to-End Automation**: Create, configure, and destroy VMs with simple commands.
*   **Universal**: Works on popular Linux distributions (Ubuntu, Fedora, and more).
*   **Flexibility**: Full control over VM configuration (RAM, CPU, disk).
*   **Pre-configured Environment**: Automatic installation of Docker and Caddy inside the VM.
*   **Isolation**: Each environment runs in a separate virtual machine.

## 🔧 Requirements

### System Requirements
*   A Linux operating system with KVM support (or WSL2 on Windows)
*   Python 3.8 or higher
*   At least 8GB RAM (for running VMs)
*   20GB+ free disk space

### Required System Packages

#### Ubuntu/Debian:
```bash
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils \
                     cloud-image-utils virt-install docker.io wget
```

#### Fedora/CentOS/RHEL:
```bash
sudo dnf install -y qemu-kvm libvirt libvirt-client virt-install \
                     cloud-utils docker wget
```

#### Arch Linux:
```bash
sudo pacman -S qemu-full libvirt virt-install bridge-utils \
                cloud-image-utils docker wget
```

### Post-Installation Setup
```bash
# Start and enable libvirt service
sudo systemctl start libvirtd
sudo systemctl enable libvirtd

# Add user to required groups
sudo usermod -aG libvirt $USER
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
```

## 📦 Installation

### Quick Install (Automated)

We provide an installation script that handles all dependencies:

```bash
# Download and run the installer
curl -sSL https://raw.githubusercontent.com/dynapsys/dockvirt/main/scripts/install.sh | bash

# Or clone and install manually
git clone https://github.com/dynapsys/dockvirt.git
cd dockvirt
sudo ./scripts/install.sh
```

### Manual Installation

#### 🐧 Linux (Native)

1.  **Install system dependencies** (see Requirements section above)

2.  **Install from PyPI** (recommended):
    ```bash
    pip install dockvirt
    ```

3.  **Or install from the repository** (for developers):
    ```bash
    git clone https://github.com/dynapsys/dockvirt.git
    cd dockvirt
    pip install -e .
    ```

4.  **Verify installation**:
    ```bash
    dockvirt check  # Check system dependencies
    dockvirt --help # Show available commands
    ```

### 🪟 Windows (WSL2)

`dockvirt` works perfectly on WSL2, solving port conflict issues between Windows and your development applications:

1.  **Install WSL2 with Ubuntu**:
    ```powershell
    # In PowerShell as Administrator
    wsl --install -d Ubuntu-22.04
    ```

2.  **In WSL2, install the dependencies**:
    ```bash
    # Update the system
    sudo apt update && sudo apt upgrade -y
    
    # Install all required dependencies
    sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils \
                         cloud-image-utils virt-install docker.io wget
    
    # Configure services
    sudo systemctl start libvirtd
    sudo systemctl enable libvirtd
    sudo usermod -aG libvirt $USER
    sudo usermod -aG docker $USER
    
    # Add your user to the required groups
    sudo usermod -a -G libvirt,kvm $USER
    newgrp libvirt
    
    # Install dockvirt
    pip install dockvirt
    ```

3.  **Start libvirt**:
    ```bash
    sudo systemctl enable --now libvirtd
    sudo systemctl start libvirtd
    ```

### 🐳 System Requirements

**Linux/WSL2:**
- KVM/QEMU (virtualization support)
- libvirt-daemon-system
- cloud-image-utils (`cloud-localds`)
- Docker (for building application images)

**Checking for virtualization support:**
```bash
# Check if KVM is available
lsmod | grep kvm
egrep -c '(vmx|svm)' /proc/cpuinfo  # Should be > 0
```

## 🏗️ How It Works

### VM Creation Process Flow

```mermaid
graph TD
    A[dockvirt up] --> B{config.yaml exists?}
    B -->|No| C[Create default config.yaml]
    B -->|Yes| D[Load configuration]
    C --> D
    D --> E{OS image exists locally?}
    E -->|No| F[Download image from URL]
    E -->|Yes| G[Use local image]
    F --> G
    G --> H[Render cloud-init templates]
    H --> I[Create cloud-init ISO]
    I --> J[Create VM disk with backing file]
    J --> K[Run virt-install]
    K --> L[VM ready with Docker + Caddy]
```

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          HOST SYSTEM                           │
├─────────────────────────────────────────────────────────────────┤
│  dockvirt CLI                                                   │
│  ├── config.py         (configuration management)              │
│  ├── image_manager.py  (OS image downloading)                │
│  ├── vm_manager.py     (VM creation/destruction)               │
│  └── cli.py           (user interface)                         │
├─────────────────────────────────────────────────────────────────┤
│  ~/.dockvirt/                                                   │
│  ├── config.yaml      (default configuration)                  │
│  ├── images/          (OS image cache)                         │
│  └── vm_name/         (cloud-init files for each VM)           │
├─────────────────────────────────────────────────────────────────┤
│  libvirt/KVM                                                    │
│  ├── virt-install     (VM creation)                            │
│  ├── virsh            (VM management)                          │
│  └── qemu-kvm         (virtualization)                         │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        VIRTUAL MACHINE                         │
├─────────────────────────────────────────────────────────────────┤
│  Ubuntu/Fedora OS + cloud-init                                 │
│  ├── Docker Engine    (automatically installed)                │
│  └── docker-compose   (runs containers)                        │
│      ├── Caddy        (reverse proxy on port 80/443)          │
│      └── App Container (Your application)                     │
└─────────────────────────────────────────────────────────────────┘
```

## ⚙️ Configuration

### Configuration Hierarchy

`dockvirt` uses a layered configuration system:

1. **Global config** (`~/.dockvirt/config.yaml`) - System-wide defaults
2. **Project config** (`.dockvirt` file) - Project-specific defaults
3. **CLI parameters** - Override any defaults

### Global Configuration

`dockvirt` automatically creates a configuration file at `~/.dockvirt/config.yaml` on its first run:

```yaml
default_os: ubuntu22.04
images:
  ubuntu22.04:
    name: ubuntu22.04
    url: https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img
    variant: ubuntu22.04
  fedora38:
    name: fedora38
    url: https://archives.fedoraproject.org/pub/archive/fedora/linux/releases/38/Cloud/x86_64/images/Fedora-Cloud-Base-38-1.6.x86_64.qcow2
    variant: fedora38
```

Note: The key `os_images` is also accepted for backward compatibility. The CLI merges both `images` and `os_images` automatically.

### Project Configuration (.dockvirt file)

Create a `.dockvirt` file in your project directory:

```ini
# VM Configuration
name=my-project
domain=my-project.local
image=nginx:latest
port=80
os=ubuntu22.04

# Resource Allocation (optional)
mem=4096    # RAM in MB
disk=20     # Disk in GB
cpus=2      # Number of vCPUs
```

## 🖥️ Usage

### 🚀 New Workflow - Docker Build Inside the VM

**From now on, Docker images are built automatically inside the VM!** You no longer need to build images on the host.

```bash
# Old way (no longer necessary):
# docker build -t my-app:latest .
# dockvirt up --image my-app:latest

# New way - just run:
cd my-project/  # directory with a Dockerfile
dockvirt up --name my-app --domain my-app.local --image my-app:latest --port 80
# The Dockerfile and your app files are automatically copied to the VM and built there!
```

### 🚀 Quick Start with a .dockvirt File

The easiest way is to create a `.dockvirt` file in your project directory (like an `.env` file):

```bash
# Create the .dockvirt file
cat > .dockvirt << EOF
name=my-app
domain=my-app.local
image=my-app:latest
port=80
os=ubuntu22.04
mem=4096
disk=20
cpus=2
EOF

# Now, just run (in the directory with the Dockerfile):
dockvirt up
```

### 🔧 Or Use CLI Parameters

```bash
# Use the default OS (ubuntu22.04)
dockvirt up \
  --name my-app \
  --domain my-app.local \
  --image nginx:latest \
  --port 80

# Or choose a specific OS
dockvirt up \
  --name fedora-app \
  --domain fedora-app.local \
  --image httpd:latest \
  --port 80 \
  --os fedora38
```

### 🌐 Accessing Your Application

After creating the VM, `dockvirt` will display its IP address. Add it to your `/etc/hosts` file:

```
<ip_address> my-app.local
```

Tip: If you use a reverse proxy (Caddy) inside the VM, IP-based checks may require a Host header. You can verify with:

```bash
curl -H 'Host: my-app.local' http://<ip_address>/
```

### 🔎 Getting the VM IP address

Use the built-in `ip` subcommand:

```bash
dockvirt ip --name <vm_name>
```

Note: The VM image installs and enables `qemu-guest-agent`, so IP detection works with both NAT and bridged networking.

### 🔌 Networking: NAT vs Bridge (LAN)

By default, VMs use libvirt NAT (`network=default`). To expose a VM directly in your LAN, use a Linux bridge (e.g., `br0`) and run with `--net bridge=br0`.

- One-time (Fedora/NetworkManager) bridge creation example:

```bash
sudo nmcli con add type bridge ifname br0 con-name br0
sudo nmcli con add type bridge-slave ifname enp3s0 master br0
sudo nmcli con modify br0 ipv4.method auto ipv6.method auto
sudo nmcli con up br0
```

- Per-VM:

```bash
dockvirt up --net bridge=br0
```

- Or persist at project level by adding to `.dockvirt`:

```ini
net=bridge=br0
```

With bridge networking, the VM receives a LAN IP and is visible to other machines on your network.

The `.dockvirt` file has priority over the default parameters, but CLI parameters override everything.

## 🔥 Advanced Usage Examples

### 🚀 Example 1: Multi-Tenant SaaS Platform

**Scenario:** Each SaaS customer gets a completely isolated application instance in a separate VM.

```bash
# First build your application image
docker build -t myapp:v2.1 .

# Customer A
dockvirt up --name client-a --domain client-a.myaas.com --image myapp:v2.1 --os ubuntu22.04

# Customer B (using different image version)
dockvirt up --name client-b --domain client-b.myaas.com --image nginx:latest --os fedora38

# Customer C (beta tester)
dockvirt up --name client-c --domain beta.myaas.com --image myapp:v2.1 --os ubuntu22.04
```

**Result:** 
- ✅ Zero conflicts between customers
- ✅ Different application versions for different customers  
- ✅ Full data and resource isolation
- ✅ Automatic SSL/TLS for each domain

### 🌐 Example 2: Development Environment as Code

**Scenario:** The entire development team gets identical environments with a single command.

```yaml
# .dockvirt-stack (multi-app)
stack:
  frontend:
    image: myapp-frontend:latest
    domain: app.dev.local
    os: ubuntu22.04
  backend:
    image: myapp-api:latest  
    domain: api.dev.local
    os: ubuntu22.04
  database:
    image: postgres:15
    domain: db.dev.local
    os: fedora38
```

```bash
# Note: Stack deployment is a planned feature
# For now, create individual VMs:

# Developer One
dockvirt up --name dev-john-frontend --domain app.dev-john.local --image myapp:latest --port 3000
dockvirt up --name dev-john-api --domain api.dev-john.local --image myapp:latest --port 8080

# Developer Two  
dockvirt up --name dev-jane-frontend --domain app.dev-jane.local --image myapp:latest --port 3000
dockvirt up --name dev-jane-api --domain api.dev-jane.local --image myapp:latest --port 8080
```

## 📚 Detailed Examples

We have prepared several practical examples to show you the possibilities of the new, simplified API:

*   **[Example 1: Static Nginx Website](./examples/1-static-nginx-website)** - Basic usage with automatic image downloading
*   **[Example 2: Python Flask Web App](./examples/2-python-flask-app)** - An application with an Ubuntu vs. Fedora comparison
*   **[Example 3: Operating System Comparison](./examples/3-multi-os-comparison)** - Configuring custom images and performance testing

Each example now uses the new, simplified API - you no longer need to provide image paths or OS variants!

## 🔍 HTTPS Diagnostic Tools

DockerVirt includes comprehensive diagnostic tools for validating HTTPS domains and troubleshooting connection issues:

### 📋 HTTPS Connection Tester

Test all aspects of HTTPS connectivity including DNS, port accessibility, SSL certificates, and content:

```bash
# Test HTTPS connection comprehensively
python3 scripts/https_connection_tester.py https://your-domain.dockvirt.dev:8443

# Example output includes:
# ✅ DNS Resolution: domain -> IP
# ✅ Port Connectivity: Port accessible
# ✅ SSL Certificate: Details and verification status  
# ✅ HTTP Content: Response and headers
# 🔍 Headless Browser Test: Automated browser testing
```

### 🔧 HTTPS Issues Bypass Solutions

When encountering HSTS policies or certificate trust issues:

```bash
# Generate multiple bypass solutions
python3 scripts/hsts_certificate_bypass.py your-domain.dockvirt.dev 8443

# Solutions provided:
# 1️⃣ Alternative domain without HSTS (recommended)
# 2️⃣ Firefox developer profile with disabled certificate checks
# 3️⃣ Chromium with certificate bypass flags
# 4️⃣ Manual HSTS cache clearing instructions
# 5️⃣ Locally trusted certificate generation
```

### 🌐 Common HTTPS Issues & Solutions

**Problem: "SEC_ERROR_UNKNOWN_ISSUER" + HSTS Policy**

```bash
# Quick fix - Use alternative domain:
# 1. Run bypass script to create https-demo.local
python3 scripts/hsts_certificate_bypass.py

# 2. Access via new domain (no HSTS):
# https://https-demo.local:8443/

# 3. Or use Firefox developer profile:
scripts/firefox-dev-https.sh https://your-domain.dockvirt.dev:8443/
```

**Problem: "Unable to Connect" - VM Not Responding**

```bash
# Diagnose connection issues:
python3 scripts/https_connection_tester.py https://domain:port

# Common fixes:
# - Wait for VM to fully boot (60s+)
# - Check if VM service is running inside
# - Verify port is accessible: nc -zv IP PORT
```

### 🔒 Certificate Trust Solutions

For production-like local HTTPS without browser warnings:

```bash
# Method 1: Clear HSTS cache manually
# Firefox: about:networking#hsts -> Delete domain

# Method 2: Use alternative domain
# Generated automatically by bypass script

# Method 3: Install local CA (advanced)
# Creates trusted certificates in /tmp/https-certs/
```

## 🚨 Troubleshooting

### ❌ "cloud-localds: command not found"
```bash
# Install the missing package
sudo apt install cloud-image-utils

# Or on RPM-based systems
sudo dnf install cloud-utils
```

### ❌ Permission denied when accessing libvirt
```bash
# Add your user to the libvirt group
sudo usermod -a -G libvirt $USER
newgrp libvirt

# Restart the service
sudo systemctl restart libvirtd
```

### ❌ Permission denied writing ~/.dockvirt/*.qcow2 or cidata.iso (qemu:///system)

When using the system libvirt (qemu:///system), VMs run as the `qemu` user and must be able to traverse your home and read VM files. On Fedora/SELinux you may also need proper labels.

Fix (safe to apply):

```bash
# Allow qemu to traverse your home
sudo setfacl -m u:qemu:x "$HOME"

# Give qemu read access on dockvirt files
sudo setfacl -R -m u:qemu:rx "$HOME/.dockvirt"
sudo find "$HOME/.dockvirt" -type f -name '*.qcow2' -exec setfacl -m u:qemu:rw {} +
sudo find "$HOME/.dockvirt" -type f -name '*.iso'   -exec setfacl -m u:qemu:r  {} +

# SELinux labels (Fedora/SELinux)
# IMPORTANT: Label only image files, not the entire directory
# If you previously labeled the whole tree, remove that rule first:
#   sudo semanage fcontext -d -t svirt_image_t "$HOME/.dockvirt(/.*)?"
sudo semanage fcontext -a -t svirt_image_t "$HOME/.dockvirt(/.*)?\\.qcow2"
sudo semanage fcontext -a -t svirt_image_t "$HOME/.dockvirt(/.*)?\\.iso"
sudo restorecon -Rv "$HOME/.dockvirt"
```

Tips:

- Always connect virsh to the system libvirt with: `virsh --connect qemu:///system <subcommand>`.
- Alternatively, configure a libvirt storage pool (e.g. `/var/lib/libvirt/images/dockvirt`) and store VM files there to avoid ACLs on `$HOME`.

### ❌ qemu-img "Failed to get write lock"

This usually happens after an interrupted run that left a domain or disk around. Fix:

```bash
# Tear down the VM if it exists
dockvirt down --name <vm_name>

# Or auto-heal common leftovers
make heal
```

Then try `dockvirt up` again.

### ❌ KVM not available
```bash
# Check if virtualization is enabled in your BIOS
egrep -c '(vmx|svm)' /proc/cpuinfo

# On WSL2, make sure Hyper-V is enabled
# In PowerShell as Administrator:
# Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

### ❌ Port conflicts on Windows + WSL2
```bash
# Check which ports Windows is using
netstat -an | findstr LISTENING

# In WSL2, all VMs have isolated ports
dockvirt up --name app1 --domain app1.local --image nginx --port 80
dockvirt up --name app2 --domain app2.local --image apache --port 80
# Both run without conflicts!
```

## 🩺 Dockvirt Doctor & Dev venv (PEP 668)

Use Dockvirt Doctor to diagnose and optionally fix environment issues. This is especially helpful on Homebrew Python (PEP 668 externally-managed environments).

```bash
# Quick diagnostics
make doctor
python3 scripts/doctor.py --summary

# Detailed logging + file log
python3 scripts/doctor.py --verbose --log-file ~/.dockvirt/doctor.log

# Auto-fix common issues (may require sudo and re-login for groups)
make doctor-fix
```

Avoid running `make ...` with `sudo`. Doctor already detects `SUDO_USER` and acts on your real home (`/home/<user>`), but invoking make with sudo may lead to confusing paths and permissions.

### Development install with a virtualenv (PEP 668 friendly)

```bash
# Use your preferred Python (example shows 3.13)
PY=$(command -v python3.13 || command -v python3)

# Create a venv that can access system packages (e.g. python3-libvirt)
$PY -m venv --system-site-packages .venv-3.13
source .venv-3.13/bin/activate

# Install the project without forcing libvirt-python from pip
pip install -U pip setuptools wheel
pip install -e . --no-deps
pip install jinja2 click pyyaml

# Verify and diagnose
python -m dockvirt.cli --help
python3 scripts/doctor.py --summary
```

### Ensure libvirt default network is active

```bash
sudo systemctl enable --now libvirtd
sudo virsh net-define /usr/share/libvirt/networks/default.xml || true
sudo virsh net-start default || true
sudo virsh net-autostart default
```

Tip: The CLI runs a preflight network check and will print hints if the `default` network is missing or inactive.

## 🤖 Automation Agent

Use the built-in Automation Agent to validate your setup end-to-end, including domain reachability. It can optionally apply safe fixes (ACL/SELinux for qemu:///system and /etc/hosts entries) using sudo.

```bash
# Summary mode (no sudo changes): tests examples, prints report
make agent

# Auto-fix mode (sudo): doctor --fix, default network, ACL/SELinux, /etc/hosts
make agent-fix

# Filter examples, skip host Docker build (image built inside VM)
PY=.venv-3.13/bin/python \
  $PY scripts/agent.py run --example 1-static-nginx-website --skip-host-build

# Select OS variants to test
$PY scripts/agent.py run --os ubuntu22.04 --os fedora38 --skip-host-build

# Report location
cat agent_report.md
```

Optional local LLM remediation: you can enable a small local model (via Ollama) to propose and apply safe fixes automatically.

```bash
export DOCKVIRT_USE_LLM=1
# Optional model selection (default: llama3.2:3b)
export DOCKVIRT_LLM_MODEL=llama3.2:3b
make agent-fix
```

Note: Do not run `sudo make agent-fix`. The agent will request sudo where needed and stream commands in the console.

What it does:

- Creates VMs with `dockvirt up` per example and OS variant.
- Fetches VM IP via virsh leases and checks HTTP by IP.
- Verifies local DNS for domain (from `.dockvirt`) and checks HTTP via domain.
- Optionally appends to `/etc/hosts` (auto mode) when a domain doesn’t resolve.
- Cleans up VMs with `dockvirt down`.

## 💾 Generating Images and Packages

### 📦 Distribution Packages (.deb/.rpm)

**Note: Image generation is a planned feature, not yet implemented**

```bash
# These commands are planned for future releases:
# dockvirt generate-image --type deb-package --output my-app.deb
# dockvirt generate-image --type rpm-package --output my-app.rpm

# For now, use standard VM deployment:
dockvirt up --name production-app --domain app.local --image nginx:latest --port 80
```

### 🥧 Raspberry Pi SD Card Image

**Note: Raspberry Pi support is planned for future releases**

```bash
# This feature is planned for future releases:
# dockvirt generate-image --type raspberry-pi --output rpi-dockvirt.img

# For now, use standard x86_64 deployment
```

### 💻 PC Bootable ISO

**Note: ISO generation is planned for future releases**

```bash
# This feature is planned for future releases:
# dockvirt generate-image --type pc-iso --output production-server.iso
```

**Example production-stack.yaml:**
```yaml
apps:
  frontend:
    image: mycompany/frontend:v2.1
    domain: app.company.com
    port: 3000
  api:
    image: mycompany/api:v2.1  
    domain: api.company.com
    port: 8080
  monitoring:
    image: grafana/grafana:latest
    domain: monitoring.company.com
    port: 3000
config:
  auto_start: true
  ssl_enabled: true
  backup_enabled: true
```

### 🚢 Podman Support

```bash
# Use Podman instead of Docker
export DOCKVIRT_RUNTIME=podman
dockvirt up --name my-app --image nginx:latest

# Or in the .dockvirt file
runtime=podman
name=my-app
image=nginx:latest
```

## 🛠️ Development

The repository contains a `Makefile` to facilitate the development process. See the [CONTRIBUTING.md](./CONTRIBUTING.md) file to learn how to contribute to the project's development.

If you're developing locally inside this repository, prefer using the project virtualenv to avoid conflicts with system or Homebrew installations:

```bash
make install
.
venv-3.13/bin/dockvirt --help

# If your PATH resolves to another dockvirt (e.g., Homebrew), use the venv binary explicitly:
which dockvirt
./.venv-3.13/bin/dockvirt up
```

## ✍️ Author

**Tom Sapletta** - An experienced programmer and open-source enthusiast. Passionate about automation and creating tools that make developers' lives easier.

## 📜 License

This project is licensed under the **Apache 2.0 License**. See the [LICENSE](LICENSE) file for details.

## 📚 Documentation Index

- Main: [README.md](./README.md)
- Contributing: [CONTRIBUTING.md](./CONTRIBUTING.md)
- Diagnostic tools overview: [scripts/README_DIAGNOSTIC_TOOLS.md](./scripts/README_DIAGNOSTIC_TOOLS.md)
- Examples overview: [examples/README.md](./examples/README.md)
- Examples (direct):
  - [examples/1-static-nginx-website/README.md](./examples/1-static-nginx-website/README.md)
  - [examples/2-python-flask-app/README.md](./examples/2-python-flask-app/README.md)
  - [examples/3-multi-os-comparison/README.md](./examples/3-multi-os-comparison/README.md)
  - [examples/4-microservices-stack/README.md](./examples/4-microservices-stack/README.md)
  - [examples/5-production-deployment/README.md](./examples/5-production-deployment/README.md)
- Testing and automation:
  - Command validator: [scripts/test_commands_robust.py](./scripts/test_commands_robust.py)
  - Examples test runner: [scripts/test_examples.py](./scripts/test_examples.py)
  - Automation Agent: [scripts/agent.py](./scripts/agent.py)
  - Doctor: [scripts/doctor.py](./scripts/doctor.py)
  - Recent reports (generated): [test_results.md](./test_results.md), [command_test_results.md](./command_test_results.md), [agent_report.md](./agent_report.md)
- System setup:
  - Installer: [scripts/install.sh](./scripts/install.sh)
  - LAN exposure tools: [scripts/systemd/](./scripts/systemd/), [scripts/dockvirt_lan_expose.sh](./scripts/dockvirt_lan_expose.sh), [scripts/comprehensive_lan_test.py](./scripts/comprehensive_lan_test.py)

## 🧭 Code Reference Map

- CLI entrypoint: [dockvirt/cli.py](./dockvirt/cli.py)
- Configuration loader and layered `.dockvirt`: [dockvirt/config.py](./dockvirt/config.py)
- Image management (download/cache): [dockvirt/image_manager.py](./dockvirt/image_manager.py)
- VM lifecycle (create/destroy/IP): [dockvirt/vm_manager.py](./dockvirt/vm_manager.py)
- System checks: [dockvirt/system_check.py](./dockvirt/system_check.py)
- Self-heal routines: [dockvirt/self_heal.py](./dockvirt/self_heal.py)
- Image generator (planned features scaffolding): [dockvirt/image_generator.py](./dockvirt/image_generator.py)
- Event log DB: [dockvirt/logdb.py](./dockvirt/logdb.py)
- Cloud-init templates: [dockvirt/templates/](./dockvirt/templates/)

## 🐳 Docker Test Environment

To validate README/Makefile commands in a reproducible container with libvirt/KVM, use these Makefile targets (they call scripts in `scripts/docker-test/`):

```bash
make docker-test-build   # build the test image
make docker-test-quick   # doctor + command tests + build (no VM)
make docker-test-full    # full flow: doctor-fix, e2e, examples, agent (VMs)
make docker-test-shell   # interactive shell for debugging
```

Scripts:
- [scripts/docker-test/Dockerfile](./scripts/docker-test/Dockerfile)
- [scripts/docker-test/entrypoint.sh](./scripts/docker-test/entrypoint.sh)
- [scripts/docker-test/build.sh](./scripts/docker-test/build.sh)
- [scripts/docker-test/run-quick.sh](./scripts/docker-test/run-quick.sh)
- [scripts/docker-test/run-full.sh](./scripts/docker-test/run-full.sh)
- [scripts/docker-test/shell.sh](./scripts/docker-test/shell.sh)
- [scripts/docker-test/clean.sh](./scripts/docker-test/clean.sh)

### ASCII: Docker Test Architecture

```
+----------------------+         +---------------------------------+
|      Host (Linux)    |         |        Docker Container         |
|----------------------|         |---------------------------------|
| Docker, /dev/kvm?    |  mount  | libvirtd + qemu-kvm + virsh     |
| Network: host mode   | <-----> | /workspace (repo bind-mounted)  |
|                       \        | Python venv (.venv-3.13)        |
+----------------------+ \       | Makefile targets (tests)        |
                           \---->| Default libvirt network (NAT)   |
                                   +---------------------------------+
```

### Mermaid: Automation Agent Flow

```mermaid
flowchart TD
  A[make agent / agent-fix] --> B[Doctor check / fix]
  B --> C[Ensure libvirt default network]
  C --> D[Iterate examples]
  D --> E[dockvirt up]
  E --> F[Wait for IP]
  F --> G[HTTP by IP]
  G --> H[DNS resolve domain]
  H --> I[HTTP by domain]
  I --> J[dockvirt down]
  J --> K[Report: agent_report.md]
