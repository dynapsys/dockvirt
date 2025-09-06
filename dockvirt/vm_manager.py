import subprocess
import logging
import json
import re
from pathlib import Path
from jinja2 import Template

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
        # Check for common missing dependencies and provide helpful messages
        if "cloud-localds: command not found" in result.stderr:
            raise RuntimeError(
                "Missing dependency: cloud-localds command not found.\n"
                "Install cloud-image-utils package:\n"
                "  Ubuntu/Debian: sudo apt install -y cloud-image-utils\n"
                "  Fedora/CentOS: sudo dnf install -y cloud-utils\n"
                "  Arch Linux: sudo pacman -S cloud-image-utils\n"
                "Then run: dockvirt check"
            )
        elif "virsh: command not found" in result.stderr:
            raise RuntimeError(
                "Missing dependency: virsh command not found.\n"
                "Install libvirt tools:\n"
                "  Ubuntu/Debian: sudo apt install -y qemu-kvm "
                "libvirt-daemon-system libvirt-clients\n"
                "  Fedora/CentOS: sudo dnf install -y qemu-kvm "
                "libvirt virt-install\n"
                "Then run: dockvirt check"
            )
        elif "qemu-img: command not found" in result.stderr:
            raise RuntimeError(
                "Missing dependency: qemu-img command not found.\n"
                "Install QEMU tools:\n"
                "  Ubuntu/Debian: sudo apt install -y qemu-utils\n"
                "  Fedora/CentOS: sudo dnf install -y qemu-img\n"
                "Then run: dockvirt check"
            )
        elif "Permission denied" in result.stderr and (".dockvirt" in result.stderr or "cidata.iso" in result.stderr or ".qcow2" in result.stderr):
            raise RuntimeError(
                "Permission denied writing VM files under ~/.dockvirt.\n"
                "When using system libvirt (qemu:///system), apply ACLs and SELinux labels so the 'qemu' user can access your home.\n\n"
                "Run the following commands (safe to apply):\n"
                "  sudo setfacl -m u:qemu:x \"$HOME\"\n"
                "  sudo setfacl -R -m u:qemu:rx \"$HOME/.dockvirt\"\n"
                "  sudo find \"$HOME/.dockvirt\" -type f -name '*.qcow2' -exec setfacl -m u:qemu:rw {} +\n"
                "  sudo find \"$HOME/.dockvirt\" -type f -name '*.iso' -exec setfacl -m u:qemu:r {} +\n\n"
                "If SELinux is enabled (Fedora/RHEL):\n"
                "  sudo semanage fcontext -a -t svirt_image_t \"$HOME/.dockvirt(/.*)?\\.qcow2\"\n"
                "  sudo semanage fcontext -a -t svirt_image_t \"$HOME/.dockvirt(/.*)?\\.iso\"\n"
                "  sudo restorecon -Rv \"$HOME/.dockvirt\"\n"
            )
        else:
            if "network 'default' is not active" in result.stderr.lower():
                raise RuntimeError(
                    "Default libvirt network is inactive.\n"
                    "Run: sudo virsh net-define /usr/share/libvirt/networks/default.xml && "
                    "sudo virsh net-start default && sudo virsh net-autostart default\n"
                    "Then retry: dockvirt heal; dockvirt up"
                )
            raise RuntimeError(f"Command failed: {result.stderr}")
    return result.stdout.strip()


def create_vm(name, domain, image, port, mem, disk, cpus, os_name, config, net=None, https=False):
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
        image_name=name, 
        ports=[port] if not https else [],
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
    (vm_dir / "user-data").write_text(cloudinit_rendered)
    metadata_content = f"instance-id: {name}\nlocal-hostname: {name}\n"
    (vm_dir / "meta-data").write_text(metadata_content)
    logger.debug("Cloud-init user-data and meta-data written")

    # Create cloud-init ISO
    cidata = vm_dir / "cidata.iso"
    logger.info(f"Creating cloud-init ISO: {cidata}")
    run(f"cloud-localds {cidata} {vm_dir}/user-data {vm_dir}/meta-data")

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
        f"--disk path={cidata},device=cdrom "
        f"--os-variant {os_variant} "
        f"--import --network {net_spec} --noautoconsole --graphics none"
    )
    logger.info(f"Creating VM with virt-install: {name}")
    logger.debug(f"virt-install command: {virt_cmd}")
    run(virt_cmd)
    logger.info(f"VM {name} created successfully")


def destroy_vm(name):
    logger.info(f"Destroying VM: {name}")
    run(f"virsh destroy {name} || true")
    run(f"virsh undefine {name} --remove-all-storage || true")
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
