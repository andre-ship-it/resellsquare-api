import os
import requests

class EbayDataSource:
    def __init__(self):
        # Fetches the API key you added to your Railway Variables
        self.api_key = os.environ.get('SERP_API_KEY')
        self.base_url = "https://serpapi.com/search.json"

    def fetch(self, query):
        """
        Fetches the last 10-20 verified 'Sold' listings from eBay via SerpApi.
        This bypasses the official eBay API authentication blocks.
        """
        if not self.api_key:
            return {"success": False, "error": "SERP_API_KEY is missing from Railway variables."}

        params = {
            "engine": "ebay",
            "_nkw": query,
            "ebay_domain": "ebay.com",
            "api_key": self.api_key,
            "LH_Sold": "1",        # Essential: Only shows items that actually sold
            "LH_Complete": "1",    # Essential: Shows completed auctions/listings
            "num": "20"             # Pulls enough data for a solid median average
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # SerpApi returns results in 'ebay_results'
            listings = data.get('ebay_results', [])
            prices = []
            recent_sales = []

            for item in listings:
                # Extract the numeric price (handles currency symbols automatically)
                price_data = item.get('price', {})
                extracted_price = price_data.get('extracted', 0.0)
                
                if extracted_price > 0:
                    prices.append(float(extracted_price))
                    # Build the Evidence Feed items
                    recent_sales.append({
                        "title": item.get('title'),
                        "price": extracted_price,
                        "image": item.get('thumbnail'),
                        "link": item.get('link')
                    })

            if not prices:
                return {"success": False, "error": f"No sold listings found for '{query}'."}

            # Calculate Median (Middle value) to avoid being skewed by outliers
            prices.sort()
            median = prices[len(prices)//2]

            # Return the exact structure needed by analysis.py and app.py
            return {
                "success": True,
                "metrics": {
                    "median": median,
                    "count": len(prices)
                },
                "recent_sales": recent_sales
            }

        except Exception as e:
            return {"success": False, "error": f"Connection Error: {str(e)}"}
