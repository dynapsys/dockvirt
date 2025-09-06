import click
import sys
import logging
import time
from .vm_manager import create_vm, destroy_vm, get_vm_ip
from .config import load_config, load_project_config
from .system_check import check_system_dependencies, auto_install_dependencies
from .image_generator import generate_bootable_image
from .self_heal import (
    run_heal,
    preflight_network,
    unify_images_mapping,
    on_exception_hints,
    ensure_cli_log_file,
)
from .logdb import append_event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_cli_logging() -> None:
    """Ensure CLI logs are also written to ~/.dockvirt/cli.log."""
    try:
        log_file = ensure_cli_log_file()
        has_file = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        if not has_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(fh)
    except Exception:
        pass


@click.group()
def main():
    """Run dynadock apps in isolated libvirt/KVM VMs."""
    setup_cli_logging()


@main.command()
@click.option("--name", default=None, help="Name of the VM (e.g., project1)")
@click.option(
    "--domain", default=None, help="Application domain (e.g., app.local)"
)
@click.option('--image', default=None, help='Docker image name to run in the VM')
@click.option('--port', type=int, default=None, help='Port to expose from the VM')
@click.option('--os', 'os_name', default=None, help='OS variant (e.g., ubuntu22.04, fedora38)')
@click.option("--mem", default="4096", help="RAM for the VM (MB)")
@click.option("--disk", default="20", help="Disk size for the VM (GB)")
@click.option("--cpus", default=2, help="Number of vCPUs")
@click.option(
    "--net",
    "net",
    default=None,
    help=(
        "virt-install network spec, e.g. 'network=default' (NAT) or 'bridge=br0' (LAN). "
        "Defaults to project .dockvirt 'net' or 'network=default'."
    ),
)
@click.option(
    "--https",
    is_flag=True,
    default=False,
    help="Enable HTTPS with SSL certificates. Requires full domain name (e.g., app.dockvirt.dev)"
)
def up(name, domain, image, port, os_name, mem, disk, cpus, net, https):
    """Creates a VM in libvirt with dynadock + Caddy."""
    logger.info(f"Starting VM creation with parameters: name={name}, domain={domain}, image={image}, port={port}")
    config = load_config()
    project_config = load_project_config()
    # Use values from the local .dockvirt file as defaults
    name = name or project_config.get("name")
    domain = domain or project_config.get("domain")
    image = image or project_config.get("image")
    if port is None:
        port = int(project_config.get("port", 80))
    os_name = os_name or project_config.get("os") or config["default_os"]
    net = net or project_config.get("net") or "network=default"

    # Check if required parameters are available after applying defaults
    if not name:
        click.echo("❌ Error: Missing VM name. "
                   "Provide --name or create a .dockvirt file with name=...")
        return
    if not domain:
        click.echo("❌ Error: Missing domain. "
                   "Provide --domain or create a .dockvirt file with domain=...")
        return
    if not image:
        click.echo("❌ Error: Missing Docker image. "
                   "Provide --image or create a .dockvirt file with image=...")
        return

    # Self-heal: unify images mapping to avoid Unknown OS issues
    try:
        res = unify_images_mapping(config)
        if res.changed:
            logger.info("Self-heal: %s", "; ".join(res.notes))
    except Exception:
        pass

    # Self-heal: ensure default libvirt network is active
    try:
        net_res = preflight_network()
        for note in net_res.notes:
            logger.info("Network check: %s", note)
    except Exception:
        pass

    append_event("vm.up.start", {
        "name": name, "domain": domain, "image": image, "port": port,
        "os": os_name,
    })
    try:
        create_vm(name, domain, image, port, mem, disk, cpus, os_name, config, net, https)
        # Wait for IP assignment (dhcp leases)
        ip = ""
        for _ in range(60):  # up to ~120s
            time.sleep(2)
            ip = get_vm_ip(name)
            if ip and ip != "unknown":
                break
        append_event("vm.up.success", {"name": name, "ip": ip or "unknown", "domain": domain})
        if ip and ip != "unknown":
            protocol = "https" if https else "http"
            click.echo(f"✅ VM {name} is running at {protocol}://{domain} ({ip})")
            if https:
                click.echo(f"🔐 HTTPS enabled with self-signed certificates")
                click.echo(f"📋 Trust CA certificate: ~/.dockvirt/certs/ca/ca-cert.pem")
            click.echo(f"To destroy this VM, run: dockvirt down --name {name}")
        else:
            click.echo(f"⚠️ VM {name} created but IP not found. Check with: dockvirt ip {name}")
            click.echo(f"To destroy this VM, run: dockvirt down --name {name}")
    except Exception as e:
        click.echo(f"❌ VM creation failed: {e}")
        # Provide hints
        hints = on_exception_hints(str(e), name).notes
        for h in hints:
            click.echo(f"💡 {h}")
        append_event("vm.up.error", {"name": name, "error": str(e), "hints": hints})
        sys.exit(1)


@main.command()
@click.option("--name", required=True, help="Name of the VM to destroy")
def down(name):
    """Destroys a VM in libvirt."""
    destroy_vm(name)
    click.echo(f"🗑️ VM {name} has been destroyed.")


@main.command(name="check")
def check_system():
    """Checks system dependencies and readiness to run dockvirt."""
    success = check_system_dependencies()
    if not success:
        click.echo(
            "\n💡 Tip: Use 'dockvirt setup --install' for auto-installation"
        )
        sys.exit(1)


@main.command(name="setup")
@click.option(
    "--install", is_flag=True, help="Install missing dependencies."
)
def setup_system(install):
    """Configures the system for dockvirt."""
    if install:
        success = auto_install_dependencies()
        if success:
            click.echo("\n✅ Configuration completed successfully!")
        else:
            click.echo("\n❌ Problems occurred during installation")
            sys.exit(1)
    else:
        check_system_dependencies()


@main.command(name="heal")
@click.option("--apply", is_flag=True, help="Attempt non-destructive auto-remediation (may print sudo steps)")
@click.option("--auto-hosts", is_flag=True, help="Allow adding /etc/hosts entries (requires sudo)")
def heal_command(apply: bool, auto_hosts: bool):
    """Runs self-healing routines (default network, images map, guidance)."""
    setup_cli_logging()
    notes = run_heal(apply=apply, auto_hosts=auto_hosts)
    # Also unify images mapping proactively
    try:
        config = load_config()
        res = unify_images_mapping(config)
        if res.changed:
            notes.extend(["images:"] + res.notes)
    except Exception:
        pass
    append_event("heal.run", {"apply": apply, "auto_hosts": auto_hosts, "notes": notes})
    click.echo("\n".join(["🔧 Heal summary:"] + [f" - {n}" for n in notes]))


@main.command(name="ip")
@click.option("--name", required=True, help="Name of the VM")
def show_ip(name):
    """Shows the IP address of a VM."""
    ip = get_vm_ip(name)
    if ip != "unknown":
        click.echo(f"🌐 IP for VM {name}: {ip}")
    else:
        click.echo(f"❌ Could not find IP for VM {name}")
        sys.exit(1)


@main.command(name="generate-image")
@click.option(
    "--type",
    "image_type",
    type=click.Choice(
        ["raspberry-pi", "pc-iso", "deb-package", "rpm-package"]
    ),
    required=True,
    help="Type of image to generate.",
)
@click.option("--size", default="8GB", help="Image size (e.g., 8GB)")
@click.option("--output", required=True, help="Output filename")
@click.option("--apps", help="List of Docker applications (comma-separated)")
@click.option("--domains", help="List of domains (comma-separated)")
@click.option("--config", help="YAML configuration file")
def generate_image(image_type, size, output, apps, domains, config):
    """Generates bootable images, deb/rpm packages from Docker apps."""
    try:
        generate_bootable_image(
            image_type=image_type,
            size=size,
            output_path=output,
            apps=apps.split(',') if apps else [],
            domains=domains.split(',') if domains else [],
            config_file=config
        )
        click.echo(f"✅ Image {output} generated successfully!")
    except Exception as e:
        click.echo(f"❌ Error generating image: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
