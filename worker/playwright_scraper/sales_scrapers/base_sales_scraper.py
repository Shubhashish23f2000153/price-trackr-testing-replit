from playwright.sync_api import Page
from typing import List, Dict, Any
from abc import ABC, abstractmethod

class BaseSalesScraper(ABC):
    """
    Base class for a dedicated sales scraper.
    Each scraper should find and return a list of sale data dictionaries.
    """
    def __init__(self, user_agent: str):
        self.user_agent = user_agent

    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Implementation for scraping a specific site's deals page.
        
        Returns:
            List[Dict[str, Any]]: A list of sale objects, where each object
                                  matches the SaleCreate schema.
        """
        pass