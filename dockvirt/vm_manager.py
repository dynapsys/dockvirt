import subprocess
from pathlib import Path
from jinja2 import Template

from .image_manager import get_image_path

BASE_DIR = Path.home() / ".dockvirt"


def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Błąd: {result.stderr}")
    return result.stdout.strip()


def create_vm(name, domain, image, port, mem, disk, cpus, os_name, config):
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    vm_dir = BASE_DIR / name
    vm_dir.mkdir(exist_ok=True)
    templates_dir = Path(__file__).parent / "templates"

    # Render Caddyfile
    caddyfile_template = (templates_dir / "Caddyfile.j2").read_text()
    caddyfile_content = Template(caddyfile_template).render(
        domain=domain, app_name=name, app_port=port
    )

    # Render docker-compose.yml
    docker_compose_template_path = templates_dir / "docker-compose.yml.j2"
    docker_compose_template = docker_compose_template_path.read_text()

    docker_compose_content = Template(docker_compose_template).render(
        app_name=name, app_image=image
    )

    # Pobierz obraz systemu operacyjnego
    base_image = get_image_path(os_name, config)
    os_variant = config["images"][os_name]["variant"]
    
    # Render cloud-init config (user-data)
    cloudinit_template = (templates_dir / "cloud-init.yaml.j2").read_text()
    cloudinit_rendered = Template(cloudinit_template).render(
        docker_compose_content=docker_compose_content,
        caddyfile_content=caddyfile_content,
        os_family="fedora" if "fedora" in os_name else "debian",
        remote_user="fedora" if "fedora" in os_name else "ubuntu"
    )
    (vm_dir / "user-data").write_text(cloudinit_rendered)
    metadata_content = f"instance-id: {name}\nlocal-hostname: {name}\n"
    (vm_dir / "meta-data").write_text(metadata_content)

    # Create cloud-init ISO
    cidata = vm_dir / "cidata.iso"
    run(f"cloud-localds {cidata} {vm_dir}/user-data {vm_dir}/meta-data")

    # Create VM disk from base image
    disk_img = vm_dir / f"{name}.qcow2"
    run(f"qemu-img create -f qcow2 -b {base_image} {disk_img} {disk}G")

    # Create VM using virt-install
    run(
        f"virt-install --name {name} --ram {mem} --vcpus {cpus} "
        f"--disk path={disk_img},format=qcow2 "
        f"--disk path={cidata},device=cdrom "
        f"--os-type linux --os-variant {os_variant} "
        f"--import --network network=default --noautoconsole --graphics none"
    )


def destroy_vm(name):
    run(f"virsh destroy {name} || true")
    run(f"virsh undefine {name} --remove-all-storage")


def get_vm_ip(name):
    # Wymaga zainstalowanego libvirt + dnsmasq
    leases = run("virsh net-dhcp-leases default")
    for line in leases.splitlines():
        if name in line:
            return line.split()[4].split("/")[0]
    return "unknown"
