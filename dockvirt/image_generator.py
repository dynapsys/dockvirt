#!/usr/bin/env python3
"""
Bootable image generator for dockvirt.
Generates bootable SD card images for Raspberry Pi, bootable ISO images for PC,
and distributable packages (deb/rpm) with Docker applications.
"""

import subprocess
import tempfile
import shutil
import yaml
from pathlib import Path


def generate_bootable_image(
    image_type="raspberry-pi",
    size="8GB",
    output_path="dockvirt.img",
    apps=None,
    domains=None,
    config_file=None,
):
    """Generate bootable image with dockvirt configuration."""
    supported_types = ['raspberry-pi', 'pc-iso', 'deb-package', 'rpm-package']
    
    if image_type not in supported_types:
        raise ValueError(f"Unsupported image type: {image_type}. Supported types are: {supported_types}")
    
    if apps is None:
        apps = []
    if domains is None:
        domains = []
        
    # Load config file if provided
    config = {}
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        if image_type == 'raspberry-pi':
            return _generate_rpi_image(temp_dir, size, output_path, apps, domains, config)
        elif image_type == 'pc-iso':
            return _generate_pc_iso(temp_dir, size, output_path, apps, domains, config)
        elif image_type == 'deb-package':
            return _generate_deb_package(temp_dir, output_path, apps, domains, config)
        elif image_type == 'rpm-package':
            return _generate_rpm_package(temp_dir, output_path, apps, domains, config)
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def _generate_deb_package(temp_dir, output_path, apps, domains, config):
    """Generate .deb package with Docker applications."""
    print("📦 Generating .deb package...")
    
    # Create package structure
    pkg_dir = temp_dir / "dockvirt-app"
    pkg_dir.mkdir()
    
    # DEBIAN control directory
    debian_dir = pkg_dir / "DEBIAN"
    debian_dir.mkdir()
    
    # Control file
    control_content = f"""Package: dockvirt-app
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Depends: docker.io, libvirt-daemon-system, cloud-image-utils
Maintainer: DockerVirt Team <team@dockvirt.io>
Description: DockerVirt application package
 Pre-configured Docker applications for VM deployment.
 Applications: {', '.join(apps)}
 Domains: {', '.join(domains)}
"""
    
    with open(debian_dir / "control", "w") as f:
        f.write(control_content)
        
    # Create post-install script
    postinst_content = """#!/bin/bash
set -e

# Install dockvirt if not already installed
if ! command -v dockvirt &> /dev/null; then
    pip3 install dockvirt
fi

# Create systemd service for auto-deployment
cat > /etc/systemd/system/dockvirt-app.service << 'EOF'
[Unit]
Description=DockerVirt Application Deployment
After=docker.service libvirtd.service

[Service]
Type=oneshot
RemainAfterExit=yes
"""

    for i, (app, domain) in enumerate(zip(apps, domains)):
        postinst_content += f"""
ExecStart=/usr/local/bin/dockvirt up --name app{i+1} --domain {domain} --image {app} --port 80
"""

    postinst_content += """
[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable dockvirt-app.service

echo "✅ DockerVirt application package installed successfully!"
echo "Run 'systemctl start dockvirt-app' to deploy applications"
"""
    
    with open(debian_dir / "postinst", "w") as f:
        f.write(postinst_content)
    
    subprocess.run(["chmod", "755", str(debian_dir / "postinst")], check=True)
    
    # Build .deb package
    subprocess.run(["dpkg-deb", "--build", str(pkg_dir), output_path], check=True)
    print(f"✅ .deb package created: {output_path}")
    return output_path


def _generate_rpm_package(temp_dir, output_path, apps, domains, config):
    """Generate .rpm package with Docker applications."""
    print("📦 Generating .rpm package...")
    
    # Create RPM build structure
    rpm_dir = temp_dir / "rpmbuild"
    for subdir in ["BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS"]:
        (rpm_dir / subdir).mkdir(parents=True)
    
    # Create spec file
    spec_content = f"""Name: dockvirt-app
Version: 1.0.0
Release: 1%{{?dist}}
Summary: DockerVirt application package
License: GPL
Requires: docker, libvirt-daemon-system

%description
Pre-configured Docker applications for VM deployment.
Applications: {', '.join(apps)}
Domains: {', '.join(domains)}

%install
mkdir -p %{{buildroot}}/etc/systemd/system

cat > %{{buildroot}}/etc/systemd/system/dockvirt-app.service << 'EOF'
[Unit]
Description=DockerVirt Application Deployment
After=docker.service libvirtd.service

[Service]
Type=oneshot
RemainAfterExit=yes
"""

    for i, (app, domain) in enumerate(zip(apps, domains)):
        spec_content += f"""
ExecStart=/usr/local/bin/dockvirt up --name app{i+1} --domain {domain} --image {app} --port 80
"""

    spec_content += """EOF

%post
if ! command -v dockvirt &> /dev/null; then
    pip3 install dockvirt
fi
systemctl daemon-reload
systemctl enable dockvirt-app.service

%files
/etc/systemd/system/dockvirt-app.service
"""
    
    with open(rpm_dir / "SPECS" / "dockvirt-app.spec", "w") as f:
        f.write(spec_content)
    
    # Build RPM
    subprocess.run([
        "rpmbuild", "--define", f"_topdir {rpm_dir}",
        "-ba", str(rpm_dir / "SPECS" / "dockvirt-app.spec")
    ], check=True)
    
    # Move RPM to output location
    rpm_files = list((rpm_dir / "RPMS" / "x86_64").glob("*.rpm"))
    if rpm_files:
        shutil.move(str(rpm_files[0]), output_path)
        print(f"✅ .rpm package created: {output_path}")
        return output_path
    else:
        raise RuntimeError("Failed to create RPM package")


def _generate_rpi_image(temp_dir, size, output_path, apps, domains, config):
    """Generate Raspberry Pi SD card image."""
    print("🥧 Generating Raspberry Pi image...")
    
    # Download Raspberry Pi OS Lite
    base_image_url = "https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2023-12-11/2023-12-11-raspios-bookworm-armhf-lite.img.xz"
    base_image = temp_dir / "raspios-lite.img.xz"
    
    print("📥 Downloading Raspberry Pi OS Lite...")
    subprocess.run(["wget", "-O", str(base_image), base_image_url], check=True)
    subprocess.run(["xz", "-d", str(base_image)], check=True)
    
    extracted_image = temp_dir / "raspios-lite.img"
    
    # Create cloud-init config for automatic setup
    cloud_init_content = """#cloud-config
users:
  - default
  - name: dockvirt
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash

runcmd:
  - curl -fsSL https://get.docker.com | sh
  - usermod -aG docker dockvirt
  - pip3 install dockvirt
"""

    for i, (app, domain) in enumerate(zip(apps, domains)):
        cloud_init_content += f"  - dockvirt up --name app{i+1} --domain {domain} --image {app} --port 80\n"

    # Create boot config
    boot_config = temp_dir / "boot_config"
    boot_config.mkdir()
    
    with open(boot_config / "user-data", "w") as f:
        f.write(cloud_init_content)
    
    with open(boot_config / "meta-data", "w") as f:
        f.write("instance-id: dockvirt-rpi\n")
    
    # TODO: Mount image and copy cloud-init files
    # This would require root privileges and proper loop device handling
    
    shutil.copy(str(extracted_image), output_path)
    print(f"✅ Raspberry Pi image created: {output_path}")
    print("⚠️  Manual setup required: Copy cloud-init files to the boot partition")
    return output_path


def _generate_pc_iso(temp_dir, size, output_path, apps, domains, config):
    """Generate bootable PC ISO image."""
    print("💻 Generating PC ISO image...")
    
    # Download Ubuntu Server ISO
    base_iso_url = "https://releases.ubuntu.com/22.04/ubuntu-22.04.3-live-server-amd64.iso"
    base_iso = temp_dir / "ubuntu-server.iso"
    
    print("📥 Downloading Ubuntu Server ISO...")
    subprocess.run(["wget", "-O", str(base_iso), base_iso_url], check=True)
    
    # Create autoinstall config
    autoinstall_config = {
        "version": 1,
        "identity": {
            "hostname": "dockvirt-server",
            "username": "dockvirt",
            "password": "$6$rounds=4096$aabbccddeeff$password_hash"  # Change in production
        },
        "packages": ["docker.io", "python3-pip"],
        "late-commands": [
            "pip3 install dockvirt"
        ]
    }
    
    for i, (app, domain) in enumerate(zip(apps, domains)):
        autoinstall_config["late-commands"].append(
            f"dockvirt up --name app{i+1} --domain {domain} --image {app} --port 80"
        )
    
    # TODO: Create custom ISO with autoinstall
    # This would require proper ISO manipulation tools
    
    shutil.copy(str(base_iso), output_path)
    print(f"✅ PC ISO created: {output_path}")
    print("⚠️  Manual setup required: Add autoinstall configuration")
    return output_path


def generate_image_cli(image_type, size, output, config_file, apps, domains):
    """CLI interface for image generation."""
    # Parse configuration
    config = {}
    
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    
    # Convert apps and domains to lists if provided
    app_list = apps.split(',') if apps else []
    domain_list = domains.split(',') if domains else []
    
    if len(app_list) != len(domain_list):
        raise ValueError("The number of apps must match the number of domains")
    
    # Generate image using the main function
    return generate_bootable_image(
        image_type=image_type,
        size=size,
        output_path=output,
        apps=app_list,
        domains=domain_list,
        config_file=config_file
    )


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python image_generator.py <type> <size> <output> [config.yaml]")
        print("Types: raspberry-pi, pc-iso, deb-package, rpm-package")
        sys.exit(1)
    
    image_type = sys.argv[1]
    size = sys.argv[2]
    output = sys.argv[3]
    config_file = sys.argv[4] if len(sys.argv) > 4 else None
    
    try:
        generate_image_cli(image_type, size, output, config_file, None, None)
        print(f"✅ Image generated successfully: {output}")
    except Exception as e:
        print(f"❌ Error generating image: {e}")
        sys.exit(1)
