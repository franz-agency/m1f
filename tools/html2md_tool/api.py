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

"""High-level API for HTML to Markdown conversion."""

import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Union

from rich.console import Console
from rich.progress import Progress

from .config import (
    Config,
    ConversionOptions,
    OutputFormat,
    ExtractorConfig,
    ProcessorConfig,
)
from .core import HTMLParser, MarkdownConverter
from .extractors import BaseExtractor, DefaultExtractor, load_extractor
from .utils import configure_logging, get_logger

logger = get_logger(__name__)


class Html2mdConverter:
    """Main API class for HTML to Markdown conversion."""

    def __init__(
        self,
        config: Union[Config, ConversionOptions, Dict, Path, str, None] = None,
        extractor: Optional[Union[BaseExtractor, Path, str]] = None,
    ):
        """Initialize converter with configuration.

        Args:
            config: Configuration object, ConversionOptions, dict, path to config file, or None
            extractor: Custom extractor instance, path to extractor file, or None
        """
        if config is None:
            self.config = Config(source=Path("."), destination=Path("."))
        elif isinstance(config, Config):
            self.config = config
        elif isinstance(config, ConversionOptions):
            # Create Config from ConversionOptions
            self.config = Config(
                source=Path(config.source_dir) if config.source_dir else Path("."),
                destination=(
                    config.destination_dir if config.destination_dir else Path(".")
                ),
                conversion=config,
            )
        elif isinstance(config, dict):
            self.config = Config(**config)
        elif isinstance(config, (Path, str)):
            from .config import load_config

            self.config = load_config(Path(config))
        else:
            raise TypeError(f"Invalid config type: {type(config)}")

        # Configure logging
        configure_logging(
            verbose=getattr(self.config, "verbose", False),
            quiet=getattr(self.config, "quiet", False),
            log_file=getattr(self.config, "log_file", None),
        )

        # Initialize components
        self._parser = HTMLParser(getattr(self.config, "extractor", ExtractorConfig()))
        self._converter = MarkdownConverter(
            getattr(self.config, "processor", ProcessorConfig())
        )
        self._console = Console()

        # Initialize extractor
        if extractor is None:
            self._extractor = DefaultExtractor()
        elif isinstance(extractor, BaseExtractor):
            self._extractor = extractor
        elif isinstance(extractor, (Path, str)):
            self._extractor = load_extractor(Path(extractor))
        else:
            raise TypeError(f"Invalid extractor type: {type(extractor)}")

    def convert_html(
        self,
        html_content: str,
        base_url: Optional[str] = None,
        source_file: Optional[str] = None,
    ) -> str:
        """Convert HTML content to Markdown.

        Args:
            html_content: HTML content to convert
            base_url: Optional base URL for resolving relative links
            source_file: Optional source file name

        Returns:
            Markdown content
        """
        # Apply custom extractor preprocessing
        html_content = self._extractor.preprocess(html_content, self.config.__dict__)

        # Apply preprocessing if configured
        if hasattr(self.config, "preprocessing") and self.config.preprocessing:
            from .preprocessors import preprocess_html

            html_content = preprocess_html(html_content, self.config.preprocessing)

        # Parse HTML
        parsed = self._parser.parse(html_content, base_url)

        # Apply custom extractor
        parsed = self._extractor.extract(parsed, self.config.__dict__)

        # Handle CSS selectors if specified (after extraction)
        if self.config.conversion.outermost_selector:
            from bs4 import BeautifulSoup

            selected = parsed.select_one(self.config.conversion.outermost_selector)
            if selected:
                # Remove ignored elements
                if self.config.conversion.ignore_selectors:
                    for selector in self.config.conversion.ignore_selectors:
                        for elem in selected.select(selector):
                            elem.decompose()
                # Create new soup from selected element
                parsed = BeautifulSoup(str(selected), "html.parser")

        # Remove script and style tags that may have been missed
        for tag in parsed.find_all(["script", "style", "noscript"]):
            tag.decompose()

        # Apply heading offset if specified
        if self.config.conversion.heading_offset:
            for i in range(1, 7):
                for tag in parsed.find_all(f"h{i}"):
                    new_level = max(
                        1, min(6, i + self.config.conversion.heading_offset)
                    )
                    tag.name = f"h{new_level}"

        # Convert to markdown
        options = {}
        if self.config.conversion.code_language:
            options["code_language"] = self.config.conversion.code_language
        if self.config.conversion.heading_style:
            options["heading_style"] = self.config.conversion.heading_style

        markdown = self._converter.convert(parsed, options)

        # Add frontmatter if requested
        if self.config.conversion.generate_frontmatter:
            import yaml

            frontmatter = self.config.conversion.frontmatter_fields or {}

            # Extract title from HTML if not provided
            if "title" not in frontmatter:
                title_tag = parsed.find("title")
                if title_tag and title_tag.string:
                    frontmatter["title"] = title_tag.string.strip()

            # Add source file if provided
            if source_file and "source_file" not in frontmatter:
                frontmatter["source_file"] = source_file

            if frontmatter:
                fm_str = yaml.dump(frontmatter, default_flow_style=False)
                markdown = f"---\n{fm_str}---\n\n{markdown}"

        # Apply custom extractor postprocessing
        markdown = self._extractor.postprocess(markdown, self.config.__dict__)

        return markdown

    async def convert_directory_from_urls(self, urls: List[str]) -> List[Path]:
        """Convert multiple URLs in parallel.

        Args:
            urls: List of URLs to convert

        Returns:
            List of output file paths
        """
        # Simple implementation for tests
        results = []
        for url in urls:
            # Actually convert the URL
            output_path = self.convert_url(url)
            results.append(output_path)
        return results

    def convert_file(self, file_path: Path) -> Path:
        """Convert a single HTML file to Markdown.

        Args:
            file_path: Path to HTML file

        Returns:
            Path to generated Markdown file
        """
        logger.info(f"Converting {file_path}")

        # Read file content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            for encoding in ["latin-1", "cp1252"]:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        html_content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # Last resort - ignore errors
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    html_content = f.read()

        # Convert using the convert_html method which includes preprocessing
        # Use a relative base URL to avoid exposing absolute paths
        file_name = (
            file_path.name
            if file_path and file_path.name
            else (Path(file_path).resolve().name if file_path else None)
        )
        base_url = file_name
        markdown = self.convert_html(
            html_content,
            base_url=base_url,
            source_file=str(file_name if file_name else "input"),
        )

        # Determine output path
        if file_path.is_relative_to(self.config.source):
            rel_path = file_path.relative_to(self.config.source)
        else:
            # Handle case where file_path might be "." or have empty name
            rel_path = (
                Path(file_path.name)
                if file_path.name
                else Path(file_path).resolve().name
            )
            if not rel_path or str(rel_path) == ".":
                rel_path = Path(file_path).resolve().name

        output_path = self.config.destination / Path(rel_path).with_suffix(".md")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        output_path.write_text(markdown, encoding=self.config.target_encoding)

        logger.debug(f"Written to {output_path}")
        return output_path

    def convert_directory(
        self, source_dir: Optional[Path] = None, recursive: bool = True
    ) -> List[Path]:
        """Convert all HTML files in a directory.

        Args:
            source_dir: Source directory (uses config if not specified)
            recursive: Whether to search recursively

        Returns:
            List of generated Markdown files
        """
        source_dir = source_dir or self.config.source

        # Find HTML files
        pattern = "**/*" if recursive else "*"
        html_files = []

        for ext in self.config.file_extensions:
            html_files.extend(source_dir.glob(f"{pattern}{ext}"))

        # Filter excluded patterns
        if self.config.exclude_patterns:
            import fnmatch

            filtered = []
            for file in html_files:
                excluded = False
                for pattern in self.config.exclude_patterns:
                    if fnmatch.fnmatch(str(file), pattern):
                        excluded = True
                        break
                if not excluded:
                    filtered.append(file)
            html_files = filtered

        logger.info(f"Found {len(html_files)} files to convert")

        # Convert files
        if self.config.parallel and len(html_files) > 1:
            return self._convert_parallel(html_files)
        else:
            return self._convert_sequential(html_files)

    def convert_url(self, url: str) -> Path:
        """Convert a web page to Markdown.

        Args:
            url: URL to convert

        Returns:
            Path to generated Markdown file
        """
        import requests
        from urllib.parse import urlparse

        logger.info(f"Fetching {url}")

        # Fetch HTML
        response = requests.get(url)
        response.raise_for_status()

        # Convert HTML to Markdown
        markdown = self.convert_html(response.text, base_url=url)

        # Determine output filename
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip("/").split("/")
        filename = path_parts[-1] if path_parts and path_parts[-1] else "index"
        if not filename.endswith(".md"):
            filename = filename.replace(".html", "") + ".md"
        output_path = Path(self.config.destination) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        encoding = getattr(self.config, "target_encoding", "utf-8")
        output_path.write_text(markdown, encoding=encoding)

        logger.info(f"Saved to {output_path}")
        return output_path

    def convert_website(self, start_url: str) -> Dict[str, Path]:
        """Convert an entire website to Markdown.

        DEPRECATED: Use the m1f-scrape tool to download websites first,
        then use convert_directory to convert the downloaded HTML files.

        Args:
            start_url: Starting URL for crawling

        Returns:
            Dictionary mapping source files to generated markdown files
        """
        logger.warning(
            "convert_website is deprecated. Use m1f-scrape tool for downloading."
        )
        logger.info(f"Website conversion starting from {start_url}")

        # Import crawler from m1f-scrape module
        raise NotImplementedError(
            "Website crawling has been moved to the m1f-scrape tool. "
            "Please use: m1f-scrape <url> -o <output_dir>"
        )

    async def convert_website_async(self, start_url: str) -> Dict[str, Path]:
        """Async version of convert_website for backward compatibility.

        Args:
            start_url: Starting URL for crawling

        Returns:
            Dictionary mapping URLs to generated files
        """
        # HTTrack runs synchronously, so we just wrap the sync method
        return self.convert_website(start_url)

    def _convert_sequential(self, files: List[Path]) -> List[Path]:
        """Convert files sequentially."""
        results = []

        with Progress() as progress:
            task = progress.add_task("Converting files...", total=len(files))

            for file in files:
                try:
                    output = self.convert_file(file)
                    results.append(output)
                except Exception as e:
                    logger.error(f"Failed to convert {file}: {e}")
                finally:
                    progress.update(task, advance=1)

        return results

    def _convert_parallel(self, files: List[Path]) -> List[Path]:
        """Convert files in parallel."""
        results = []
        max_workers = self.config.max_workers or None

        with Progress() as progress:
            task = progress.add_task("Converting files...", total=len(files))

            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self._convert_file_wrapper, file): file
                    for file in files
                }

                for future in futures:
                    try:
                        output = future.result()
                        if output:
                            results.append(output)
                    except Exception as e:
                        logger.error(f"Failed to convert {futures[future]}: {e}")
                    finally:
                        progress.update(task, advance=1)

        return results

    def _convert_file_wrapper(self, file_path: Path) -> Optional[Path]:
        """Wrapper for parallel processing."""
        try:
            # Re-initialize parser and converter in worker process
            parser = HTMLParser(self.config.extractor)
            converter = MarkdownConverter(self.config.processor)

            parsed = parser.parse_file(file_path)
            markdown = converter.convert(parsed)

            # Determine output path
            if file_path.is_relative_to(self.config.source):
                rel_path = file_path.relative_to(self.config.source)
            else:
                # Handle case where file_path might be "." or have empty name
                rel_path = (
                    Path(file_path.name)
                    if file_path.name
                    else Path(file_path).resolve().name
                )
                if not rel_path or str(rel_path) == ".":
                    rel_path = Path(file_path).resolve().name

            output_path = self.config.destination / Path(rel_path).with_suffix(".md")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding=self.config.target_encoding)

            return output_path
        except Exception as e:
            logger.error(f"Error in worker: {e}")
            return None

    def generate_m1f_bundle(self) -> Path:
        """Generate an m1f bundle from converted files.

        Returns:
            Path to generated m1f bundle
        """
        if not self.config.m1f.create_bundle:
            raise ValueError("m1f bundle creation not enabled in config")

        logger.info("Generating m1f bundle...")

        # Import m1f integration
        from .processors.m1f_integration import M1FBundler

        bundler = M1FBundler(self.config.m1f)
        bundle_path = bundler.create_bundle(
            self.config.destination, bundle_name=self.config.m1f.bundle_name
        )

        logger.info(f"Created m1f bundle: {bundle_path}")
        return bundle_path


# Convenience functions
def convert_file(file_path: Union[str, Path], **kwargs) -> Path:
    """Convert a single HTML file to Markdown.

    Args:
        file_path: Path to HTML file
        **kwargs: Additional configuration options

    Returns:
        Path to generated Markdown file
    """
    config = Config(
        source=Path(file_path).parent,
        destination=kwargs.pop("destination", Path(".")),
        **kwargs,
    )
    converter = Html2mdConverter(config)
    return converter.convert_file(Path(file_path))


def convert_directory(
    source_dir: Union[str, Path], destination_dir: Union[str, Path], **kwargs
) -> List[Path]:
    """Convert all HTML files in a directory to Markdown.

    Args:
        source_dir: Source directory containing HTML files
        destination_dir: Destination directory for Markdown files
        **kwargs: Additional configuration options

    Returns:
        List of generated Markdown files
    """
    config = Config(
        source=Path(source_dir), destination=Path(destination_dir), **kwargs
    )
    converter = Html2mdConverter(config)
    return converter.convert_directory()


def convert_url(url: str, destination_dir: Union[str, Path] = ".", **kwargs) -> Path:
    """Convert a web page to Markdown.

    Args:
        url: URL to convert
        destination_dir: Destination directory
        **kwargs: Additional configuration options

    Returns:
        Path to generated Markdown file
    """
    config = Config(
        source=Path("."),  # Not used for URL conversion
        destination=Path(destination_dir),
        **kwargs,
    )
    converter = Html2mdConverter(config)
    return converter.convert_url(url)


def convert_html(html_content: str, **kwargs) -> str:
    """Convert HTML content to Markdown.

    Args:
        html_content: HTML content to convert
        **kwargs: Additional options

    Returns:
        Markdown content
    """
    from pathlib import Path
    from .config.models import ConversionOptions, Config

    # Create minimal config
    config = Config(
        source=Path("."),
        destination=Path("."),
    )

    # Apply conversion options
    if kwargs:
        for key, value in kwargs.items():
            if hasattr(config.conversion, key):
                setattr(config.conversion, key, value)

    converter = Html2mdConverter(config)
    return converter.convert_html(html_content)
