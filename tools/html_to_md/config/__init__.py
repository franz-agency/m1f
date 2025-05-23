"""Configuration module for HTML to Markdown converter."""

from .loader import ConfigLoader, load_config
from .models import (
    AssetConfig,
    ConversionOptions,
    CrawlerConfig,
    ExtractorConfig,
    HeadingStyle,
    LinkHandling,
    M1FConfig,
    OutputFormat,
    ProcessorConfig,
)

# Convenience re-export
Config = ConversionOptions

__all__ = [
    "Config",
    "ConfigLoader",
    "load_config",
    "ConversionOptions",
    "ExtractorConfig",
    "ProcessorConfig", 
    "CrawlerConfig",
    "AssetConfig",
    "M1FConfig",
    "OutputFormat",
    "HeadingStyle",
    "LinkHandling",
] 