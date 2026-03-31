"""Shared utilities for platform modules."""


def validate_platform_config(config, platform_name, required_keys):
    """Check that a platform section exists in config with all required keys non-empty.

    Args:
        config: Full config dict.
        platform_name: e.g. "twitter", "reddit".
        required_keys: List of key names that must be non-empty strings.

    Returns:
        Error message string, or None if valid.
    """
    section = config.get(platform_name)
    if not section or not isinstance(section, dict):
        return f"No '{platform_name}' section in config. Run /setup {platform_name} to configure."

    for key in required_keys:
        if not section.get(key):
            return f"Missing '{platform_name}.{key}' in config. Run /setup {platform_name} to fix."

    return None
