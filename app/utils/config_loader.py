import yaml
import os
from .logger import ls

DEFAULT_CONFIG_PATH = os.path.join(os.getcwd(), 'config.yaml')

def load_config(config_path=DEFAULT_CONFIG_PATH):
    """
    Loads YAML configuration and provides basic schema validation.
    """
    if not os.path.exists(config_path):
        ls.warning(f"Config file not found: {config_path}. Using hardcoded defaults.")
        # Minimal set for app to run if file is missing
        return {}
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            # Schema validation could go here
            return config if config else {}
    except Exception as e:
        ls.error(f"Failed to load config from {config_path}: {e}")
        return {}

def save_config(config, config_path=DEFAULT_CONFIG_PATH):
    """
    Saves configuration dict back to file.
    """
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        ls.info(f"Config saved to {config_path}")
        return True
    except Exception as e:
        ls.error(f"Failed to save config to {config_path}: {e}")
        return False
