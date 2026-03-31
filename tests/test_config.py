import os
import sys
import tempfile

_PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugin")
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

import yaml


def test_get_config_path_returns_social_agent():
    """get_config_path returns .social-agent.yaml in CWD."""
    from scripts.utils.config import get_config_path

    path = get_config_path()
    assert path.endswith(".social-agent.yaml")


def test_load_config_nested_structure():
    """load_config correctly loads nested platform credentials."""
    from scripts.utils.config import load_config

    config_data = {
        "kie_api_key": "test-key",
        "twitter": {
            "api_key": "tk",
            "api_secret": "ts",
            "access_token": "tt",
            "access_secret": "ta",
        },
        "reddit": {
            "client_id": "rc",
            "client_secret": "rs",
            "username": "ru",
            "password": "rp",
        },
        "auto_post": False,
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        path = f.name

    try:
        config = load_config(path)
        assert config["kie_api_key"] == "test-key"
        assert config["twitter"]["api_key"] == "tk"
        assert config["reddit"]["client_id"] == "rc"
        assert config["auto_post"] is False
    finally:
        os.unlink(path)


def test_load_config_missing_file():
    """load_config returns None for non-existent file."""
    from scripts.utils.config import load_config

    result = load_config("/nonexistent/path/config.yaml")
    assert result is None
