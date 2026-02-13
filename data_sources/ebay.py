import os
import requests
import logging

logger = logging.getLogger(__name__)

class EbayDataSource:
    def __init__(self):
        self.api_key = os.environ.get('SERP_API_KEY')
        self.base_url = "https://serpapi.com/search.json"

    def fetch(self, query):
        """
        Fetches eBay data with an automatic fallback.
        1. Tries 'Sold' listings first for accuracy.
        2. Falls back to 'Active' listings if 'Sold' is blocked/empty.
        """
        # Strategy A: The "Sold" Search (Best for Resellers)
        params = {
            "engine": "ebay",
            "_nkw": query,
            "ebay_domain": "ebay.com",
            "api_key": self.api_key,
            "show_only": "sold",
            "LH_Sold": "1",
            "LH_Complete": "1"
        }

        try:
            logger.info(f"Attempting Sold search for: {query}")
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            # Key Change: SerpApi often labels results as 'organic_results'
            listings = data.get('ebay_results', []) or data.get('organic_results', [])

            # Strategy B: Fallback to Active Listings if Sold is empty
            if not listings:
                logger.warning(f"No Sold results for {query}. Trying Active listings fallback.")
                params.pop("show_only", None)
                params.pop("LH_Sold", None)
                response = requests.get(self.base_url, params=params)
                data = response.json()
                listings = data.get('ebay_results', []) or data.get('organic_results', [])

            if not listings:
                return {"success": False, "error": "No market data found on eBay."}

            prices = []
            recent_sales = []

            for item in listings[:15]:
                # Safe price extraction for SerpApi format
                price_data = item.get('price', {})
                price_val = price_data.get('extracted', 0)
                
                if price_val > 0:
                    prices.append(float(price_val))
                    recent_sales.append({
                        "title": item.get('title'),
                        "price": price_val,
                        "image": item.get('thumbnail'),
                        "link": item.get('link')
                    })

            prices.sort()
            median = prices[len(prices)//2] if prices else 0

            return {
                "success": True,
                "metrics": {"median": median, "count": len(prices)},
                "recent_sales": recent_sales
            }

        except Exception as e:
            logger.error(f"Ebay Data Source Error: {str(e)}")
            return {"success": False, "error": str(e)}
