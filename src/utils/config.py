"""Configuration loading from YAML files and environment variables."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional


_DEFAULT_CONFIG: Dict[str, Any] = {
    "backend": {
        "type": "memory",
        "url": "redis://localhost:6379/0",
    },
    "workers": {
        "count": 4,
        "timeout": 300,
    },
    "scheduler": {
        "enabled": True,
        "tick_interval": 1.0,
    },
    "logging": {
        "level": "INFO",
        "structured": False,
    },
    "dashboard": {
        "host": "0.0.0.0",
        "port": 8000,
    },
}


def load_config(
    config_path: Optional[str] = None,
    env_prefix: str = "TASKFORGE_",
) -> Dict[str, Any]:
    """Load configuration from YAML file and overlay environment variables."""
    config = dict(_DEFAULT_CONFIG)
    if config_path:
        file_config = _load_yaml(config_path)
        config = _deep_merge(config, file_config)
    env_config = _load_env(env_prefix)
    config = _deep_merge(config, env_config)
    return config


def _load_yaml(path: str) -> Dict[str, Any]:
    """Load a YAML configuration file."""
    try:
        import yaml
        file_path = Path(path)
        if not file_path.exists():
            return {}
        with open(file_path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    except ImportError:
        raise ImportError("Install pyyaml: pip install pyyaml>=6.0")


def _load_env(prefix: str) -> Dict[str, Any]:
    """Extract configuration values from environment variables."""
    result: Dict[str, Any] = {}
    prefix_upper = prefix.upper()
    for key, value in os.environ.items():
        if not key.startswith(prefix_upper):
            continue
        parts = key[len(prefix_upper) :].lower().split("_")
        nested = result
        for part in parts[:-1]:
            nested = nested.setdefault(part, {})
        nested[parts[-1]] = _coerce_value(value)
    return result


def _coerce_value(value: str) -> Any:
    """Attempt to coerce an env var string to a Python type."""
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge override into base."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result