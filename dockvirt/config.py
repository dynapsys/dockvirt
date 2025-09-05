import yaml  # type: ignore
from pathlib import Path

CONFIG_DIR = Path.home() / ".dockvirt"
CONFIG_PATH = CONFIG_DIR / "config.yaml"
IMAGES_DIR = CONFIG_DIR / "images"

DEFAULT_CONFIG = {
    "default_os": "ubuntu22.04",
    "images": {
        "ubuntu22.04": {
            "url": "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img",
            "variant": "ubuntu22.04",
        },
        "fedora36": {
            "url": "https://download.fedoraproject.org/pub/fedora/linux/releases/36/Cloud/x86_64/images/Fedora-Cloud-Base-36-1.5.x86_64.qcow2",
            "variant": "fedora-cloud-base-36",
        },
    },
}

def load_config():
    """Ładuje konfigurację z pliku YAML, tworząc domyślny, jeśli nie istnieje."""
    if not CONFIG_PATH.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
        return DEFAULT_CONFIG

    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)
