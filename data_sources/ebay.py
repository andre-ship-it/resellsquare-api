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
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            # --- CRITICAL DEBUGGING LINE ---
            if "error" in data:
                logger.error(f"SERPAPI ERROR: {data['error']}")
                return {"success": False, "error": data["error"]}
            
            listings = data.get('ebay_results', [])
            if not listings:
                logger.warning("SERPAPI WARNING: No ebay_results found in response")
                return {"success": False, "error": "No results found"}

            prices = []
            recent_sales = []
            for item in listings:
                price_val = item.get('price', {}).get('extracted', 0)
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
            logger.error(f"FETCH EXCEPTION: {str(e)}")
            return {"success": False, "error": str(e)}
