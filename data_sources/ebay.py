import os
import requests
from statistics import median

class EbayDataSource:
    def __init__(self):
        # Using the exact variable name from your Railway screenshot
        self.client_id = os.environ.get("EBAY_CLIENT_ID")
        self.endpoint = "https://svcs.ebay.com/services/search/FindingService/v1"

    def fetch(self, query):
        if not self.client_id:
            return {"success": False, "error": "EBAY_CLIENT_ID missing."}

        # Headers are often required for Production (PRD) keys to validate the request
        headers = {
            "X-EBAY-SOA-SECURITY-APPNAME": self.client_id,
            "X-EBAY-SOA-OPERATION-NAME": "findCompletedItems",
            "X-EBAY-SOA-RESPONSE-DATA-FORMAT": "JSON"
        }

        params = {
            "SERVICE-VERSION": "1.13.0",
            "SECURITY-APPNAME": self.client_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "true",
            "keywords": query,
            "itemFilter(0).name": "SoldItemsOnly",
            "itemFilter(0).value": "true",
            "paginationInput.entriesPerPage": "10"
        }

        try:
            # Using both headers and params for maximum compatibility with PRD keys
            response = requests.get(self.endpoint, params=params, headers=headers, timeout=10)
            data = response.json()

            # Navigate deep eBay JSON
            res = data.get("findCompletedItemsResponse", [{}])[0]
            
            # Check if API actually returned items
            search_result = res.get("searchResult", [{}])[0]
            items = search_result.get("item", [])

            if not items:
                print(f"DEBUG: eBay returned 0 items for {query}")
                return {"success": False, "error": "No items found"}

            prices = []
            recent_sales = []

            for item in items:
                p_val = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", 0)
                price = float(p_val)
                if price > 0:
                    prices.append(price)
                    recent_sales.append({
                        "title": item.get("title", ["Unknown"])[0],
                        "price": price,
                        "date": item.get("listingInfo", [{}])[0].get("endTime", [""])[0].split("T")[0],
                        "image": item.get("galleryURL", [""])[0]
                    })

            market_median = round(median(prices), 2) if prices else 0

            return {
                "success": True,
                "metrics": {"median": market_median, "count": len(recent_sales)},
                "recent_sales": recent_sales
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
