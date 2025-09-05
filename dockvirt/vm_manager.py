import subprocess
import logging
from pathlib import Path
from jinja2 import Template

from .image_manager import get_image_path

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

BASE_DIR = Path.home() / ".dockvirt"


def run(cmd):
    logger.info(f"Executing command: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Command failed with exit code {result.returncode}: {result.stderr}")
        raise RuntimeError(f"Error: {result.stderr}")
    logger.debug(f"Command output: {result.stdout.strip()}")
    return result.stdout.strip()


def create_vm(name, domain, image, port, mem, disk, cpus, os_name, config):
    logger.info(f"Creating VM: name={name}, domain={domain}, image={image}, port={port}, mem={mem}, disk={disk}, cpus={cpus}, os={os_name}")
    
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    vm_dir = BASE_DIR / name
    vm_dir.mkdir(exist_ok=True)
    logger.debug(f"VM directory created: {vm_dir}")
    
    templates_dir = Path(__file__).parent / "templates"
    logger.debug(f"Using templates from: {templates_dir}")

    # Render Caddyfile
    logger.debug("Rendering Caddyfile template")
    caddyfile_template = (templates_dir / "Caddyfile.j2").read_text()
    caddyfile_content = Template(caddyfile_template).render(
        domain=domain, app_name=name, app_port=port
    )
    logger.debug(f"Caddyfile rendered for domain {domain}, port {port}")

    # Render docker-compose.yml
    logger.debug("Rendering docker-compose.yml template")
    docker_compose_template_path = templates_dir / "docker-compose.yml.j2"
    docker_compose_template = docker_compose_template_path.read_text()

    docker_compose_content = Template(docker_compose_template).render(
        app_name=name, app_image=image
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
    os_variant = config["images"][os_name]["variant"]
    logger.info(f"Using base image: {base_image} (variant: {os_variant})")

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
    logger.info(f"Creating VM disk: {disk_img} ({disk}GB)")
    run(f"qemu-img create -f qcow2 -b {base_image} {disk_img} {disk}G")

    # Create VM using virt-install
    virt_cmd = (
        f"virt-install --name {name} --ram {mem} --vcpus {cpus} "
        f"--disk path={disk_img},format=qcow2 "
        f"--disk path={cidata},device=cdrom "
        f"--os-type linux --os-variant {os_variant} "
        f"--import --network network=default --noautoconsole --graphics none"
    )
    logger.info(f"Creating VM with virt-install: {name}")
    logger.debug(f"virt-install command: {virt_cmd}")
    run(virt_cmd)
    logger.info(f"VM {name} created successfully")


def destroy_vm(name):
    run(f"virsh destroy {name} || true")
    run(f"virsh undefine {name} --remove-all-storage")


def get_vm_ip(name):
    """Get the IP address of a running VM."""
    # Requires libvirt + dnsmasq to be installed
    try:
        leases = run("virsh net-dhcp-leases default")
        for line in leases.splitlines():
            if name in line:
                return line.split()[4].split("/")[0]
        return "unknown"
    except Exception:
        return "unknown"
