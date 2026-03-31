import os
import yaml


def get_config_path():
    """Return the config file path in the current working directory."""
    return os.path.join(os.getcwd(), ".social-agent.yaml")


def load_config(path=None):
    """Load config from a YAML file.

    Returns the parsed YAML dict, or None if file doesn't exist.
    """
    if path is None:
        path = get_config_path()

    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        content = f.read().strip()

    if not content:
        return {}

    return yaml.safe_load(content) or {}


def save_config(config, path=None):
    """Save config dict as a YAML file."""
    if path is None:
        path = get_config_path()

    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    yaml_str = yaml.dump(config, default_flow_style=False, sort_keys=False)

    with open(path, "w") as f:
        f.write(yaml_str)
