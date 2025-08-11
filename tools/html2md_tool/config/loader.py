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

"""Configuration loading and saving utilities."""

import json
from pathlib import Path
from typing import Any, Dict
import warnings
from dataclasses import fields

import yaml
import sys

# Import safe file operations
from ...m1f.file_operations import safe_exists, safe_open

# Use unified colorama module
from ...shared.colors import (
    Colors,
    success,
    error,
    warning,
    info,
    header,
    COLORAMA_AVAILABLE,
)

from .models import Config


def load_config(path: Path) -> Config:
    """Load configuration from file.

    Args:
        path: Path to configuration file (JSON or YAML)

    Returns:
        Config object

    Raises:
        ValueError: If file format is not supported
        FileNotFoundError: If file does not exist
    """
    if not safe_exists(path):
        raise FileNotFoundError(f"Configuration file not found: {path}")

    suffix = path.suffix.lower()

    if suffix in [".json"]:
        with safe_open(path, "r") as f:
            data = json.load(f)
    elif suffix in [".yaml", ".yml"]:
        with safe_open(path, "r") as f:
            data = yaml.safe_load(f)
    else:
        raise ValueError(f"Unsupported configuration format: {suffix}")

    # Import nested config models
    from .models import (
        ConversionOptions,
        ExtractorConfig,
        ProcessorConfig,
        AssetConfig,
        CrawlerConfig,
        M1fConfig,
    )

    # Get valid field names from Config dataclass
    valid_fields = {f.name for f in fields(Config)}

    # Filter out unknown fields and warn about them
    filtered_data = {}
    unknown_fields = []

    for key, value in data.items():
        if key in valid_fields:
            # Convert string paths to Path objects for specific fields
            if key in ["source", "destination", "log_file"] and value is not None:
                filtered_data[key] = Path(value)
            # Handle nested configuration objects
            elif key == "conversion" and isinstance(value, dict):
                filtered_data[key] = ConversionOptions(**value)
            elif key == "extractor" and isinstance(value, dict):
                filtered_data[key] = ExtractorConfig(**value)
            elif key == "processor" and isinstance(value, dict):
                filtered_data[key] = ProcessorConfig(**value)
            elif key == "assets" and isinstance(value, dict):
                filtered_data[key] = AssetConfig(**value)
            elif key == "crawler" and isinstance(value, dict):
                filtered_data[key] = CrawlerConfig(**value)
            elif key == "m1f" and isinstance(value, dict):
                filtered_data[key] = M1fConfig(**value)
            else:
                filtered_data[key] = value
        else:
            unknown_fields.append(key)

    # Warn about unknown fields
    if unknown_fields:
        warning(f"Ignoring unknown configuration fields: {', '.join(unknown_fields)}")
        info(
            f"{Colors.DIM}   These fields are not recognized by m1f-html2md and will be ignored.{Colors.RESET}"
        )

    return Config(**filtered_data)


def save_config(config: Config, path: Path) -> None:
    """Save configuration to file.

    Args:
        config: Config object to save
        path: Path to save configuration to

    Raises:
        ValueError: If file format is not supported
    """
    suffix = path.suffix.lower()

    # Convert dataclass to dict
    data = _config_to_dict(config)

    if suffix in [".json"]:
        with safe_open(path, "w") as f:
            json.dump(data, f, indent=2)
    elif suffix in [".yaml", ".yml"]:
        with safe_open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
    else:
        raise ValueError(f"Unsupported configuration format: {suffix}")


def _config_to_dict(config: Config) -> Dict[str, Any]:
    """Convert Config object to dictionary.

    Args:
        config: Config object

    Returns:
        Dictionary representation
    """
    from dataclasses import asdict

    data = asdict(config)

    # Convert Path objects to strings
    def convert_paths(obj):
        if isinstance(obj, dict):
            return {k: convert_paths(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_paths(v) for v in obj]
        elif isinstance(obj, Path):
            return str(obj)
        else:
            return obj

    return convert_paths(data)
