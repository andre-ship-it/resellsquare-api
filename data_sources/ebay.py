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
            "show_only": "sold",  # THIS IS THE KEY PARAMETER TO BYPASS BLOCKS
            "LH_Sold": "1",
            "LH_Complete": "1"
        }

        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            # Check if SerpApi returned an error or empty results
            if "error" in data:
                return {"success": False, "error": data["error"]}
                
            listings = data.get('ebay_results', [])
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

            if not prices:
                return {"success": False, "error": "No sold data found."}

            prices.sort()
            median = prices[len(prices)//2]

            return {
                "success": True,
                "metrics": {"median": median, "count": len(prices)},
                "recent_sales": recent_sales
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
