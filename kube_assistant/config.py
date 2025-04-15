"""
Configuration management for kube-assistant.

This module handles reading and writing configuration settings to a file in the user's
home directory, allowing settings to persist between CLI invocations.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration directory and file paths
CONFIG_DIR = Path.home() / ".kube-assistant"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Default configuration
DEFAULT_CONFIG = {
    "provider": "openai",
    "openai": {"api_key": "", "model": "gpt-4o"},
    "azure": {
        "api_key": "",
        "endpoint": "",
        "deployment": "",
        "api_version": "2023-05-15",
    },
}


def ensure_config_dir() -> None:
    """Ensure the configuration directory exists."""
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True)


def load_config() -> Dict[str, Any]:
    """
    Load configuration from file, or create a new one if it doesn't exist.

    Returns:
        Dictionary containing configuration settings
    """
    ensure_config_dir()

    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return config
    except (json.JSONDecodeError, IOError):
        # If config file is corrupted or can't be read, return defaults
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to file.

    Args:
        config: Dictionary containing configuration settings
    """
    ensure_config_dir()

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_provider() -> str:
    """
    Get the configured provider.

    Returns:
        Provider name ('openai' or 'azure')
    """
    config = load_config()
    return config.get("provider", DEFAULT_CONFIG["provider"])


def get_openai_settings() -> Dict[str, str]:
    """
    Get OpenAI settings.

    Returns:
        Dictionary of OpenAI settings
    """
    config = load_config()
    return config.get("openai", DEFAULT_CONFIG["openai"])


def get_azure_settings() -> Dict[str, str]:
    """
    Get Azure OpenAI settings.

    Returns:
        Dictionary of Azure OpenAI settings
    """
    config = load_config()
    return config.get("azure", DEFAULT_CONFIG["azure"])


def update_provider(provider: str) -> None:
    """
    Update the provider setting.

    Args:
        provider: Provider name ('openai' or 'azure')
    """
    config = load_config()
    config["provider"] = provider
    save_config(config)


def update_openai_settings(
    api_key: Optional[str] = None, model: Optional[str] = None
) -> None:
    """
    Update OpenAI settings.

    Args:
        api_key: OpenAI API key
        model: OpenAI model name
    """
    config = load_config()

    if api_key is not None:
        config["openai"]["api_key"] = api_key

    if model is not None:
        config["openai"]["model"] = model

    save_config(config)


def update_azure_settings(
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    deployment: Optional[str] = None,
    api_version: Optional[str] = None,
) -> None:
    """
    Update Azure OpenAI settings.

    Args:
        api_key: Azure OpenAI API key
        endpoint: Azure OpenAI endpoint URL
        deployment: Azure OpenAI deployment name
        api_version: Azure OpenAI API version
    """
    config = load_config()

    if api_key is not None:
        config["azure"]["api_key"] = api_key

    if endpoint is not None:
        config["azure"]["endpoint"] = endpoint

    if deployment is not None:
        config["azure"]["deployment"] = deployment

    if api_version is not None:
        config["azure"]["api_version"] = api_version

    save_config(config)


def view_config() -> str:
    """
    Get a string representation of the current configuration (with API keys redacted).

    Returns:
        A string representation of the configuration
    """
    config = load_config()

    # Create a copy of the config with API keys redacted for display
    display_config = config.copy()
    if display_config.get("openai", {}).get("api_key"):
        display_config["openai"]["api_key"] = (
            "***" + display_config["openai"]["api_key"][-4:]
            if len(display_config["openai"]["api_key"]) > 4
            else "***"
        )

    if display_config.get("azure", {}).get("api_key"):
        display_config["azure"]["api_key"] = (
            "***" + display_config["azure"]["api_key"][-4:]
            if len(display_config["azure"]["api_key"]) > 4
            else "***"
        )

    return json.dumps(display_config, indent=2)


def clear_config() -> None:
    """Clear all configuration settings."""
    save_config(DEFAULT_CONFIG.copy())
