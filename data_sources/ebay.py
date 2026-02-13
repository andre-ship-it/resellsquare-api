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
            "LH_Sold": "1",
            "LH_Complete": "1"
        }

        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            results = data.get('ebay_results', [])
            prices = []
            recent_sales = []

            for item in results[:10]:
                price = item.get('price', {}).get('extracted', 0)
                if price > 0:
                    prices.append(price)
                    recent_sales.append({
                        "title": item.get('title'),
                        "price": price,
                        "image": item.get('thumbnail'),
                        "link": item.get('link')
                    })

            if not prices:
                return {"success": False, "error": "No data found"}

            prices.sort()
            median = prices[len(prices)//2]

            # These fields are required to fix the "undefined" on your dashboard
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
