import click
from .vm_manager import create_vm, destroy_vm, get_vm_ip
from .config import load_config


@click.group()
def main():
    """dockvirt-libvirt - uruchamianie dynadock w izolowanych VM libvirt."""


@main.command()
@click.option("--name", required=True, help="Nazwa VM (np. project1)")
@click.option(
    "--domain", required=True, help="Domena aplikacji (np. app.local)"
)
@click.option(
    "--image", required=True, help="Obraz Dockera aplikacji dynadock"
)
@click.option(
    "--port", default=8000, help="Port aplikacji wewnątrz kontenera"
)
@click.option("--mem", default="4096", help="RAM dla VM (MB)")
@click.option("--disk", default="20", help="Dysk dla VM (GB)")
@click.option("--cpus", default=2, help="Liczba vCPU")
@click.option(
    "--os", "os_name", 
    help="Nazwa systemu operacyjnego do użycia (np. ubuntu22.04)."
)
def up(name, domain, image, port, mem, disk, cpus, os_name):
    """Tworzy VM w libvirt z dynadock + Caddy."""
    config = load_config()
    if not os_name:
        os_name = config["default_os"]

    create_vm(name, domain, image, port, mem, disk, cpus, os_name, config)
    ip = get_vm_ip(name)
    click.echo(f"✅ VM {name} działa pod http://{domain} ({ip})")


@main.command()
@click.option("--name", required=True, help="Nazwa VM do usunięcia")
def down(name):
    """Usuwa VM w libvirt."""
    destroy_vm(name)
    click.echo(f"🗑️ VM {name} została usunięta.")
