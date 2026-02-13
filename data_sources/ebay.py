import os
import requests
import logging

logger = logging.getLogger(__name__)

class EbayDataSource:
    def __init__(self):
        self.api_key = os.environ.get('SERP_API_KEY')
        self.base_url = "https://serpapi.com/search.json"

    def fetch(self, query):
        """Minimal fetch to verify any data is coming from SerpApi."""
        params = {
            "engine": "ebay",
            "_nkw": query,
            "api_key": self.api_key
        }

        try:
            logger.info(f"Connecting to SerpApi for query: {query}")
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            # Check for API-level errors (e.g., invalid key)
            if "error" in data:
                logger.error(f"SERPAPI ERROR: {data['error']}")
                return {"success": False, "error": data["error"]}
            
            # Use 'organic_results' as a fallback if 'ebay_results' is missing
            listings = data.get('ebay_results', []) or data.get('organic_results', [])
            
            if not listings:
                logger.warning(f"No results found for {query}. Full response keys: {list(data.keys())}")
                return {"success": False, "error": "No listings found."}

            prices = []
            recent_sales = []

            for item in listings:
                # Use .get() to safely access price data
                price_data = item.get('price', {})
                # SerpApi sometimes returns a raw string or an 'extracted' float
                price_val = price_data.get('extracted', 0)
                
                if price_val > 0:
                    prices.append(float(price_val))
                    recent_sales.append({
                        "title": item.get('title'),
                        "price": price_val,
                        "image": item.get('thumbnail'),
                        "link": item.get('link')
                    })

            # Calculate a basic median if any prices exist
            prices.sort()
            median = prices[len(prices)//2] if prices else 0

            return {
                "success": True,
                "metrics": {"median": median, "count": len(prices)},
                "recent_sales": recent_sales
            }

        except Exception as e:
            logger.error(f"FETCH EXCEPTION: {str(e)}")
            return {"success": False, "error": str(e)}
