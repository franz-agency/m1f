"""HTML preprocessors for cleaning up content before conversion."""

from bs4 import BeautifulSoup, Comment
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class PreprocessingConfig:
    """Configuration for HTML preprocessing."""

    # Elements to completely remove
    remove_elements: List[str] = field(default_factory=lambda: ["script", "style"])

    # CSS selectors for elements to remove
    remove_selectors: List[str] = field(default_factory=list)

    # ID selectors for elements to remove
    remove_ids: List[str] = field(default_factory=list)

    # Class names for elements to remove
    remove_classes: List[str] = field(default_factory=list)

    # Comments containing these strings will be removed
    remove_comments_containing: List[str] = field(default_factory=list)

    # Text patterns to remove (regex)
    remove_text_patterns: List[str] = field(default_factory=list)

    # URL patterns to fix (from -> to)
    fix_url_patterns: Dict[str, str] = field(default_factory=dict)

    # Remove empty elements
    remove_empty_elements: bool = True

    # Custom processing function name
    custom_processor: Optional[str] = None


class GenericPreprocessor:
    """Generic HTML preprocessor based on configuration."""

    def __init__(self, config: PreprocessingConfig):
        self.config = config

    def preprocess(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Apply preprocessing based on configuration."""

        # Remove specified elements
        for tag_name in self.config.remove_elements:
            for tag in soup.find_all(tag_name):
                tag.extract()

        # Remove elements by CSS selector
        for selector in self.config.remove_selectors:
            for element in soup.select(selector):
                element.extract()

        # Remove elements by ID
        for element_id in self.config.remove_ids:
            element = soup.find(id=element_id)
            if element:
                element.extract()

        # Remove elements by class
        for class_name in self.config.remove_classes:
            for element in soup.find_all(class_=class_name):
                element.extract()

        # Remove comments containing specific text
        if self.config.remove_comments_containing:
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment_text = str(comment)
                for pattern in self.config.remove_comments_containing:
                    if pattern in comment_text:
                        comment.extract()
                        break

        # Remove text matching patterns
        if self.config.remove_text_patterns:
            for pattern in self.config.remove_text_patterns:
                regex = re.compile(pattern)
                for text in soup.find_all(string=regex):
                    if text.parent and text.parent.name not in ["script", "style"]:
                        text.replace_with("")

        # Fix URLs
        if self.config.fix_url_patterns:
            for tag in soup.find_all(["a", "link", "img", "script"]):
                for attr in ["href", "src"]:
                    if url := tag.get(attr):
                        for (
                            pattern,
                            replacement,
                        ) in self.config.fix_url_patterns.items():
                            if pattern in url:
                                tag[attr] = url.replace(pattern, replacement)

        # Remove empty elements
        if self.config.remove_empty_elements:
            # Multiple passes to catch nested empty elements
            for _ in range(3):
                for tag in soup.find_all():
                    if (
                        tag.name not in ["img", "br", "hr", "input", "meta", "link"]
                        and not tag.get_text(strip=True)
                        and not tag.find_all(
                            ["img", "table", "ul", "ol", "video", "audio", "iframe"]
                        )
                    ):
                        tag.extract()

        return soup


def preprocess_html(html_content: str, config: PreprocessingConfig) -> str:
    """Preprocess HTML content before conversion.

    Args:
        html_content: Raw HTML content
        config: Preprocessing configuration

    Returns:
        Cleaned HTML content
    """
    soup = BeautifulSoup(html_content, "html.parser")

    preprocessor = GenericPreprocessor(config)
    soup = preprocessor.preprocess(soup)

    return str(soup)
