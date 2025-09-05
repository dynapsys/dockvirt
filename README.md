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
dockvirt up --name frontend --domain frontend.local --image frontend-app:latest --port 3000
dockvirt up --name backend --domain backend.local --image backend-app:latest --port 8080  
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

*   A Linux operating system with KVM support.
*   Installed packages: `qemu-kvm`, `libvirt-daemon-system`, `virt-manager`, `cloud-image-utils`.
*   A cloud image (`.qcow2`) for your chosen distribution (e.g., Ubuntu 22.04, Fedora Cloud Base).

## 📦 Installation

### 🐧 Linux (Native)

1.  **Install from PyPI** (recommended):
    ```bash
    pip install dockvirt
    ```

2.  **Or install from the repository** (for developers):
    ```bash
    git clone https://github.com/dynapsys/dockvirt.git
    cd dockvirt
    make install
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
    
    # Install KVM/QEMU and libvirt
    sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils
    sudo apt install -y cloud-image-utils  # for cloud-localds
    
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

`dockvirt` automatically creates a configuration file at `~/.dockvirt/config.yaml` on its first run:

```yaml
default_os: ubuntu22.04
images:
  ubuntu22.04:
    url: https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img
    variant: ubuntu22.04
  fedora38:
    url: https://download.fedoraproject.org/pub/fedora/linux/releases/38/Cloud/x86_64/images/Fedora-Cloud-Base-38-1.6.x86_64.qcow2
    variant: fedora-cloud-base-38
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

The `.dockvirt` file has priority over the default parameters, but CLI parameters override everything.

## 🔥 Advanced Usage Examples

### 🚀 Example 1: Multi-Tenant SaaS Platform

**Scenario:** Each SaaS customer gets a completely isolated application instance in a separate VM.

```bash
# Customer A
dockvirt up --name client-a --domain client-a.myaas.com --image myapp:v2.1 --os ubuntu22.04

# Customer B  
dockvirt up --name client-b --domain client-b.myaas.com --image myapp:v1.9 --os fedora38

# Customer C (beta tester)
dockvirt up --name client-c --domain beta.myaas.com --image myapp:v3.0-beta --os ubuntu22.04
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
# Developer One
dockvirt stack deploy dev-john

# Developer Two
dockvirt stack deploy dev-jane

# QA environment
dockvirt stack deploy qa-env
```

## 📚 Detailed Examples

We have prepared several practical examples to show you the possibilities of the new, simplified API:

*   **[Example 1: Static Nginx Website](./examples/1-static-nginx-website)** - Basic usage with automatic image downloading
*   **[Example 2: Python Flask Web App](./examples/2-python-flask-app)** - An application with an Ubuntu vs. Fedora comparison
*   **[Example 3: Operating System Comparison](./examples/3-multi-os-comparison)** - Configuring custom images and performance testing

Each example now uses the new, simplified API - you no longer need to provide image paths or OS variants!

## 🚨 Troubleshooting

### ❌ "cloud-localds: command not found"
```bash
# Install the missing package
sudo apt install cloud-image-utils

# Or on RPM-based systems
sudo dnf install cloud-utils
```

### ❌ "Permission denied" when accessing libvirt
```bash
# Add your user to the libvirt group
sudo usermod -a -G libvirt $USER
newgrp libvirt

# Restart the service
sudo systemctl restart libvirtd
```

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

## 💾 Generating Images and Packages

### 📦 Distribution Packages (.deb/.rpm)

```bash
# Generate a .deb package with automatic Docker installation
dockvirt generate-image \
  --type deb-package \
  --output my-app.deb \
  --apps "nginx:latest,postgres:13" \
  --domains "app.local,db.local"

# Generate an .rpm package 
dockvirt generate-image \
  --type rpm-package \
  --output my-app.rpm \
  --apps "nginx:latest" \
  --domains "app.local"
```

### 🥧 Raspberry Pi SD Card Image

```bash
# Generate an SD card image with dockvirt pre-installed
dockvirt generate-image \
  --type raspberry-pi \
  --size 8GB \
  --output rpi-dockvirt.img \
  --apps "nginx:latest,postgres:13" \
  --domains "app.pi.local,db.pi.local"

# Flash to an SD card
dd if=rpi-dockvirt.img of=/dev/sdX bs=4M status=progress
```

### 💻 PC Bootable ISO

```bash
# Generate a bootable ISO for a PC/server
dockvirt generate-image \
  --type pc-iso \
  --size 16GB \
  --output production-server.iso \
  --config production-stack.yaml
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

## ✍️ Author

**Tom Sapletta** - An experienced programmer and open-source enthusiast. Passionate about automation and creating tools that make developers' lives easier.

## 📜 License

This project is licensed under the **Apache 2.0 License**. See the [LICENSE](LICENSE) file for details.
