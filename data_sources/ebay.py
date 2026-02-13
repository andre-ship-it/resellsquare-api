import os
import requests
import base64
from statistics import median

class EbayDataSource:
    def __init__(self):
        # Using exact variable names from your Railway screenshots
        self.client_id = os.environ.get("EBAY_CLIENT_ID")
        self.client_secret = os.environ.get("EBAY_CLIENT_SECRET")
        self.endpoint = "https://svcs.ebay.com/services/search/FindingService/v1"

    def get_auth_token(self):
        """Fetches a fresh OAuth token from eBay Production."""
        url = "https://api.ebay.com/identity/v1/oauth2/token"
        
        # Prepare the Basic Auth header
        auth_str = f"{self.client_id}:{self.client_secret}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_auth}"
        }
        
        payload = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }
        
        try:
            res = requests.post(url, data=payload, headers=headers)
            return res.json().get("access_token")
        except Exception as e:
            print(f"OAuth Error: {e}")
            return None

    def fetch(self, query):
        token = self.get_auth_token()
        if not token:
            return {"success": False, "error": "Authentication Failed"}

        # Production Headers for Finding API
        headers = {
            "X-EBAY-SOA-SECURITY-APPNAME": self.client_id,
            "X-EBAY-SOA-AUTHENTICATION-TOKEN": token,
            "X-EBAY-SOA-OPERATION-NAME": "findCompletedItems",
            "X-EBAY-SOA-RESPONSE-DATA-FORMAT": "JSON",
            "X-EBAY-SOA-GLOBAL-ID": "EBAY-US"
        }

        params = {
            "SERVICE-VERSION": "1.13.0",
            "keywords": query,
            "itemFilter(0).name": "SoldItemsOnly",
            "itemFilter(0).value": "true",
            "paginationInput.entriesPerPage": "10",
            "sortOrder": "EndTimeSoonest"
        }

        try:
            response = requests.get(self.endpoint, params=params, headers=headers, timeout=10)
            data = response.json()
            
            # Access deep JSON structure
            res = data.get("findCompletedItemsResponse", [{}])[0]
            search_result = res.get("searchResult", [{}])[0]
            items = search_result.get("item", [])

            if not items:
                print(f"DEBUG: No items found for {query}")
                return {"success": False, "error": "No items found"}

            prices = []
            recent_sales = []

            for item in items:
                # Extract clean price
                p_val = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", 0)
                price = float(p_val)
                
                if price > 0:
                    prices.append(price)
                    recent_sales.append({
                        "title": item.get("title", [""])[0],
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
