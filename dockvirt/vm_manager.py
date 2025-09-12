import subprocess
import logging
import json
import re
from pathlib import Path
from jinja2 import Template
import yaml
import os

from .image_manager import get_image_path

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

BASE_DIR = Path.home() / ".dockvirt"


def run(command):
    """Execute a shell command."""
    logger.debug(f"Executing command: {command}")
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True
    )
    logger.debug(f"Command exit code: {result.returncode}")
    if result.stdout:
        logger.debug(f"Command stdout: {result.stdout}")
    if result.stderr:
        logger.debug(f"Command stderr: {result.stderr}")
    
    if result.returncode != 0:
        # Check for common missing dependencies and provide a generic helpful message
        if "command not found" in result.stderr:
            tool = result.stderr.split(":")[0].strip()
            raise RuntimeError(
                f"Missing dependency: '{tool}' command not found.\n"
                f"Please run 'dockvirt doctor' or 'dockvirt setup --install' to diagnose and fix dependency issues."
            )
        elif "Permission denied" in result.stderr and (".dockvirt" in result.stderr or "cidata.iso" in result.stderr or ".qcow2" in result.stderr):
            raise RuntimeError(
                "Permission denied writing VM files under ~/.dockvirt.\n"
                "When using system libvirt (qemu:///system), apply ACLs and SELinux labels so the 'qemu' user can access your home.\n\n"
                "Run 'dockvirt doctor' for detailed instructions."
            )
        elif "network 'default' is not active" in result.stderr.lower():
            raise RuntimeError(
                "Default libvirt network is inactive.\n"
                "Run: sudo virsh net-start default && sudo virsh net-autostart default\n"
                "Or run 'dockvirt heal' for more diagnostics."
            )
        raise RuntimeError(f"Command failed: {result.stderr}")
    return result.stdout.strip()


def create_vm(name, domain, image, port, mem, disk, cpus, os_name, config, net=None, https=False, ssh_keys=None):
    logger.info(f"Creating VM: name={name}, domain={domain}, image={image}, port={port}, mem={mem}, disk={disk}, cpus={cpus}, os={os_name}")
    
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    vm_dir = BASE_DIR / name
    vm_dir.mkdir(exist_ok=True)
    logger.debug(f"VM directory created: {vm_dir}")
    
    templates_dir = Path(__file__).parent / "templates"
    logger.debug(f"Using templates from: {templates_dir}")

    # Select templates based on HTTPS mode
    if https:
        logger.debug("Using HTTPS templates")
        caddyfile_template_path = templates_dir / "Caddyfile-https.json.j2"
        docker_compose_template_path = templates_dir / "docker-compose-https.yml.j2"
        caddyfile_filename = "Caddyfile-https.json"
    else:
        logger.debug("Using HTTP templates")
        caddyfile_template_path = templates_dir / "Caddyfile.j2"
        docker_compose_template_path = templates_dir / "docker-compose.yml.j2"
        caddyfile_filename = "Caddyfile"

    # Render Caddyfile/Caddy JSON
    logger.debug(f"Rendering {caddyfile_filename} template")
    caddyfile_template = caddyfile_template_path.read_text()
    
    if https:
        # For HTTPS, use the JSON config as-is (already configured for all domains)
        caddyfile_content = caddyfile_template
    else:
        # For HTTP, render the traditional Caddyfile
        caddyfile_content = Template(caddyfile_template).render(
            domain=domain, app_name=name, app_port=port
        )
    logger.debug(f"Caddyfile rendered for domain {domain}, port {port}")

    # Render docker-compose.yml
    logger.debug("Rendering docker-compose.yml template")
    docker_compose_template = docker_compose_template_path.read_text()

    docker_compose_content = Template(docker_compose_template).render(
        app_name=name,
        app_image=image,
        home_dir=str(Path.home())
    )
    logger.debug(f"Docker compose rendered for app {name} with image {image}")

    # Check if we're in a project directory with a Dockerfile and app files
    current_dir = Path.cwd()
    logger.debug(f"Scanning current directory for app files: {current_dir}")
    dockerfile_content = None
    app_files = {}

    # Look for Dockerfile in the current directory
    dockerfile_path = current_dir / "Dockerfile"
    if dockerfile_path.exists():
        logger.info(f"Found Dockerfile: {dockerfile_path}")
        dockerfile_content = dockerfile_path.read_text()
    else:
        logger.debug("No Dockerfile found in current directory")

        # Look for common app files to copy
        common_files = [
            "index.html", "index.php", "app.py", "server.js", "main.py",
            "requirements.txt", "package.json", "composer.json",
            "nginx.conf", "apache.conf", "default.conf"
        ]

        for filename in common_files:
            file_path = current_dir / filename
            if file_path.exists():
                logger.debug(f"Found app file: {filename}")
                app_files[filename] = file_path.read_text()

        # Look for common directories to copy
        for dir_name in ["static", "templates", "public", "www", "html"]:
            dir_path = current_dir / dir_name
            if dir_path.exists():
                logger.debug(f"Found app directory: {dir_name}")
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(current_dir)
                        app_files[str(relative_path)] = file_path.read_text()
        
        logger.info(f"Collected {len(app_files)} app files for VM")

    # Get the operating system image
    logger.debug(f"Getting base image for OS: {os_name}")
    base_image = get_image_path(os_name, config)

    # Support both "images" and "os_images" config keys
    images_key = "os_images" if "os_images" in config else "images"
    os_variant = config[images_key][os_name]["variant"]

    logger.info(
        f"Using base image: {base_image} (variant: {os_variant})"
    )

    # Render cloud-init config (user-data)
    logger.debug("Rendering cloud-init template")
    cloudinit_template = (templates_dir / "cloud-init.yaml.j2").read_text()
    os_family = "fedora" if "fedora" in os_name else "debian"
    remote_user = "fedora" if "fedora" in os_name else "ubuntu"
    logger.debug(f"OS family: {os_family}, remote user: {remote_user}")
    
    cloudinit_rendered = Template(cloudinit_template).render(
        docker_compose_content=docker_compose_content,
        caddyfile_content=caddyfile_content,
        dockerfile_content=dockerfile_content,
        app_files=app_files,
        app_image=image,
        os_family=os_family,
        remote_user=remote_user
    )
    
    # Create cloud-init ISO with user-data and meta-data
    iso_path = create_cloud_init_iso(name, domain, port, app_files, ssh_keys)
    logger.debug("Cloud-init user-data and meta-data written")

    # Create VM disk from base image
    disk_img = vm_dir / f"{name}.qcow2"
    logger.info(
        f"Creating VM disk: {disk_img} ({disk}GB)"
    )

    # Detect backing file format to avoid: "Backing file specified without backing format"
    base_format = "qcow2"
    try:
        info_cmd = "qemu-img info --output=json \"%s\"" % base_image
        info_json = run(info_cmd)
        base_format = json.loads(info_json).get("format", "qcow2")
        logger.debug("Detected base image format: %s", base_format)
    except Exception as e:
        logger.warning(
            "Could not detect base image format, defaulting to qcow2: %s",
            e,
        )

    # Create overlay disk referencing the base image
    create_cmd = (
        "qemu-img create -f qcow2 -F %s -b \"%s\" \"%s\" %sG"
        % (base_format, base_image, disk_img, disk)
    )
    run(create_cmd)

    # Create VM using virt-install
    net_spec = net or "network=default"
    virt_cmd = (
        f"virt-install --connect qemu:///system "
        f"--name {name} --ram {mem} --vcpus {cpus} "
        f"--disk path={disk_img},format=qcow2 "
        f"--disk path={iso_path},device=cdrom "
        f"--os-variant {os_variant} "
        f"--import --network {net_spec} --noautoconsole --graphics none "
        f"--channel type=unix,target.type=virtio,target.name=org.qemu.guest_agent.0"
    )
    logger.info(f"Creating VM with virt-install: {name}")
    logger.debug(f"virt-install command: {virt_cmd}")
    run(virt_cmd)
    logger.info(f"VM {name} created successfully")


def create_cloud_init_iso(name, domain, port, app_files=None, ssh_keys=None):
    """Create a cloud-init ISO with user-data and meta-data."""
    iso_dir = os.path.join(get_vm_dir(name), 'cloud-init')
    os.makedirs(iso_dir, exist_ok=True)
    
    # Default user data with improved SSH settings
    user_data = {
        'users': [
            'default',
            {
                'name': 'ubuntu',
                'sudo': 'ALL=(ALL) NOPASSWD:ALL',
                'ssh_authorized_keys': ssh_keys or [],
                'lock_passwd': False,
                'passwd': "$6$rounds=4096$wQ5DpBu0mDTTGlRr$WjB6tkmJKlYpF3rJ6fX1vJYwv8iJkLmH1vXkLmNpOqRrStUvWxYzA",  # hasło: ubuntu
                'shell': '/bin/bash',
                'groups': ['sudo', 'docker']
            }
        ],
        'ssh_pwauth': True,
        'chpasswd': {
            'list': [
                'ubuntu:ubuntu'  # Ustaw hasło dla użytkownika ubuntu
            ],
            'expire': False
        },
        'ssh_authorized_keys': ssh_keys or [],
        'ssh_genkeytypes': ['rsa', 'ed25519'],
        'ssh_keys': {
            'rsa_private': '',
            'rsa_public': '',
            'ed25519_private': '',
            'ed25519_public': ''
        },
        'package_update': True,
        'package_upgrade': True,
        'packages': [
            'qemu-guest-agent',
            'openssh-server',
            'sudo',
            'haveged',  # For better entropy
            'cloud-initramfs-growroot',  # For root filesystem resizing
            'bash-completion',
            'curl',
            'wget'
        ],
        'runcmd': [
            'systemctl enable --now qemu-guest-agent',
            'systemctl enable --now ssh',
            'systemctl restart ssh',
            'sed -i "s/^#*PasswordAuthentication.*/PasswordAuthentication yes/g" /etc/ssh/sshd_config',
            'sed -i "s/^#*PermitRootLogin.*/PermitRootLogin no/g" /etc/ssh/sshd_config',
            'systemctl restart sshd',
            'cloud-init clean',
            'cloud-init init',
            'cloud-init modules --mode=config',
            'cloud-init modules --mode=final'
        ],
        'power_state': {
            'mode': 'reboot',
            'message': 'Rebooting after cloud-init configuration',
            'timeout': 30,
            'condition': True
        }
    }

    # Add port forwarding if specified
    if port:
        user_data['runcmd'].extend([
            'apt-get update',
            'apt-get install -y nginx',
            f'echo "server {{ listen 80; location / {{ proxy_pass http://localhost:{port}; }} }}" > /etc/nginx/sites-available/default',
            'systemctl restart nginx'
        ])

    meta_data = {
        'instance-id': f"iid-{name}",
        'local-hostname': domain
    }

    # Write config files
    with open(os.path.join(iso_dir, 'user-data'), 'w') as f:
        f.write('#cloud-config\n' + yaml.dump(user_data))
    
    with open(os.path.join(iso_dir, 'meta-data'), 'w') as f:
        f.write(yaml.dump(meta_data))

    # Create ISO image
    iso_path = os.path.join(get_vm_dir(name), 'cidata.iso')
    run(f"genisoimage -output {iso_path} -volid cidata -joliet -rock {iso_dir}/user-data {iso_dir}/meta-data")
    
    return iso_path


def destroy_vm(name):
    logger.info(f"Destroying VM: {name}")
    run(f"virsh --connect qemu:///system destroy {name} || true")
    run(f"virsh --connect qemu:///system undefine {name} --remove-all-storage || true")
    logger.info(f"VM {name} destroyed successfully")


def get_vm_ip(name):
    """Get the IP address of a running VM."""
    # Requires libvirt + dnsmasq to be installed
    # Prefer system libvirt (qemu:///system)
    
    # 0) Try direct DHCP lease lookup (most reliable method)
    try:
        out = run(
            "virsh --connect qemu:///system net-dhcp-leases default"
        )
        for line in out.splitlines():
            if name in line:
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})/\d+", line)
                if m:
                    return m.group(1)
    except Exception:
        pass
    
    # 1) Try domifaddr from DHCP lease source
    try:
        out = run(
            f"virsh --connect qemu:///system domifaddr {name} --source lease --full"
        )
        for line in out.splitlines():
            m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})/\d+", line)
            if m:
                return m.group(1)
    except Exception:
        pass

    # 1b) Try qemu-guest-agent if available (works with bridged networking)
    try:
        out = run(
            f"virsh --connect qemu:///system domifaddr {name} --source agent --full"
        )
        for line in out.splitlines():
            m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})/\d+", line)
            if m:
                return m.group(1)
    except Exception:
        pass

    # 2) Fallback: get MAC from domain XML, then search net-dhcp-leases
    try:
        xml = run(f"virsh --connect qemu:///system dumpxml {name}")
        mac_match = re.search(r"<mac address='([0-9A-Fa-f:]+)'", xml)
        if mac_match:
            mac = mac_match.group(1).lower()
            leases = run(
                "virsh --connect qemu:///system net-dhcp-leases default"
            )
            for line in leases.splitlines():
                if mac in line.lower():
                    m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})/\d+", line)
                    if m:
                        return m.group(1)
    except Exception:
        pass

    return "unknown"


def get_vm_dir(name):
    return os.path.join(str(BASE_DIR), name)
