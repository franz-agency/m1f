"""
Universal prompt loader for m1f tools

This module provides a flexible prompt loading system that can be used
by any m1f tool. It supports:
- Loading prompts from filesystem
- Caching for performance
- Template formatting
- Fallback mechanisms
"""

from pathlib import Path
from typing import Dict, Optional, Union, List
import logging
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class PromptLoader:
    """
    Flexible prompt loader that can load from multiple directories.
    
    Attributes:
        base_dirs: List of base directories to search for prompts
        cache_enabled: Whether to cache loaded prompts
        encoding: File encoding (default: utf-8)
    """
    base_dirs: List[Path]
    cache_enabled: bool = True
    encoding: str = 'utf-8'
    
    def __post_init__(self):
        """Ensure base_dirs are Path objects"""
        self.base_dirs = [Path(d) for d in self.base_dirs]
        self._cache: Dict[str, str] = {}
    
    def add_search_path(self, path: Union[str, Path]):
        """Add a new search path for prompts"""
        self.base_dirs.append(Path(path))
    
    def load(self, prompt_path: str) -> str:
        """
        Load a prompt from the first matching file in search paths.
        
        Args:
            prompt_path: Relative path to prompt (e.g., "analysis/synthesis.md")
            
        Returns:
            Prompt content as string
            
        Raises:
            FileNotFoundError: If prompt not found in any search path
        """
        # Check cache first
        if self.cache_enabled and prompt_path in self._cache:
            logger.debug(f"Loaded prompt from cache: {prompt_path}")
            return self._cache[prompt_path]
        
        # Search in all base directories
        for base_dir in self.base_dirs:
            full_path = base_dir / prompt_path
            if full_path.exists() and full_path.is_file():
                content = full_path.read_text(encoding=self.encoding)
                
                # Cache if enabled
                if self.cache_enabled:
                    self._cache[prompt_path] = content
                
                logger.debug(f"Loaded prompt from: {full_path}")
                return content
        
        # Not found in any path
        searched_paths = [str(base_dir / prompt_path) for base_dir in self.base_dirs]
        raise FileNotFoundError(
            f"Prompt '{prompt_path}' not found in any of these locations:\n" + 
            "\n".join(f"  - {p}" for p in searched_paths)
        )
    
    def load_with_fallback(self, primary_path: str, fallback_path: str) -> str:
        """
        Load a prompt with fallback option.
        
        Args:
            primary_path: Primary prompt path to try
            fallback_path: Fallback path if primary not found
            
        Returns:
            Prompt content from primary or fallback
        """
        try:
            return self.load(primary_path)
        except FileNotFoundError:
            logger.debug(f"Primary prompt not found, using fallback: {fallback_path}")
            return self.load(fallback_path)
    
    def format(self, prompt_path: str, **kwargs) -> str:
        """
        Load and format a prompt with variables.
        
        Args:
            prompt_path: Path to prompt template
            **kwargs: Variables to substitute
            
        Returns:
            Formatted prompt
        """
        template = self.load(prompt_path)
        return format_prompt(template, **kwargs)
    
    def clear_cache(self):
        """Clear the prompt cache"""
        self._cache.clear()
        logger.debug("Cleared prompt cache")


# Global prompt loader instance - tools can add their own paths
_global_loader: Optional[PromptLoader] = None


def get_global_loader() -> PromptLoader:
    """Get or create the global prompt loader"""
    global _global_loader
    if _global_loader is None:
        # Start with shared prompts directory
        shared_prompts = Path(__file__).parent.parent / "prompts"
        _global_loader = PromptLoader([shared_prompts])
    return _global_loader


def load_prompt(prompt_path: str, base_dir: Optional[Path] = None) -> str:
    """
    Load a prompt using the global loader or a specific base directory.
    
    Args:
        prompt_path: Relative path to prompt
        base_dir: Optional specific base directory (adds to search paths)
        
    Returns:
        Prompt content
    """
    loader = get_global_loader()
    
    # Add base_dir to search paths if provided
    if base_dir and base_dir not in loader.base_dirs:
        loader.add_search_path(base_dir)
    
    return loader.load(prompt_path)


def format_prompt(template: str, **kwargs) -> str:
    """
    Format a prompt template with variables.
    
    Args:
        template: Prompt template with {variable} placeholders
        **kwargs: Variables to substitute
        
    Returns:
        Formatted prompt
        
    Raises:
        ValueError: If required variables are missing
    """
    try:
        # Use format_map for better error messages
        return template.format_map(kwargs)
    except KeyError as e:
        # Find all required variables
        import re
        required_vars = set(re.findall(r'\{(\w+)\}', template))
        provided_vars = set(kwargs.keys())
        missing_vars = required_vars - provided_vars
        
        raise ValueError(
            f"Missing required variables in prompt template: {', '.join(missing_vars)}\n"
            f"Required: {required_vars}\n"
            f"Provided: {provided_vars}"
        )


@lru_cache(maxsize=128)
def get_prompt_variables(template: str) -> List[str]:
    """
    Extract variable names from a prompt template.
    
    Args:
        template: Prompt template
        
    Returns:
        List of variable names
    """
    import re
    return list(set(re.findall(r'\{(\w+)\}', template)))


def validate_prompt_args(template: str, **kwargs) -> bool:
    """
    Validate that all required variables are provided.
    
    Args:
        template: Prompt template
        **kwargs: Provided variables
        
    Returns:
        True if all required variables are provided
    """
    required = set(get_prompt_variables(template))
    provided = set(kwargs.keys())
    return required.issubset(provided)