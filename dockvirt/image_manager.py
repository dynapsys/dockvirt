import os
import subprocess
from urllib.parse import urlparse

from .config import IMAGES_DIR


def download_image(url, filename):
    """Downloads an image from the given URL and saves it to the images directory."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    image_path = IMAGES_DIR / filename

    if image_path.exists():
        print(f"Image {filename} already exists, skipping download.")
        return str(image_path)

    print(f"Downloading image from {url}...")
    try:
        subprocess.run(
            ["wget", "-O", str(image_path), url],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ Image {filename} downloaded successfully.")
        return str(image_path)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error downloading image: {e.stderr}")


def get_image_path(os_name, config):
    """Returns the path to the OS image, downloading it if it doesn't exist."""
    if os_name not in config["images"]:
        raise ValueError(f"Unknown operating system: {os_name}")

    image_config = config["images"][os_name]
    url = image_config["url"]

    # Extract filename from URL
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    if not filename.endswith(('.qcow2', '.img')):
        filename += '.qcow2'

    return download_image(url, filename)
