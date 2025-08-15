"""Web scraper backends for HTML2MD."""

from typing import Dict, Type, Optional
from .base import WebScraperBase, ScraperConfig, ScrapedPage
from .beautifulsoup import BeautifulSoupScraper
from .httrack import HTTrackScraper

# Import new scrapers with error handling for optional dependencies
try:
    from .selectolax import SelectolaxScraper

    SELECTOLAX_AVAILABLE = True
except ImportError:
    SELECTOLAX_AVAILABLE = False
    SelectolaxScraper = None

# Scrapy removed - use other scrapers instead

try:
    from .playwright import PlaywrightScraper

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    PlaywrightScraper = None

__all__ = [
    "WebScraperBase",
    "ScraperConfig",
    "ScrapedPage",
    "create_scraper",
    "SCRAPER_REGISTRY",
    "BeautifulSoupScraper",
    "HTTrackScraper",
    "SelectolaxScraper",
    "PlaywrightScraper",
]

# Registry of available scraper backends
SCRAPER_REGISTRY: Dict[str, Type[WebScraperBase]] = {
    "beautifulsoup": BeautifulSoupScraper,
    "bs4": BeautifulSoupScraper,  # Alias
    "httrack": HTTrackScraper,
}

# Add optional scrapers if available
if SELECTOLAX_AVAILABLE:
    SCRAPER_REGISTRY["selectolax"] = SelectolaxScraper
    SCRAPER_REGISTRY["httpx"] = SelectolaxScraper  # Alias


if PLAYWRIGHT_AVAILABLE:
    SCRAPER_REGISTRY["playwright"] = PlaywrightScraper


def create_scraper(
    backend: str, config: Optional[ScraperConfig] = None
) -> WebScraperBase:
    """Factory function to create appropriate scraper instance.

    Args:
        backend: Name of the scraper backend to use
        config: Configuration for the scraper (uses defaults if not provided)

    Returns:
        Instance of the requested scraper backend

    Raises:
        ValueError: If the backend is not registered
    """
    if backend not in SCRAPER_REGISTRY:
        available = ", ".join(SCRAPER_REGISTRY.keys()) if SCRAPER_REGISTRY else "none"
        raise ValueError(
            f"Unknown scraper backend: {backend}. " f"Available backends: {available}"
        )

    if config is None:
        config = ScraperConfig()

    scraper_class = SCRAPER_REGISTRY[backend]
    return scraper_class(config)
