from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable

class Scraper(ABC):
    """
    Abstract Base Class for Spotify scraping engines.
    Ensures that both Selenium and Playwright implementations provide a consistent API.
    """

    @abstractmethod
    def scrape_track(self, url: str, headless: bool = True, log_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        """Scrape metadata for a single track."""
        pass

    @abstractmethod
    def scrape_album(self, url: str, headless: bool = True, log_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        """Scrape metadata for an album."""
        pass

    @abstractmethod
    def scrape_playlist(self, url: str, headless: bool = True, log_callback: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
        """Scrape metadata for a playlist."""
        pass
