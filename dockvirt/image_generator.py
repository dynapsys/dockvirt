#!/usr/bin/env python3
"""
Bootable image generator for dockvirt.
Creates bootable SD card images for Raspberry Pi and ISO images for PC.
"""

import os
import subprocess
import tempfile
import yaml
from pathlib import Path
from jinja2 import Template


class ImageGenerator:
    """Generate bootable images with pre-configured dockvirt setups."""
    
    def __init__(self):
        self.temp_dir = None
        self.supported_types = ['raspberry-pi', 'pc-iso', 'usb-stick']
        
    def generate_image(self, image_type, size, output_path, config):
        """Generate bootable image with dockvirt configuration."""
        if image_type not in self.supported_types:
            raise ValueError(f"Unsupported image type: {image_type}")
        
        self.temp_dir = Path(tempfile.mkdtemp())
        
        try:
            if image_type == 'raspberry-pi':
                return self._generate_rpi_image(size, output_path, config)
            elif image_type == 'pc-iso':
                return self._generate_pc_iso(size, output_path, config)
            elif image_type == 'usb-stick':
                return self._generate_usb_image(size, output_path, config)
        finally:
            # Cleanup temp directory
            subprocess.run(['rm', '-rf', str(self.temp_dir)], check=False)
    
    def _generate_rpi_image(self, size, output_path, config):
        """Generate Raspberry Pi SD card image."""
        print("🥧 Generating Raspberry Pi SD card image...")
        
        # Download base Raspberry Pi OS Lite
        base_image = self.temp_dir / "raspios-lite.img"
        self._download_base_image("raspberry-pi", base_image)
        
        # Mount and customize image
        mount_point = self.temp_dir / "mount"
        mount_point.mkdir()
        
        # Create loop device and mount
        loop_device = self._create_loop_device(base_image)
        self._mount_image(loop_device, mount_point)
        
        try:
            # Install dockvirt and dependencies
            self._install_dockvirt_in_image(mount_point, "arm64")
            
            # Configure auto-start services
            self._configure_autostart(mount_point, config)
            
            # Copy application configs
            self._copy_app_configs(mount_point, config)
            
            # Resize image if needed
            if size != "default":
                self._resize_image(base_image, size)
            
            # Copy to output location
            subprocess.run(['cp', str(base_image), output_path], check=True)
            
        finally:
            self._unmount_image(mount_point)
            self._detach_loop_device(loop_device)
        
        print(f"✅ Raspberry Pi image created: {output_path}")
        return True
    
    def _generate_pc_iso(self, size, output_path, config):
        """Generate PC bootable ISO."""
        print("💻 Generating PC bootable ISO...")
        
        # Use Ubuntu Server as base
        iso_dir = self.temp_dir / "iso"
        iso_dir.mkdir()
        
        # Download Ubuntu Server ISO
        base_iso = self.temp_dir / "ubuntu-server.iso"
        self._download_base_image("ubuntu-server", base_iso)
        
        # Extract ISO contents
        subprocess.run([
            'xorriso', '-osirrox', 'on',
            '-indev', str(base_iso),
            '-extract', '/', str(iso_dir)
        ], check=True)
        
        # Customize preseed for automated installation
        self._create_preseed_config(iso_dir, config)
        
        # Add dockvirt installation scripts
        self._add_dockvirt_installer(iso_dir, config)
        
        # Create custom initrd with dockvirt configs
        self._customize_initrd(iso_dir, config)
        
        # Rebuild ISO
        subprocess.run([
            'xorriso', '-as', 'mkisofs',
            '-r', '-V', 'DockerVirt-Server',
            '-cache-inodes', '-J', '-l',
            '-b', 'isolinux/isolinux.bin',
            '-c', 'isolinux/boot.cat',
            '-no-emul-boot', '-boot-load-size', '4',
            '-boot-info-table',
            '-eltorito-alt-boot',
            '-e', 'boot/grub/efi.img',
            '-no-emul-boot',
            '-o', output_path,
            str(iso_dir)
        ], check=True)
        
        print(f"✅ PC ISO created: {output_path}")
        return True
    
    def _generate_usb_image(self, size, output_path, config):
        """Generate USB stick image."""
        print("🔌 Generating USB stick image...")
        
        # Similar to PC ISO but optimized for USB boot
        return self._generate_pc_iso(size, output_path, config)
    
    def _download_base_image(self, image_type, output_path):
        """Download base OS image."""
        urls = {
            'raspberry-pi': 'https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2023-05-03/2023-05-03-raspios-bullseye-arm64-lite.img.xz',
            'ubuntu-server': 'https://releases.ubuntu.com/22.04/ubuntu-22.04.3-live-server-amd64.iso'
        }
        
        if image_type not in urls:
            raise ValueError(f"No base image URL for type: {image_type}")
        
        print(f"📥 Downloading base image for {image_type}...")
        subprocess.run([
            'wget', '-O', str(output_path), urls[image_type]
        ], check=True)
        
        # Extract if compressed
        if str(output_path).endswith('.xz'):
            subprocess.run(['xz', '-d', str(output_path)], check=True)
            return Path(str(output_path)[:-3])  # Remove .xz extension
        
        return output_path
    
    def _create_loop_device(self, image_path):
        """Create loop device for image."""
        result = subprocess.run([
            'sudo', 'losetup', '--find', '--partscan', '--show', str(image_path)
        ], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    
    def _mount_image(self, loop_device, mount_point):
        """Mount image filesystem."""
        # Mount root partition (usually partition 2 for RPi)
        subprocess.run([
            'sudo', 'mount', f"{loop_device}p2", str(mount_point)
        ], check=True)
        
        # Mount boot partition if exists
        boot_mount = mount_point / "boot"
        if not boot_mount.exists():
            boot_mount.mkdir()
        subprocess.run([
            'sudo', 'mount', f"{loop_device}p1", str(boot_mount)
        ], check=False)  # Don't fail if boot partition doesn't exist
    
    def _install_dockvirt_in_image(self, mount_point, arch):
        """Install dockvirt and dependencies in mounted image."""
        print("📦 Installing dockvirt in image...")
        
        # Use chroot to install packages
        chroot_script = mount_point / "install_dockvirt.sh"
        
        install_script = f"""#!/bin/bash
set -e

# Update package lists
apt update

# Install Python and pip
apt install -y python3 python3-pip python3-venv

# Install Docker
curl -fsSL https://get.docker.com | sh

# Install libvirt and KVM
apt install -y qemu-kvm libvirt-daemon-system libvirt-clients cloud-image-utils

# Install dockvirt
pip3 install dockvirt

# Enable services
systemctl enable docker
systemctl enable libvirtd

# Add default user to groups
usermod -aG docker pi || usermod -aG docker ubuntu
usermod -aG libvirt pi || usermod -aG libvirt ubuntu
usermod -aG kvm pi || usermod -aG kvm ubuntu

# Clean up
apt clean
rm -f /install_dockvirt.sh
"""
        
        with open(chroot_script, 'w') as f:
            f.write(install_script)
        
        subprocess.run(['sudo', 'chmod', '+x', str(chroot_script)], check=True)
        subprocess.run([
            'sudo', 'chroot', str(mount_point), '/install_dockvirt.sh'
        ], check=True)
    
    def _configure_autostart(self, mount_point, config):
        """Configure dockvirt to start applications on boot."""
        print("⚙️ Configuring auto-start services...")
        
        # Create systemd service for dockvirt auto-start
        service_file = mount_point / "etc/systemd/system/dockvirt-autostart.service"
        
        service_content = """[Unit]
Description=DockerVirt Auto-start Applications
After=network.target docker.service libvirtd.service
Requires=docker.service libvirtd.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
ExecStart=/usr/local/bin/dockvirt-autostart.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        # Create auto-start script
        script_file = mount_point / "usr/local/bin/dockvirt-autostart.sh"
        
        script_content = self._generate_autostart_script(config)
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        subprocess.run(['sudo', 'chmod', '+x', str(script_file)], check=True)
        
        # Enable the service
        subprocess.run([
            'sudo', 'chroot', str(mount_point),
            'systemctl', 'enable', 'dockvirt-autostart.service'
        ], check=True)
    
    def _generate_autostart_script(self, config):
        """Generate script to auto-start configured applications."""
        script_lines = [
            "#!/bin/bash",
            "# DockerVirt auto-start script",
            "set -e",
            "",
            "# Wait for system to be ready",
            "sleep 30",
            "",
            "cd /home/dockvirt",
            ""
        ]
        
        # Add commands for each configured app
        if 'apps' in config:
            for app_name, app_config in config['apps'].items():
                cmd_parts = [
                    "dockvirt up",
                    f"--name {app_name}",
                    f"--domain {app_config.get('domain', f'{app_name}.local')}",
                    f"--image {app_config['image']}",
                    f"--port {app_config.get('port', 80)}"
                ]
                
                if 'os' in app_config:
                    cmd_parts.append(f"--os {app_config['os']}")
                
                script_lines.append(" \\\n  ".join(cmd_parts))
                script_lines.append("")
        
        script_lines.extend([
            "echo '✅ DockerVirt auto-start completed'",
            "logger 'DockerVirt auto-start completed'"
        ])
        
        return "\n".join(script_lines)
    
    def _copy_app_configs(self, mount_point, config):
        """Copy application configurations to image."""
        config_dir = mount_point / "home/dockvirt"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create .dockvirt files for each app
        if 'apps' in config:
            for app_name, app_config in config['apps'].items():
                dockvirt_file = config_dir / f".dockvirt-{app_name}"
                
                dockvirt_content = []
                for key, value in app_config.items():
                    dockvirt_content.append(f"{key}={value}")
                
                with open(dockvirt_file, 'w') as f:
                    f.write("\n".join(dockvirt_content))
    
    def _create_preseed_config(self, iso_dir, config):
        """Create preseed configuration for automated Ubuntu installation."""
        preseed_content = """
# Automated installation preseed for DockerVirt
d-i debian-installer/locale string en_US
d-i keyboard-configuration/xkb-keymap select us

# Network configuration
d-i netcfg/choose_interface select auto

# Mirror settings
d-i mirror/country string manual
d-i mirror/http/hostname string archive.ubuntu.com
d-i mirror/http/directory string /ubuntu

# Account setup
d-i passwd/user-fullname string DockerVirt User
d-i passwd/username string dockvirt
d-i passwd/user-password password dockvirt
d-i passwd/user-password-again password dockvirt
d-i user-setup/allow-password-weak boolean true

# Partitioning
d-i partman-auto/method string regular
d-i partman-auto/choose_recipe select atomic
d-i partman/confirm_write_new_label boolean true
d-i partman/choose_partition select finish
d-i partman/confirm boolean true
d-i partman/confirm_nooverwrite boolean true

# Package selection
tasksel tasksel/first multiselect ubuntu-server
d-i pkgsel/include string openssh-server python3 python3-pip curl wget

# Boot loader
d-i grub-installer/only_debian boolean true

# Late command - install dockvirt
d-i preseed/late_command string \\
    in-target curl -fsSL https://get.docker.com | sh; \\
    in-target pip3 install dockvirt; \\
    in-target systemctl enable docker
"""
        
        preseed_file = iso_dir / "preseed" / "dockvirt.seed"
        preseed_file.parent.mkdir(exist_ok=True)
        
        with open(preseed_file, 'w') as f:
            f.write(preseed_content)
    
    def _add_dockvirt_installer(self, iso_dir, config):
        """Add dockvirt installer and configuration to ISO."""
        installer_dir = iso_dir / "dockvirt-installer"
        installer_dir.mkdir(exist_ok=True)
        
        # Copy configuration
        config_file = installer_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # Create post-install script
        post_install = installer_dir / "post-install.sh"
        with open(post_install, 'w') as f:
            f.write(self._generate_autostart_script(config))
    
    def _customize_initrd(self, iso_dir, config):
        """Customize initrd with dockvirt configurations."""
        # This would involve extracting, modifying, and repacking initrd
        # Implementation depends on specific requirements
        pass
    
    def _resize_image(self, image_path, new_size):
        """Resize image file to specified size."""
        subprocess.run([
            'qemu-img', 'resize', str(image_path), new_size
        ], check=True)
    
    def _unmount_image(self, mount_point):
        """Unmount image filesystem."""
        subprocess.run(['sudo', 'umount', '-R', str(mount_point)], check=False)
    
    def _detach_loop_device(self, loop_device):
        """Detach loop device."""
        subprocess.run(['sudo', 'losetup', '-d', loop_device], check=False)


def generate_image_cli(image_type, size, output, config_file, apps, domains):
    """CLI interface for image generation."""
    generator = ImageGenerator()
    
    # Parse configuration
    config = {}
    
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    
    # Add apps from CLI parameters
    if apps and domains:
        app_list = apps.split(',')
        domain_list = domains.split(',')
        
        if len(app_list) != len(domain_list):
            raise ValueError("Number of apps must match number of domains")
        
        config['apps'] = {}
        for app, domain in zip(app_list, domain_list):
            config['apps'][app.split(':')[0]] = {
                'image': app,
                'domain': domain,
                'port': 80
            }
    
    # Generate image
    return generator.generate_image(image_type, size, output, config)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python image_generator.py <type> <size> <output> [config.yaml]")
        print("Types: raspberry-pi, pc-iso, usb-stick")
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
