#!/usr/bin/env python3
"""
===========================
html_to_md - HTML to Markdown Converter
===========================

SYNOPSIS
========
Converts HTML files to Markdown recursively with customizable options for content
extraction, formatting, and link handling. Supports various selector options to target
specific content within HTML documents, and can handle complex conversions with custom
rules.

DESCRIPTION
===========
This script helps convert HTML content to Markdown format, which is useful for:

- Creating documentation from web content
- Converting existing HTML documentation to more readable Markdown
- Extracting content from HTML files for use with Large Language Models (LLMs)
- Pre-processing web content for inclusion in m1f bundles

KEY FEATURES
============
- Recursive file scanning to process all HTML files in a directory structure
- Customizable CSS selectors to target specific content within HTML files
- Option to ignore specific HTML elements during conversion
- Automatic adjustment of internal links to point to Markdown files
- Smart handling of HTML comments, script tags, and style blocks
- Configurable output formatting options, including frontmatter generation
- Support for various Markdown flavors via custom conversion options
- Character encoding detection and conversion for international content
- Detailed logging and performance metrics
- Parallel processing support for faster conversion of large document sets

REQUIREMENTS
============
- Python 3.9+ 
- BeautifulSoup4: HTML parsing
- markdownify: Core HTML to Markdown conversion
- chardet (optional): Character encoding detection

INSTALLATION
============
No special installation is needed. Just download the script and ensure it has execute 
permissions if you want to run it directly (e.g., `chmod +x html_to_md.py` on 
Linux/macOS).

Required Python packages can be installed with:
  pip install beautifulsoup4 markdownify chardet

USAGE
=====
Basic command:
  python tools/html_to_md.py --source-dir /path/to/html/files --destination-dir /path/to/output

Advanced usage with content selection:
  python tools/html_to_md.py --source-dir ./docs/html --destination-dir ./docs/markdown \
    --outermost-selector "main.content" --ignore-selectors "nav" "footer" ".sidebar"

With heading level adjustment and frontmatter:
  python tools/html_to_md.py --source-dir ./website --destination-dir ./docs \
    --heading-offset 1 --add-frontmatter

For all options, run:
  python tools/html_to_md.py --help

AUTHOR
======
Franz und Franz (https://franz.agency)

VERSION
=======
1.0.0
"""

import argparse
import datetime
import logging
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Comment

# Try to import optional modules
try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Import markdownify - required for the core functionality
from markdownify import markdownify

# --- Configuration ---
# Default HTML file extensions to look for
HTML_EXTENSIONS = {".html", ".htm", ".xhtml"}

# Default elements to remove from HTML before conversion
DEFAULT_REMOVE_ELEMENTS = ["script", "style", "iframe", "noscript"]

# Setup logger
logger = logging.getLogger("html_to_md")
file_handler = None
console_handler = None


# --- Helper Functions ---
def configure_logging(
    verbose: bool, 
    output_dir: Optional[Path] = None,
    quiet: bool = False
) -> None:
    """Configure logging settings based on verbosity level.
    
    Args:
        verbose: Whether to enable verbose (DEBUG) logging
        output_dir: Optional directory for log file output
        quiet: If True, suppress all console output
    """
    global file_handler, console_handler
    logger_instance = logging.getLogger("html_to_md")
    
    # Reset existing handlers
    for handler in logger_instance.handlers[:]:
        logger_instance.removeHandler(handler)
    
    # Set log level
    logger_instance.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger_instance.propagate = False
    
    # Configure console handler
    if not quiet:
        new_console_handler = logging.StreamHandler(sys.stdout)
        new_console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        console_formatter = logging.Formatter("%(levelname)-8s: %(message)s")
        new_console_handler.setFormatter(console_formatter)
        logger_instance.addHandler(new_console_handler)
        console_handler = new_console_handler
    
    # Configure file handler if output directory is provided
    if output_dir:
        try:
            log_file_path = output_dir / "html_to_md.log"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            new_file_handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
            new_file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter("%(asctime)s - %(levelname)-8s: %(message)s")
            new_file_handler.setFormatter(file_formatter)
            logger_instance.addHandler(new_file_handler)
            file_handler = new_file_handler
            
            if verbose:
                logger.debug(f"Log file created at: {log_file_path}")
        except Exception as e:
            logger.error(f"Failed to create log file: {e}")


def detect_encoding(file_path: Path) -> str:
    """Detect the character encoding of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Detected character encoding or 'utf-8' if detection fails
    """
    if not CHARDET_AVAILABLE:
        return "utf-8"
    
    try:
        # Check for BOM markers first
        with open(file_path, "rb") as f:
            raw_data = f.read(4)
            
        if not raw_data:
            return "utf-8"
            
        if raw_data.startswith(b"\xff\xfe"):
            return "utf-16-le"
        elif raw_data.startswith(b"\xfe\xff"):
            return "utf-16-be"
        elif raw_data.startswith(b"\xef\xbb\xbf"):
            return "utf-8-sig"
        
        # If no BOM found, use chardet for detection
        with open(file_path, "rb") as f:
            raw_data = f.read(min(65536, os.path.getsize(file_path)))
            
        result = chardet.detect(raw_data)
        
        if result["confidence"] < 0.7:
            return "utf-8"
            
        return result["encoding"].lower()
    except Exception as e:
        logger.warning(f"Error detecting encoding for {file_path}: {e}")
        return "utf-8"


def read_file_with_encoding(
    file_path: Path, target_encoding: Optional[str] = None
) -> Tuple[str, str]:
    """Read a file with its detected encoding or convert to target encoding.
    
    Args:
        file_path: Path to the file to read
        target_encoding: Target encoding to convert to, or None to keep original
        
    Returns:
        Tuple containing (file_content, used_encoding)
    """
    original_encoding = detect_encoding(file_path)
    used_encoding = original_encoding
    
    try:
        # Read the file with the detected encoding
        with open(file_path, "rb") as f:
            content_bytes = f.read()
            
        if not content_bytes:
            return "", used_encoding
            
        # Decode with the detected encoding
        try:
            content = content_bytes.decode(used_encoding)
        except UnicodeDecodeError:
            # Fallback to UTF-8 with replacement
            content = content_bytes.decode("utf-8", errors="replace")
            logger.warning(f"Encoding issues with {file_path}. Falling back to UTF-8 with replacement.")
            used_encoding = "utf-8"
            
        # Convert to target encoding if specified
        if target_encoding and target_encoding.lower() != used_encoding.lower():
            logger.debug(f"Converting {file_path} from {used_encoding} to {target_encoding}")
            # Re-encode using the target encoding
            content_bytes = content.encode(target_encoding, errors="replace")
            content = content_bytes.decode(target_encoding)
            used_encoding = target_encoding
            
        return content, used_encoding
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return f"[ERROR: Unable to read file {file_path}. Reason: {e}]", used_encoding


def adjust_internal_links(
    soup: BeautifulSoup, 
    link_extensions: Optional[Dict[str, str]] = None
) -> None:
    """Rewrite links to other files so they point to Markdown or other formats.
    
    Args:
        soup: BeautifulSoup object to modify
        link_extensions: Optional dictionary mapping source extensions to target extensions
    """
    if link_extensions is None:
        # Default is to convert HTML links to Markdown
        link_extensions = {".html": ".md", ".htm": ".md"}
    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        parsed = urlparse(href)
        
        # Skip external links or in-page anchors
        if parsed.scheme or href.startswith("#"):
            continue
            
        path = Path(parsed.path)
        suffix_lower = path.suffix.lower()
        
        # Check if this extension should be converted
        if suffix_lower in link_extensions:
            # Convert extension
            new_suffix = link_extensions[suffix_lower]
            new_path = path.with_suffix(new_suffix).as_posix()
            
            # Preserve fragment if present
            if parsed.fragment:
                new_path += f"#{parsed.fragment}"
                
            a["href"] = new_path


def create_frontmatter(
    title: Optional[str] = None,
    source_file: Optional[Path] = None,
    custom_fields: Optional[Dict] = None
) -> str:
    """Create YAML frontmatter for markdown files.
    
    Args:
        title: Optional title for the document
        source_file: Optional source file path for metadata
        custom_fields: Optional dictionary of custom frontmatter fields
        
    Returns:
        YAML frontmatter string
    """
    if not YAML_AVAILABLE:
        logger.warning("yaml module not available. Frontmatter will be created manually.")
    
    frontmatter = {}
    
    # Add title if provided
    if title:
        frontmatter["title"] = title
    
    # Add metadata from source file
    if source_file:
        try:
            stat = source_file.stat()
            frontmatter["source_file"] = str(source_file.name)
            frontmatter["date_converted"] = datetime.datetime.now().isoformat()
            frontmatter["date_modified"] = datetime.datetime.fromtimestamp(
                stat.st_mtime
            ).isoformat()
        except Exception as e:
            logger.warning(f"Error getting metadata from {source_file}: {e}")
    
    # Add custom fields
    if custom_fields:
        frontmatter.update(custom_fields)
    
    # Format frontmatter
    if YAML_AVAILABLE:
        yaml_text = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        return f"---\n{yaml_text}---\n\n"
    else:
        # Manual YAML creation
        yaml_lines = ["---"]
        for key, value in frontmatter.items():
            yaml_lines.append(f"{key}: {value}")
        yaml_lines.append("---")
        yaml_lines.append("")
        return "\n".join(yaml_lines)


def extract_title_from_html(soup: BeautifulSoup) -> Optional[str]:
    """Extract the title from HTML content.
    
    Args:
        soup: BeautifulSoup object of the HTML
        
    Returns:
        Title string or None if not found
    """
    # Look for title tag
    title_tag = soup.title
    if title_tag:
        return title_tag.get_text(strip=True)
    
    # Look for first h1 tag
    h1_tag = soup.find("h1")
    if h1_tag:
        return h1_tag.get_text(strip=True)
    
    # Look for meta title
    meta_title = soup.find("meta", {"name": "title"})
    if meta_title and meta_title.get("content"):
        return meta_title["content"]
    
    return None


def convert_html(
    html: str,
    outer_selector: str = "",
    ignore_selectors: Iterable[str] = None,
    remove_elements: Iterable[str] = None,
    heading_offset: int = 0,
    link_extensions: Optional[Dict[str, str]] = None,
    strip_classes: bool = True,
    add_line_breaks: bool = True,
    convert_code_blocks: bool = True
) -> str:
    """Convert HTML content to Markdown with advanced options.
    
    Args:
        html: HTML content to convert
        outer_selector: CSS selector for the outermost element to convert
        ignore_selectors: CSS selectors to remove from HTML before conversion
        remove_elements: HTML elements to remove before conversion
        heading_offset: Number to add to heading levels (e.g., h1 -> h2 if offset=1)
        link_extensions: Dictionary mapping source extensions to target extensions
        strip_classes: Whether to strip class attributes before conversion
        add_line_breaks: Whether to add line breaks between elements
        convert_code_blocks: Whether to convert code blocks with language hint
        
    Returns:
        Converted Markdown content
    """
    if ignore_selectors is None:
        ignore_selectors = []
        
    if remove_elements is None:
        remove_elements = DEFAULT_REMOVE_ELEMENTS
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove specified elements
    for tag_name in remove_elements:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    
    # Remove HTML comments
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()
    
    # Extract the specified content if outer_selector is provided
    root = soup
    if outer_selector:
        found = soup.select_one(outer_selector)
        if found:
            root = found
        else:
            logger.warning(f"Selector '{outer_selector}' not found. Using entire document.")
    
    # Remove elements matching ignore selectors
    for selector in ignore_selectors:
        for el in root.select(selector):
            el.decompose()
    
    # Process heading levels if offset is provided
    if heading_offset != 0:
        for i in range(1, 7):
            # Process headings in reverse order when increasing levels to avoid 
            # unintended cascading (e.g., h1 -> h2 -> h3)
            level = 7 - i if heading_offset > 0 else i
            new_level = min(6, max(1, level + heading_offset))
            
            if level != new_level:
                for heading in root.find_all(f"h{level}"):
                    # Create new tag with the adjusted level
                    new_tag = soup.new_tag(f"h{new_level}")
                    new_tag.string = heading.get_text()
                    heading.replace_with(new_tag)
    
    # Adjust internal links
    adjust_internal_links(root, link_extensions)
    
    # Strip class attributes if requested
    if strip_classes:
        for tag in root.find_all(True):
            if tag.has_attr("class"):
                del tag["class"]
    
    # Special handling for code blocks if requested
    if convert_code_blocks:
        for pre in root.find_all("pre"):
            code = pre.find("code")
            if code and code.has_attr("class"):
                # Extract language from class (e.g., "language-python" -> "python")
                classes = code["class"]
                lang = None
                for cls in classes:
                    if cls.startswith(("language-", "lang-")):
                        lang = cls.split("-", 1)[1]
                        break
                
                if lang:
                    # Add a language hint comment before the pre tag
                    pre.insert_before(soup.new_string(f"```{lang}"))
                    pre.insert_after(soup.new_string("```"))
                    # Remove the original pre and code tags but keep content
                    code.replace_with(code.get_text())
                    pre.replace_with(pre.get_text())
    
    # Extract content
    html_content = root.decode_contents()
    
    # Convert to Markdown
    md_options = {
        "heading_style": "ATX"  # Use # style headings
    }
    
    md_content = markdownify(html_content, **md_options)
    
    # Add line breaks between block elements if requested
    if add_line_breaks:
        # This is a simple approach - a more sophisticated approach would
        # analyze the markdown to identify block elements and ensure proper spacing
        md_content = md_content.replace("\n#", "\n\n#")  # Add space before headings
        md_content = md_content.replace("\n-", "\n\n-")  # Add space before lists
        md_content = md_content.replace("\n1.", "\n\n1.")  # Add space before ordered lists
        md_content = md_content.replace("\n---", "\n\n---")  # Add space before horizontal rules
    
    return md_content


def process_file(
    src: Path,
    dst: Path,
    options: Dict,
) -> Tuple[Path, Path, bool]:
    """Process a single HTML file to Markdown.
    
    Args:
        src: Source HTML file path
        dst: Destination Markdown file path
        options: Dictionary of conversion options
        
    Returns:
        Tuple of (source path, destination path, success status)
    """
    try:
        # Read file content
        html, encoding = read_file_with_encoding(src, options.get("target_encoding"))
        
        # Create BeautifulSoup object for title extraction (if needed for frontmatter)
        soup = BeautifulSoup(html, "html.parser")
        title = None
        
        if options.get("add_frontmatter"):
            title = extract_title_from_html(soup)
        
        # Convert HTML to Markdown
        md = convert_html(
            html,
            outer_selector=options.get("outermost_selector", ""),
            ignore_selectors=options.get("ignore_selectors", []),
            remove_elements=options.get("remove_elements", DEFAULT_REMOVE_ELEMENTS),
            heading_offset=options.get("heading_offset", 0),
            link_extensions=options.get("link_extensions"),
            strip_classes=options.get("strip_classes", True),
            add_line_breaks=options.get("add_line_breaks", True),
            convert_code_blocks=options.get("convert_code_blocks", True)
        )
        
        # Add frontmatter if requested
        if options.get("add_frontmatter"):
            custom_fields = options.get("frontmatter_fields", {})
            frontmatter = create_frontmatter(title, src, custom_fields)
            md = frontmatter + md
        
        # Ensure the destination directory exists
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to the destination file
        dst.write_text(md, encoding="utf-8")
        
        logger.debug(f"Converted: {src} -> {dst}")
        return src, dst, True
    except Exception as e:
        logger.error(f"Error processing {src}: {e}")
        return src, dst, False


def find_html_files(
    source_dir: Path,
    include_extensions: Set[str] = None,
    exclude_patterns: List[str] = None,
    exclude_dirs: List[str] = None,
) -> List[Path]:
    """Find HTML files in the source directory.
    
    Args:
        source_dir: Directory to search for HTML files
        include_extensions: Set of file extensions to include
        exclude_patterns: List of patterns to exclude
        exclude_dirs: List of directory names to exclude
        
    Returns:
        List of Path objects for HTML files
    """
    if include_extensions is None:
        include_extensions = HTML_EXTENSIONS
        
    if exclude_dirs is None:
        exclude_dirs = [".git", "node_modules", "__pycache__", "venv", ".venv"]
    
    html_files = []
    
    for ext in include_extensions:
        pattern = f"*{ext}"
        for file_path in source_dir.glob(f"**/{pattern}"):
            # Check if file is in an excluded directory
            if exclude_dirs:
                skip = False
                for parent in file_path.parents:
                    if parent.name in exclude_dirs:
                        skip = True
                        break
                if skip:
                    continue
            
            # Check against exclude patterns
            if exclude_patterns:
                skip = False
                for pattern in exclude_patterns:
                    if pattern in str(file_path):
                        skip = True
                        break
                if skip:
                    continue
            
            html_files.append(file_path)
    
    return html_files


def main() -> None:
    """Main entry point for the HTML to Markdown converter."""
    start_time = time.time()
    
    # Create a custom argument parser
    parser = argparse.ArgumentParser(
        description="Convert HTML files in a directory tree to Markdown",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument("--source-dir", required=True, 
                      help="Directory with HTML files")
    parser.add_argument("--destination-dir", required=True, 
                      help="Directory to write Markdown files")
    
    # Content selection options
    parser.add_argument("--outermost-selector", default="",
                      help="CSS selector for the outermost element to convert")
    parser.add_argument("--ignore-selectors", nargs="*", default=[],
                      help="CSS selectors to remove from the HTML before conversion")
    parser.add_argument("--remove-elements", nargs="*", default=DEFAULT_REMOVE_ELEMENTS,
                      help="HTML elements to remove before conversion")
    
    # Filter options
    parser.add_argument("--include-extensions", nargs="*", 
                      help="File extensions to include (default: .html, .htm, .xhtml)")
    parser.add_argument("--exclude-patterns", nargs="*", default=[],
                      help="Patterns to exclude from processing")
    parser.add_argument("--exclude-dirs", nargs="*", 
                      help="Directory names to exclude from processing")
    
    # Formatting options
    parser.add_argument("--heading-offset", type=int, default=0,
                      help="Number to add to heading levels (e.g., h1 -> h2 if offset=1)")
    parser.add_argument("--add-frontmatter", action="store_true",
                      help="Add YAML frontmatter to the output Markdown")
    parser.add_argument("--frontmatter-fields", nargs="*", 
                      help="Custom frontmatter fields (format: key=value)")
    parser.add_argument("--strip-classes", action="store_true", default=True,
                      help="Strip class attributes from HTML elements")
    parser.add_argument("--add-line-breaks", action="store_true", default=True,
                      help="Add line breaks between block elements")
    parser.add_argument("--convert-code-blocks", action="store_true", default=True,
                      help="Convert code blocks with language hint")
    
    # Encoding options
    parser.add_argument("--target-encoding", 
                      help="Convert all files to the specified character encoding")
    
    # Processing options
    parser.add_argument("--parallel", action="store_true",
                      help="Enable parallel processing for faster conversion")
    parser.add_argument("--max-workers", type=int, default=None,
                      help="Maximum number of worker processes for parallel conversion")
    
    # Output options
    parser.add_argument("--force", "-f", action="store_true",
                      help="Force overwrite of existing Markdown files")
    parser.add_argument("--verbose", "-v", action="store_true",
                      help="Enable verbose output")
    parser.add_argument("--quiet", "-q", action="store_true",
                      help="Suppress all console output")
    
    args = parser.parse_args()
    
    # Set up logging
    configure_logging(args.verbose, Path(args.destination_dir), args.quiet)
    
    # Set up source and destination directories
    src_root = Path(args.source_dir)
    dst_root = Path(args.destination_dir)
    
    if not src_root.exists() or not src_root.is_dir():
        logger.error(f"Source directory does not exist or is not a directory: {src_root}")
        sys.exit(1)
    
    # Create destination directory if it doesn't exist
    dst_root.mkdir(parents=True, exist_ok=True)
    
    # Process frontmatter fields if provided
    frontmatter_fields = {}
    if args.frontmatter_fields:
        for field in args.frontmatter_fields:
            if "=" in field:
                key, value = field.split("=", 1)
                frontmatter_fields[key.strip()] = value.strip()
    
    # Process include extensions
    include_extensions = set(HTML_EXTENSIONS)
    if args.include_extensions:
        include_extensions = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" 
                             for ext in args.include_extensions}
    
    # Find HTML files to process
    html_files = find_html_files(
        src_root,
        include_extensions=include_extensions,
        exclude_patterns=args.exclude_patterns,
        exclude_dirs=args.exclude_dirs
    )
    
    if not html_files:
        logger.warning(f"No HTML files found in {src_root}")
        sys.exit(0)
    
    logger.info(f"Found {len(html_files)} HTML files to process")
    
    # Create conversion options dictionary
    conversion_options = {
        "outermost_selector": args.outermost_selector,
        "ignore_selectors": args.ignore_selectors,
        "remove_elements": args.remove_elements,
        "heading_offset": args.heading_offset,
        "add_frontmatter": args.add_frontmatter,
        "frontmatter_fields": frontmatter_fields,
        "strip_classes": args.strip_classes,
        "add_line_breaks": args.add_line_breaks,
        "convert_code_blocks": args.convert_code_blocks,
        "target_encoding": args.target_encoding,
        "link_extensions": {".html": ".md", ".htm": ".md"}
    }
    
    # Process files
    success_count = 0
    error_count = 0
    
    if args.parallel:
        # Parallel processing
        with ProcessPoolExecutor(max_workers=args.max_workers) as executor:
            future_to_file = {}
            
            for html_file in html_files:
                rel = html_file.relative_to(src_root)
                dst_file = dst_root / rel
                dst_file = dst_file.with_suffix(".md")
                
                # Skip if destination exists and force is not specified
                if dst_file.exists() and not args.force:
                    logger.debug(f"Skipping existing file: {dst_file}")
                    continue
                
                # Submit task to the executor
                future = executor.submit(
                    process_file, html_file, dst_file, conversion_options
                )
                future_to_file[future] = html_file
            
            # Process completed tasks
            for future in as_completed(future_to_file):
                src, dst, success = future.result()
                if success:
                    success_count += 1
                else:
                    error_count += 1
    else:
        # Sequential processing
        for html_file in html_files:
            rel = html_file.relative_to(src_root)
            dst_file = dst_root / rel
            dst_file = dst_file.with_suffix(".md")
            
            # Skip if destination exists and force is not specified
            if dst_file.exists() and not args.force:
                logger.debug(f"Skipping existing file: {dst_file}")
                continue
            
            # Process the file
            _, _, success = process_file(html_file, dst_file, conversion_options)
            if success:
                success_count += 1
            else:
                error_count += 1
    
    # Calculate and log execution time
    end_time = time.time()
    execution_time = end_time - start_time
    
    if execution_time >= 60:
        minutes, seconds = divmod(execution_time, 60)
        time_str = f"{int(minutes)}m {seconds:.2f}s"
    else:
        time_str = f"{execution_time:.2f}s"
    
    logger.info(f"Conversion completed in {time_str}")
    logger.info(f"Successfully converted {success_count} files")
    
    if error_count > 0:
        logger.warning(f"Failed to convert {error_count} files")
    
    # Clean up handlers
    if file_handler:
        file_handler.close()
    if console_handler:
        console_handler.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
