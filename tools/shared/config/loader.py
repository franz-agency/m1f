# Copyright 2025 Franz und Franz GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Universal configuration loader for m1f tools

Supports JSON, YAML, and TOML formats with automatic format detection.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union, TypeVar, Type
import logging

from m1f.file_operations import (
    safe_exists,
    safe_open,
    safe_read_text,
)

logger = logging.getLogger(__name__)

# Type variable for config classes
T = TypeVar("T")


def load_config_file(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load configuration from a file.

    Automatically detects format based on file extension.

    Args:
        path: Path to configuration file

    Returns:
        Configuration as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
    """
    path = Path(path)

    if not safe_exists(path, logger):
        raise FileNotFoundError(f"Configuration file not found: {path}")

    suffix = path.suffix.lower()

    try:
        if suffix == ".json":
            with safe_open(path, "r", encoding="utf-8", logger=logger) as f:
                return json.load(f)

        elif suffix in [".yaml", ".yml"]:
            import yaml

            with safe_open(path, "r", encoding="utf-8", logger=logger) as f:
                return yaml.safe_load(f) or {}

        elif suffix == ".toml":
            try:
                import tomllib  # Python 3.11+
            except ImportError:
                import tomli as tomllib  # Fallback for older versions

            with safe_open(path, "rb", logger=logger) as f:
                return tomllib.load(f)

        else:
            raise ValueError(f"Unsupported configuration format: {suffix}")

    except Exception as e:
        logger.error(f"Error loading config from {path}: {e}")
        raise


def save_config_file(
    data: Dict[str, Any],
    path: Union[str, Path],
    format: Optional[str] = None,
    pretty: bool = True,
) -> None:
    """
    Save configuration to a file.

    Args:
        data: Configuration data
        path: Path to save to
        format: Force specific format (json, yaml, toml). If None, detect from extension
        pretty: Pretty-print the output

    Raises:
        ValueError: If format is not supported
    """
    path = Path(path)

    # Determine format
    if format:
        suffix = f".{format}"
    else:
        suffix = path.suffix.lower()

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if suffix in [".json"]:
            with safe_open(path, "w", encoding="utf-8", logger=logger) as f:
                if pretty:
                    json.dump(data, f, indent=2, sort_keys=True)
                else:
                    json.dump(data, f)

        elif suffix in [".yaml", ".yml"]:
            import yaml

            with safe_open(path, "w", encoding="utf-8", logger=logger) as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=True)

        elif suffix in [".toml"]:
            try:
                import tomli_w
            except ImportError:
                raise ImportError(
                    "tomli-w required for TOML output. Install with: pip install tomli-w"
                )

            with safe_open(path, "wb", logger=logger) as f:
                tomli_w.dump(data, f)

        else:
            raise ValueError(f"Unsupported configuration format: {suffix}")

    except Exception as e:
        logger.error(f"Error saving config to {path}: {e}")
        raise


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge multiple configuration dictionaries.

    Later configs override earlier ones.

    Args:
        *configs: Configuration dictionaries to merge

    Returns:
        Merged configuration
    """
    result = {}

    for config in configs:
        if config:
            _deep_merge(result, config)

    return result


def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> None:
    """
    Deep merge update into base (modifies base in-place).

    Args:
        base: Base dictionary to merge into
        update: Dictionary to merge from
    """
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            # Recursively merge dictionaries
            _deep_merge(base[key], value)
        else:
            # Override value
            base[key] = value


def load_config_with_defaults(
    path: Optional[Union[str, Path]] = None,
    defaults: Optional[Dict[str, Any]] = None,
    env_prefix: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Load configuration with defaults and environment variable overrides.

    Args:
        path: Optional path to config file
        defaults: Default configuration values
        env_prefix: Prefix for environment variables (e.g., "M1F_RESEARCH_")

    Returns:
        Merged configuration
    """
    # Start with defaults
    config = defaults.copy() if defaults else {}

    # Load from file if provided
    if path and safe_exists(Path(path), logger):
        file_config = load_config_file(path)
        config = merge_configs(config, file_config)

    # Apply environment variable overrides
    if env_prefix:
        import os

        env_config = {}

        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                # Convert M1F_RESEARCH_URL_COUNT to url_count
                config_key = key[len(env_prefix) :].lower()

                # Try to parse as JSON first (for complex values)
                try:
                    env_config[config_key] = json.loads(value)
                except json.JSONDecodeError:
                    # Keep as string
                    env_config[config_key] = value

        if env_config:
            logger.debug(f"Applying environment overrides: {list(env_config.keys())}")
            config = merge_configs(config, env_config)

    return config


def validate_config(
    config: Dict[str, Any], schema: Dict[str, Any], strict: bool = False
) -> bool:
    """
    Validate configuration against a schema.

    Args:
        config: Configuration to validate
        schema: Schema definition
        strict: If True, fail on extra fields

    Returns:
        True if valid

    Raises:
        ValueError: If validation fails
    """
    # This is a simple implementation. For production, use jsonschema or similar
    errors = []

    # Check required fields
    for field, field_schema in schema.items():
        if field_schema.get("required", False) and field not in config:
            errors.append(f"Missing required field: {field}")

    # Check types
    for field, value in config.items():
        if field in schema:
            expected_type = schema[field].get("type")
            if expected_type and not isinstance(value, expected_type):
                errors.append(
                    f"Field '{field}' should be {expected_type.__name__}, got {type(value).__name__}"
                )
        elif strict:
            errors.append(f"Unknown field: {field}")

    if errors:
        raise ValueError(
            "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    return True
