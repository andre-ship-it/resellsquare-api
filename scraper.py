"""
ResellSquare eBay Scraper
Clean, working implementation with anti-bot measures
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import re
from typing import Dict, List

class EbayScraper:
    """Scrapes eBay sold listings for pricing data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.ebay.com/sch/i.html"
        
    def _get_headers(self) -> dict:
        """Returns realistic browser headers"""
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
    
    def _build_url(self, search_term: str, max_results: int = 50) -> str:
        """Build eBay sold listings URL"""
        params = {
            '_nkw': search_term,
            'LH_Sold': '1',
            'LH_Complete': '1',
            '_ipg': str(max_results)
        }
        
        query_string = '&'.join([f"{k}={v.replace(' ', '+')}" for k, v in params.items()])
        return f"{self.base_url}?{query_string}"
    
    def _extract_price(self, price_text: str) -> float:
        """Extract numeric price from text"""
        try:
            price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                price = float(price_str)
                if 0.01 < price < 100000:
                    return price
        except (ValueError, AttributeError):
            pass
        return None
    
    def scrape(self, search_term: str) -> Dict:
        """Scrape eBay sold listings for a product"""
        
        time.sleep(random.uniform(2, 4))
        
        url = self._build_url(search_term)
        
        try:
            response = self.session.get(url, headers=self._get_headers(), timeout=15)
            response.raise_for_status()
            
            if 'Pardon Our Interruption' in response.text or 'captcha' in response.text.lower():
                return {
                    'success': False,
                    'error': 'Blocked by eBay - please try again in a few minutes',
                    'search_term': search_term
                }
            
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select("li.s-item")
            
            prices = []
            titles = []
            
            for item in items:
                title_elem = item.select_one(".s-item__title")
                if not title_elem or "Shop on eBay" in title_elem.get_text():
                    continue
                
                price_elem = item.select_one(".s-item__price")
                if price_elem:
                    price = self._extract_price(price_elem.get_text(strip=True))
                    if price:
                        prices.append(price)
                        titles.append(title_elem.get_text(strip=True)[:100])
            
            if not prices:
                return {
                    'success': False,
                    'error': 'No sold listings found - try a different search term',
                    'search_term': search_term
                }
            
            avg_price = sum(prices) / len(prices)
            
            return {
                'success': True,
                'search_term': search_term,
                'count': len(prices),
                'avg_price': round(avg_price, 2),
                'min_price': round(min(prices), 2),
                'max_price': round(max(prices), 2),
                'median_price': round(sorted(prices)[len(prices)//2], 2),
                'recent_sales': [
                    {'title': titles[i], 'price': prices[i]} 
                    for i in range(min(5, len(prices)))
                ]
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'search_term': search_term
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Scraping error: {str(e)}',
                'search_term': search_term
            }
