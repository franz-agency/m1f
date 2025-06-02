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

import yaml

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
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    suffix = path.suffix.lower()

    if suffix in [".json"]:
        with open(path, "r") as f:
            data = json.load(f)
    elif suffix in [".yaml", ".yml"]:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    else:
        raise ValueError(f"Unsupported configuration format: {suffix}")

    return Config(**data)


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
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    elif suffix in [".yaml", ".yml"]:
        with open(path, "w") as f:
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
