import os
import subprocess
from urllib.parse import urlparse

from .config import IMAGES_DIR


def download_image(url, filename):
    """Pobiera obraz z podanego URL i zapisuje go w katalogu obrazów."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    image_path = IMAGES_DIR / filename

    if image_path.exists():
        print(f"Obraz {filename} już istnieje, pomijam pobieranie.")
        return str(image_path)

    print(f"Pobieranie obrazu z {url}...")
    try:
        subprocess.run(
            ["wget", "-O", str(image_path), url],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ Obraz {filename} został pobrany.")
        return str(image_path)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Błąd podczas pobierania obrazu: {e.stderr}")


def get_image_path(os_name, config):
    """Zwraca ścieżkę do obrazu OS, pobierając go jeśli nie istnieje."""
    if os_name not in config["images"]:
        raise ValueError(f"Nieznany system operacyjny: {os_name}")

    image_config = config["images"][os_name]
    url = image_config["url"]

    # Wyodrębnij nazwę pliku z URL
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    if not filename.endswith(('.qcow2', '.img')):
        filename += '.qcow2'

    return download_image(url, filename)
