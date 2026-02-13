import os
import requests

class EbayDataSource:
    def __init__(self):
        # Your new variable from Railway
        self.api_key = os.environ.get('SERP_API_KEY')
        self.base_url = "https://serpapi.com/search.json"

    def fetch(self, query):
        """Fetches 'Sold' listings using SerpApi."""
        params = {
            "engine": "ebay",
            "_nkw": query,
            "ebay_domain": "ebay.com",
            "api_key": self.api_key,
            "LH_Sold": "1",      # Filters for SOLD items only
            "LH_Complete": "1"   # Filters for COMPLETED items
        }

        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            # Extract listings from SerpApi response
            ebay_results = data.get('ebay_results', [])
            prices = []
            recent_sales = []

            for item in ebay_results[:12]:  # Collect up to 12 items
                price_info = item.get('price', {})
                extracted_price = price_info.get('extracted', 0)
                
                if extracted_price > 0:
                    prices.append(extracted_price)
                    recent_sales.append({
                        "title": item.get('title'),
                        "price": extracted_price,
                        "image": item.get('thumbnail'),
                        "link": item.get('link')
                    })

            if not prices:
                return {"success": False, "error": "No sold data found for this item."}

            # Calculate the median price for the intelligence engine
            prices.sort()
            median = prices[len(prices)//2]

            return {
                "success": True,
                "metrics": {
                    "median": median,
                    "count": len(prices)
                },
                "recent_sales": recent_sales
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
