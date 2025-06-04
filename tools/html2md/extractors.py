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

"""Custom extractor system for html2md."""

import importlib.util
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from .utils import get_logger

logger = get_logger(__name__)


class BaseExtractor:
    """Base class for custom extractors."""
    
    def extract(self, soup: BeautifulSoup, config: Optional[Dict[str, Any]] = None) -> BeautifulSoup:
        """Extract content from HTML soup.
        
        Args:
            soup: BeautifulSoup object
            config: Optional configuration dict
            
        Returns:
            Processed BeautifulSoup object
        """
        raise NotImplementedError("Subclasses must implement extract()")
        
    def preprocess(self, html: str, config: Optional[Dict[str, Any]] = None) -> str:
        """Optional preprocessing of raw HTML.
        
        Args:
            html: Raw HTML string
            config: Optional configuration dict
            
        Returns:
            Preprocessed HTML string
        """
        return html
        
    def postprocess(self, markdown: str, config: Optional[Dict[str, Any]] = None) -> str:
        """Optional postprocessing of converted markdown.
        
        Args:
            markdown: Converted markdown string
            config: Optional configuration dict
            
        Returns:
            Postprocessed markdown string
        """
        return markdown


def load_extractor(extractor_path: Path) -> BaseExtractor:
    """Load a custom extractor from a Python file.
    
    Args:
        extractor_path: Path to the extractor Python file
        
    Returns:
        Extractor instance
        
    Raises:
        ValueError: If extractor cannot be loaded
    """
    if not extractor_path.exists():
        raise ValueError(f"Extractor file not found: {extractor_path}")
        
    # Load the module dynamically
    spec = importlib.util.spec_from_file_location("custom_extractor", extractor_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load extractor from {extractor_path}")
        
    module = importlib.util.module_from_spec(spec)
    sys.modules["custom_extractor"] = module
    spec.loader.exec_module(module)
    
    # Look for extractor class or function
    if hasattr(module, 'Extractor') and isinstance(module.Extractor, type):
        # Class-based extractor
        return module.Extractor()
    elif hasattr(module, 'extract'):
        # Function-based extractor - wrap in a class
        class FunctionExtractor(BaseExtractor):
            def extract(self, soup: BeautifulSoup, config: Optional[Dict[str, Any]] = None) -> BeautifulSoup:
                return module.extract(soup, config)
                
            def preprocess(self, html: str, config: Optional[Dict[str, Any]] = None) -> str:
                if hasattr(module, 'preprocess'):
                    return module.preprocess(html, config)
                return html
                
            def postprocess(self, markdown: str, config: Optional[Dict[str, Any]] = None) -> str:
                if hasattr(module, 'postprocess'):
                    return module.postprocess(markdown, config)
                return markdown
                
        return FunctionExtractor()
    else:
        raise ValueError(f"Extractor must define either an 'Extractor' class or an 'extract' function")


class DefaultExtractor(BaseExtractor):
    """Default extractor with basic cleaning."""
    
    def extract(self, soup: BeautifulSoup, config: Optional[Dict[str, Any]] = None) -> BeautifulSoup:
        """Basic extraction that removes common navigation elements."""
        # Remove script and style tags
        for tag in soup.find_all(['script', 'style', 'noscript']):
            tag.decompose()
            
        # Remove common navigation elements
        nav_selectors = [
            'nav', '[role="navigation"]',
            'header', '[role="banner"]', 
            'footer', '[role="contentinfo"]',
            '.sidebar', 'aside',
            '[role="search"]',
            '.menu', '.toolbar',
        ]
        
        for selector in nav_selectors:
            for elem in soup.select(selector):
                elem.decompose()
                
        return soup