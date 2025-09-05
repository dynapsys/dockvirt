import click
import sys
from .vm_manager import create_vm, destroy_vm, get_vm_ip
from .config import load_config, load_project_config
from .system_check import check_system_dependencies, auto_install_dependencies
from .image_generator import generate_bootable_image


@click.group()
def main():
    """Run dynadock apps in isolated libvirt/KVM VMs."""


@main.command()
@click.option("--name", help="Name of the VM (e.g., project1)")
@click.option(
    "--domain", help="Application domain (e.g., app.local)"
)
@click.option('--image', help='Docker image name to run in the VM')
@click.option('--port', type=int, help='Port to expose from the VM')
@click.option('--os', 'os_name', help='OS variant (e.g., ubuntu22.04, fedora38)')
@click.option("--mem", default="4096", help="RAM for the VM (MB)")
@click.option("--disk", default="20", help="Disk size for the VM (GB)")
@click.option("--cpus", default=2, help="Number of vCPUs")
def up(name, domain, image, port, os_name, mem, disk, cpus):
    """Creates a VM in libvirt with dynadock + Caddy."""
    config = load_config()
    project_config = load_project_config()
    # Use values from the local .dockvirt file as defaults
    if not name and "name" in project_config:
        name = project_config["name"]
    if not domain and "domain" in project_config:
        domain = project_config["domain"]
    if not image and "image" in project_config:
        image = project_config["image"]
    # Fallback to project .dockvirt value when --port is not provided
    if port is None and "port" in project_config:
        port = int(project_config["port"])
    if not os_name and "os" in project_config:
        os_name = project_config["os"]
    if not os_name:
        os_name = config["default_os"]

    # Check if required parameters are available
    if not name:
        click.echo("❌ Error: Missing VM name. "
                   "Provide --name or create a .dockvirt file")
        return
    if not domain:
        click.echo("❌ Error: Missing domain. "
                   "Provide --domain or create a .dockvirt file")
        return
    if not image:
        click.echo("❌ Error: Missing Docker image. "
                   "Provide --image or create a .dockvirt file")
        return

    create_vm(name, domain, image, port, mem, disk, cpus, os_name, config)
    ip = get_vm_ip(name)
    click.echo(f"✅ VM {name} is running at http://{domain} ({ip})")


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
