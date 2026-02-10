"""
eBay data source for ResellSquare
Wraps the EbayScraper to provide real sold listing data
"""

import sys
import os

# Add parent directory to path so we can import scraper
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper import EbayScraper


class EbayDataSource:
    """Data source that fetches real eBay sold listing data"""

    def __init__(self):
        self.scraper = EbayScraper()

    def fetch(self, search_term: str) -> dict:
        """
        Fetch real eBay sold listing data for a search term.
        Returns data in the format expected by app.py
        """
        result = self.scraper.scrape(search_term)

        if not result.get('success', False):
            return {
                'status': 'error',
                'search_term': search_term,
                'error': result.get('error', 'Failed to fetch eBay data'),
                'titles': [],
                'prices': []
            }

        # Extract titles and prices from recent_sales
        titles = [sale['title'] for sale in result.get('recent_sales', [])]
        prices = [sale['price'] for sale in result.get('recent_sales', [])]

        return {
            'status': 'ok',
            'search_term': search_term,
            'titles': titles,
            'prices': prices
        }
