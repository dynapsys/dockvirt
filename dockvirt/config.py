import yaml  # type: ignore
import logging
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
            'url': ('https://archives.fedoraproject.org/pub/archive/fedora/linux/'
                    'releases/38/Cloud/x86_64/images/'
                    'Fedora-Cloud-Base-38-1.6.x86_64.qcow2'),
            'variant': 'fedora38'
        },
    },
}


def load_project_config():
    """Loads configuration from a local .dockvirt file in the project."""
    project_config_path = Path.cwd() / PROJECT_CONFIG_FILE
    logger.debug(f"Looking for project config at: {project_config_path}")
    
    if project_config_path.exists():
        logger.info(f"Found project config file: {project_config_path}")
        config = {}
        with open(project_config_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
        logger.debug(f"Loaded project config: {config}")
        return config
    else:
        logger.debug("No project config file found")
    return {}


def load_config():
    """Alias for get_merged_config for compatibility."""
    return get_merged_config()


def get_merged_config():
    logger.debug("Loading merged configuration")
    
    # Load global configuration
    if not CONFIG_PATH.exists():
        logger.info(f"Creating default config at: {CONFIG_PATH}")
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
        global_config = DEFAULT_CONFIG.copy()
        logger.debug("Using default configuration")
    else:
        logger.debug(f"Loading global config from: {CONFIG_PATH}")
        with open(CONFIG_PATH, "r") as f:
            global_config = yaml.safe_load(f)
        logger.debug(f"Global config loaded: {global_config.get('default_os', 'unknown')} OS")

    # Load local project configuration
    project_config = load_project_config()

    # Merge configurations - local project has priority
    merged_config = global_config.copy()
    if project_config:
        logger.info(f"Merging {len(project_config)} project-specific settings")
        for key, value in project_config.items():
            if key in merged_config:
                logger.debug(f"Overriding {key}: {merged_config[key]} -> {value}")
            else:
                logger.debug(f"Adding {key}: {value}")
            merged_config[key] = value
    else:
        logger.debug("No project config to merge")

    # Unify legacy keys: support both 'images' and 'os_images' by merging into one mapping
    images_map = {}
    try:
        if isinstance(global_config.get('images'), dict):
            images_map.update(global_config.get('images', {}))
        if isinstance(global_config.get('os_images'), dict):
            # Do not clobber existing entries from 'images'
            for k, v in global_config.get('os_images', {}).items():
                images_map.setdefault(k, v)
        if isinstance(project_config.get('images') if project_config else None, dict):
            images_map.update(project_config.get('images', {}))
        if isinstance(project_config.get('os_images') if project_config else None, dict):
            for k, v in project_config.get('os_images', {}).items():
                images_map.setdefault(k, v)
    except Exception:
        # Fallback: keep whatever was there
        pass

    # Ensure baseline known defaults exist even if user's config.yaml was older
    defaults = {
        'ubuntu22.04': {
            'url': ('https://cloud-images.ubuntu.com/jammy/current/'
                    'jammy-server-cloudimg-amd64.img'),
            'variant': 'ubuntu22.04'
        },
        'fedora38': {
            'url': ('https://download.fedoraproject.org/pub/fedora/linux/'
                    'releases/38/Cloud/x86_64/images/'
                    'Fedora-Cloud-Base-38-1.6.x86_64.qcow2'),
            'variant': 'fedora38'
        },
    }
    for k, v in defaults.items():
        images_map.setdefault(k, v)

    if images_map:
        merged_config['images'] = images_map
        # Also keep 'os_images' in sync for backward compatibility
        merged_config['os_images'] = images_map

    logger.info(
        f"Final config: OS={merged_config.get('default_os', 'unknown')}, {len(merged_config.get('images', {}))} OS images available"
    )
    return merged_config
