import os
import requests

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
            "LH_Sold": "1", # Forces ONLY sold listings for accuracy
            "LH_Complete": "1"
        }

        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            listings = data.get('ebay_results', [])
            prices = []
            recent_sales = []

            for item in listings[:10]: # Get top 10 sold items
                price_data = item.get('price', {})
                raw_price = price_data.get('extracted', 0)
                if raw_price > 0:
                    prices.append(raw_price)
                    recent_sales.append({
                        "title": item.get('title'),
                        "price": raw_price,
                        "image": item.get('thumbnail'),
                        "link": item.get('link')
                    })

            if not prices:
                return {"success": False, "error": "No sold data found"}

            median_price = sorted(prices)[len(prices)//2]

            return {
                "success": True,
                "metrics": {
                    "median": median_price,
                    "count": len(prices)
                },
                "recent_sales": recent_sales
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
