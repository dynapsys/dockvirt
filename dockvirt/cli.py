import click
from .vm_manager import create_vm, destroy_vm, get_vm_ip
from .config import load_config, load_project_config


@click.group()
def main():
    """dockvirt-libvirt - uruchamianie dynadock w izolowanych VM libvirt."""


@main.command()
@click.option("--name", help="Nazwa VM (np. project1)")
@click.option(
    "--domain", help="Domena aplikacji (np. app.local)"
)
@click.option('--image', help='Docker image name to run in VM')
@click.option('--port', type=int, help='Port to expose from VM')
@click.option('--os', help='OS variant to use (ubuntu22.04, fedora36)')
@click.option("--mem", default="4096", help="RAM dla VM (MB)")
@click.option("--disk", default="20", help="Dysk dla VM (GB)")
@click.option("--cpus", default=2, help="Liczba vCPU")
def up(name, domain, image, port, mem, disk, cpus, os):
    """Tworzy VM w libvirt z dynadock + Caddy."""
    config = load_config()
    project_config = load_project_config()
    # Użyj wartości z lokalnego pliku .dockvirt jako domyślnych
    if not name and "name" in project_config:
        name = project_config["name"]
    if not domain and "domain" in project_config:
        domain = project_config["domain"]
    if not image and "image" in project_config:
        image = project_config["image"]
    if port == 8000 and "port" in project_config:
        port = int(project_config["port"])
    if not os and "os" in project_config:
        os = project_config["os"]
    if not os:
        os = config["default_os"]

    # Sprawdź czy wymagane parametry są dostępne
    if not name:
        click.echo("❌ Błąd: Brak nazwy VM. Podaj --name lub utwórz plik .dockvirt")
        return
    if not domain:
        click.echo("❌ Błąd: Brak domeny. Podaj --domain lub utwórz plik .dockvirt")
        return
    if not image:
        click.echo("❌ Błąd: Brak obrazu Docker. Podaj --image lub utwórz plik .dockvirt")
        return

    create_vm(name, domain, image, port, mem, disk, cpus, os, config)
    ip = get_vm_ip(name)
    click.echo(f"✅ VM {name} działa pod http://{domain} ({ip})")


@main.command()
@click.option("--name", required=True, help="Nazwa VM do usunięcia")
def down(name):
    """Usuwa VM w libvirt."""
    destroy_vm(name)
    click.echo(f"🗑️ VM {name} została usunięta.")
