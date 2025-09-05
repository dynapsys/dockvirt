import click
from .vm_manager import create_vm, destroy_vm, get_vm_ip


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
    "--os-variant",
    default="ubuntu22.04",
    help="Wariant OS dla virt-install (np. fedora-cloud-base).",

)
@click.option(
    "--base-image",
    required=True,
    help="Ścieżka do bazowego obrazu chmurowego (qcow2).",
)
def up(name, domain, image, port, mem, disk, cpus, os_variant, base_image):
    """Tworzy VM w libvirt z dynadock + Caddy."""
    create_vm(
        name, domain, image, port, mem, disk, cpus, os_variant, base_image
    )
    ip = get_vm_ip(name)
    click.echo(f"✅ VM {name} działa pod http://{domain} ({ip})")


@main.command()
@click.option("--name", required=True, help="Nazwa VM do usunięcia")
def down(name):
    """Usuwa VM w libvirt."""
    destroy_vm(name)
    click.echo(f"🗑️ VM {name} została usunięta.")
