import os
import requests
import logging

logger = logging.getLogger(__name__)

class EbayDataSource:
    def __init__(self):
        self.api_key = os.environ.get('SERP_API_KEY')
        self.base_url = "https://serpapi.com/search.json"

    def fetch(self, query):
        params = {
            "engine": "ebay",
            "_nkw": query,
            "ebay_domain": "ebay.com",
            "api_key": self.api_key,
            "LH_Sold": "1",
            "LH_Complete": "1"
        }

        try:
            logger.info(f"Connecting to SerpApi for: {query}")
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            # SerpApi often puts results in 'organic_results' for eBay
            listings = data.get('ebay_results', []) or data.get('organic_results', [])

            if not listings:
                logger.warning(f"No results found for {query}")
                return {"success": False, "error": "No market data found."}

            prices = []
            recent_sales = []

            for item in listings[:15]:
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
            logger.error(f"Ebay Fetch Error: {str(e)}")
            return {"success": False, "error": str(e)}
