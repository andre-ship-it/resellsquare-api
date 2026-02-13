import os
import requests
from statistics import median

class EbayDataSource:
    def __init__(self):
        # Matching your Railway variable name: EBAY_CLIENT_ID
        self.client_id = os.environ.get("EBAY_CLIENT_ID")
        self.endpoint = "https://svcs.ebay.com/services/search/FindingService/v1"

    def fetch(self, query):
        """
        Fetches live 'Sold' listings from eBay and calculates market metrics.
        """
        if not self.client_id:
            return {"success": False, "error": "EBAY_CLIENT_ID missing from environment."}

        params = {
            "OPERATION-NAME": "findCompletedItems",
            "SERVICE-VERSION": "1.13.0",
            "SECURITY-APPNAME": self.client_id, # This uses your 'AndreTim-...' ID
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "true",
            "keywords": query,
            # Filter for Sold/Completed items only
            "itemFilter(0).name": "SoldItemsOnly",
            "itemFilter(0).value": "true",
            "paginationInput.entriesPerPage": "10",
            "sortOrder": "EndTimeSoonest"
        }

        try:
            response = requests.get(self.endpoint, params=params, timeout=10)
            data = response.json()

            # Navigate the eBay JSON response
            search_response = data.get("findCompletedItemsResponse", [{}])[0]
            
            # Check if the API request was successful
            if search_response.get("ack", ["Failure"])[0] == "Failure":
                error_msg = search_response.get("errorMessage", [{}])[0].get("error", [{}])[0].get("message", ["Unknown API Error"])[0]
                return {"success": False, "error": f"eBay API: {error_msg}"}

            search_result = search_response.get("searchResult", [{}])[0]
            items = search_result.get("item", [])

            if not items:
                return {"success": False, "error": "No sold items found for this query."}

            recent_sales = []
            prices = []

            for item in items:
                title = item.get("title", ["Unknown"])[0]
                price_val = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", 0)
                price = float(price_val)
                
                if price <= 0: continue
                
                image = item.get("galleryURL", [""])[0]
                raw_date = item.get("listingInfo", [{}])[0].get("endTime", [""])[0]
                clean_date = raw_date.split("T")[0] if "T" in raw_date else "Recent"

                prices.append(price)
                recent_sales.append({
                    "title": title,
                    "price": price,
                    "date": clean_date,
                    "image": image
                })

            # Calculate actual market median from live prices
            market_median = round(median(prices), 2) if prices else 0

            return {
                "success": True,
                "metrics": {
                    "median": market_median,
                    "count": len(recent_sales)
                },
                "recent_sales": recent_sales
            }

        except Exception as e:
            print(f"Connection Error: {e}")
            return {"success": False, "error": "Could not connect to eBay server."}
