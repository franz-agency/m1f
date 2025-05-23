"""Configuration loader with support for YAML and TOML files."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
try:
    import tomllib
except ImportError:
    import tomli as tomllib

from .models import ConversionOptions


class ConfigLoader:
    """Load configuration from various sources."""
    
    def __init__(self, config_file: Optional[Path] = None):
        """Initialize config loader.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config_file = config_file
        self.config_data: Dict[str, Any] = {}
    
    def load(self) -> ConversionOptions:
        """Load configuration from file.
        
        Returns:
            Loaded configuration object
            
        Raises:
            ValueError: If config file format is not supported
        """
        if self.config_file:
            self.config_data = self._load_file(self.config_file)
        
        return ConversionOptions(**self.config_data)
    
    def _load_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from file based on extension.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Configuration dictionary
            
        Raises:
            ValueError: If file format is not supported
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        suffix = file_path.suffix.lower()
        
        if suffix in {".yaml", ".yml"}:
            return self._load_yaml(file_path)
        elif suffix == ".toml":
            return self._load_toml(file_path)
        elif suffix == ".json":
            return self._load_json(file_path)
        else:
            raise ValueError(f"Unsupported configuration format: {suffix}")
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML configuration file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    
    def _load_toml(self, file_path: Path) -> Dict[str, Any]:
        """Load TOML configuration file."""
        with open(file_path, "rb") as f:
            return tomllib.load(f)
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON configuration file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def merge_cli_args(self, cli_args: Dict[str, Any]) -> None:
        """Merge CLI arguments into configuration.
        
        CLI arguments take precedence over file configuration.
        
        Args:
            cli_args: Dictionary of CLI arguments
        """
        # Remove None values from CLI args
        cli_args = {k: v for k, v in cli_args.items() if v is not None}
        
        # Deep merge with CLI args taking precedence
        self.config_data = self._deep_merge(self.config_data, cli_args)
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            update: Dictionary to merge in (takes precedence)
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def save(self, file_path: Path, format: Optional[str] = None) -> None:
        """Save current configuration to file.
        
        Args:
            file_path: Path to save configuration to
            format: Format to save in (yaml, toml, json). If None, inferred from extension.
        """
        if format is None:
            suffix = file_path.suffix.lower()
            format = suffix.lstrip(".")
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format in {"yaml", "yml"}:
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config_data, f, default_flow_style=False, sort_keys=False)
        elif format == "toml":
            # toml writing requires tomlkit for preserving formatting
            try:
                import tomlkit
                with open(file_path, "w", encoding="utf-8") as f:
                    tomlkit.dump(self.config_data, f)
            except ImportError:
                raise ImportError("tomlkit required for writing TOML files")
        elif format == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2)
        else:
            raise ValueError(f"Unsupported format for saving: {format}")


def load_config(
    config_file: Optional[Union[str, Path]] = None,
    cli_args: Optional[Dict[str, Any]] = None
) -> ConversionOptions:
    """Convenience function to load configuration.
    
    Args:
        config_file: Optional configuration file path
        cli_args: Optional CLI arguments to merge
        
    Returns:
        Loaded configuration
    """
    if config_file:
        config_file = Path(config_file)
    
    loader = ConfigLoader(config_file)
    
    if config_file:
        config = loader.load()
    else:
        config = ConversionOptions(**cli_args or {})
    
    if cli_args and config_file:
        loader.merge_cli_args(cli_args)
        config = loader.load()
    
    return config 