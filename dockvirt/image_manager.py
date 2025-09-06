import os
import shutil
import subprocess
from urllib.parse import urlparse

from .config import IMAGES_DIR


def download_image(url, filename):
    """Downloads an image from the given URL and saves it to the images directory.

    Robust behavior:
    - Retries with sensible timeouts
    - Falls back to alternate Fedora mirror domain if primary fails
    - Uses curl if available, otherwise wget
    """
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    image_path = IMAGES_DIR / filename

    if image_path.exists() and image_path.stat().st_size > 0:
        print(f"Image {filename} already exists, skipping download.")
        return str(image_path)

    # Build candidate URL list (fallback to dl.fedoraproject.org for Fedora images)
    urls = [url]
    if "download.fedoraproject.org" in url:
        alt = url.replace("download.fedoraproject.org", "dl.fedoraproject.org")
        if alt != url:
            urls.append(alt)

    last_err = ""
    for u in urls:
        print(f"Downloading image from {u}...")
        for attempt in range(1, 4):
            try:
                if shutil.which("curl"):
                    cmd = [
                        "curl", "-L", "--fail",
                        "--retry", "5", "--retry-all-errors",
                        "--connect-timeout", "10", "--max-time", "600",
                        "-o", str(image_path), u,
                    ]
                else:
                    cmd = [
                        "wget", "-t", "5", "--waitretry=5", "--read-timeout=60",
                        "-O", str(image_path), u,
                    ]
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                if image_path.exists() and image_path.stat().st_size > 0:
                    print(f"✅ Image {filename} downloaded successfully.")
                    return str(image_path)
                else:
                    last_err = "zero-size file after download"
            except subprocess.CalledProcessError as e:
                last_err = e.stderr or e.stdout or str(e)
                # Clean partial file and retry
                try:
                    if image_path.exists():
                        image_path.unlink()
                except FileNotFoundError:
                    pass
                print(f"Retry {attempt}/3 failed: {last_err}")
        # Next URL fallback

    raise RuntimeError(f"Error downloading image: {last_err}")


def get_image_path(os_name, config):
    """Returns the path to the OS image, downloading it if it doesn't exist.

    Robustly merges both 'images' and 'os_images' so that either key is accepted.
    """
    images_map = {}
    cfg_images = config.get("images")
    cfg_os_images = config.get("os_images")
    if isinstance(cfg_images, dict):
        images_map.update(cfg_images)
    if isinstance(cfg_os_images, dict):
        for k, v in cfg_os_images.items():
            images_map.setdefault(k, v)

    if os_name not in images_map:
        raise ValueError(f"Unknown operating system: {os_name}")

    image_config = images_map[os_name]
    url = image_config["url"]

    # Extract filename from URL
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    if not filename.endswith(('.qcow2', '.img')):
        filename += '.qcow2'

    return download_image(url, filename)
