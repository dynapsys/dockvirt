import click
import sys
from .vm_manager import create_vm, destroy_vm, get_vm_ip
from .config import load_config, load_project_config
from .system_check import check_system_dependencies, auto_install_dependencies
from .image_generator import generate_bootable_image


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
        click.echo("❌ Błąd: Brak nazwy VM. "
                   "Podaj --name lub utwórz plik .dockvirt")
        return
    if not domain:
        click.echo("❌ Błąd: Brak domeny. "
                   "Podaj --domain lub utwórz plik .dockvirt")
        return
    if not image:
        click.echo("❌ Błąd: Brak obrazu Docker. "
                   "Podaj --image lub utwórz plik .dockvirt")
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


@main.command(name="check")
def check_system():
    """Sprawdza zależności systemu i gotowość do uruchomienia dockvirt."""
    success = check_system_dependencies()
    if not success:
        click.echo("\n💡 Tip: Użyj 'dockvirt setup --install' "
                   "dla auto-instalacji")
        sys.exit(1)


@main.command(name="setup")
@click.option("--install", is_flag=True, help="Automatycznie instaluje brakujące zależności")
def setup_system(install):
    """Konfiguruje system dla dockvirt."""
    if install:
        success = auto_install_dependencies()
        if success:
            click.echo("\n✅ Konfiguracja zakończona pomyślnie!")
        else:
            click.echo("\n❌ Wystąpiły problemy podczas instalacji")
            sys.exit(1)
    else:
        check_system_dependencies()


@main.command(name="ip")
@click.option("--name", required=True, help="Nazwa VM")
def show_ip(name):
    """Pokazuje adres IP VM."""
    ip = get_vm_ip(name)
    if ip != "unknown":
        click.echo(f"🌐 IP VM {name}: {ip}")
    else:
        click.echo(f"❌ Nie można znaleźć IP dla VM {name}")
        sys.exit(1)


@main.command(name="generate-image")
@click.option("--type", "image_type", 
              type=click.Choice(['raspberry-pi', 'pc-iso', 'deb-package', 'rpm-package']),
              required=True, help="Typ obrazu do wygenerowania")
@click.option("--size", default="8GB", help="Rozmiar obrazu (np. 8GB)")
@click.option("--output", required=True, help="Nazwa pliku wyjściowego")
@click.option("--apps", help="Lista aplikacji Docker (oddzielone przecinkami)")
@click.option("--domains", help="Lista domen (oddzielone przecinkami)")
@click.option("--config", help="Plik konfiguracyjny YAML")
def generate_image(image_type, size, output, apps, domains, config):
    """Generuje bootable obrazy, paczki deb/rpm z aplikacji Docker."""
    try:
        generate_bootable_image(
            image_type=image_type,
            size=size,
            output_path=output,
            apps=apps.split(',') if apps else [],
            domains=domains.split(',') if domains else [],
            config_file=config
        )
        click.echo(f"✅ Obraz {output} został wygenerowany pomyślnie!")
    except Exception as e:
        click.echo(f"❌ Błąd podczas generowania obrazu: {e}")
        sys.exit(1)
