import yaml  # type: ignore
from pathlib import Path

CONFIG_DIR = Path.home() / ".dockvirt"
CONFIG_PATH = CONFIG_DIR / "config.yaml"
IMAGES_DIR = CONFIG_DIR / "images"
PROJECT_CONFIG_FILE = ".dockvirt"

DEFAULT_CONFIG = {
    "default_os": "ubuntu22.04",
    "images": {
        'ubuntu22.04': {
            'url': ('https://cloud-images.ubuntu.com/jammy/current/'
                    'jammy-server-cloudimg-amd64.img'),
            'variant': 'ubuntu22.04'
        },
        'fedora38': {
            'url': ('https://download.fedoraproject.org/pub/fedora/linux/'
                    'releases/38/Cloud/x86_64/images/'
                    'Fedora-Cloud-Base-38-1.6.x86_64.qcow2'),
            'variant': 'fedora-cloud-base-38'
        },
    },
}


def load_project_config():
    """Ładuje konfigurację z lokalnego pliku .dockvirt w projekcie."""
    project_config_path = Path.cwd() / PROJECT_CONFIG_FILE
    if project_config_path.exists():
        config = {}
        with open(project_config_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
        return config
    return {}


def load_config():
    """Alias dla get_merged_config dla kompatybilności."""
    return get_merged_config()


def get_merged_config():
    # Wczytaj globalną konfigurację
    if not CONFIG_PATH.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
        global_config = DEFAULT_CONFIG.copy()
    else:
        with open(CONFIG_PATH, "r") as f:
            global_config = yaml.safe_load(f)

    # Wczytaj lokalną konfigurację projektu
    project_config = load_project_config()

    # Połącz konfiguracje - lokalny projekt ma priorytet
    merged_config = global_config.copy()
    if project_config:
        for key, value in project_config.items():
            merged_config[key] = value

    return merged_config
