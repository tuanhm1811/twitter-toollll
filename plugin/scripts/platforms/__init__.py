"""Platform modules for social media posting.

Each platform module implements:
    post(config, content_parts, images=None) -> dict
    validate_config(config) -> str | None
"""

PLATFORMS = {
    "twitter": "scripts.platforms.twitter",
    "reddit": "scripts.platforms.reddit",
    "threads": "scripts.platforms.threads",
    "facebook": "scripts.platforms.facebook",
}


def get_platform_module(platform_name):
    """Import and return the platform module for the given name.

    Returns None if platform is not supported.
    """
    module_path = PLATFORMS.get(platform_name)
    if not module_path:
        return None

    import importlib
    return importlib.import_module(module_path)
