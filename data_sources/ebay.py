import os
import requests
import base64
from statistics import median

class EbayDataSource:
    def __init__(self):
        # Precise variable mapping to your Railway environment
        self.client_id = os.environ.get("EBAY_CLIENT_ID")
        self.client_secret = os.environ.get("EBAY_CLIENT_SECRET")
        self.endpoint = "https://svcs.ebay.com/services/search/FindingService/v1"

    def get_auth_token(self):
        """Generates a fresh OAuth Access Token using Client Credentials."""
        url = "https://api.ebay.com/identity/v1/oauth2/token"
        
        # Base64 encode ID:Secret for Basic Auth header
        auth_str = f"{self.client_id}:{self.client_secret}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_auth}"
        }
        
        # Requesting required scope for public market data
        payload = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }
        
        try:
            res = requests.post(url, data=payload, headers=headers, timeout=10)
            token_data = res.json()
            return token_data.get("access_token")
        except Exception as e:
            print(f"Token Error: {e}")
            return None

    def fetch(self, query):
        token = self.get_auth_token()
        if not token:
            return {"success": False, "error": "eBay Authentication Failed"}

        # Attempting 'Sold' data first, then falling back to 'Active' data
        for operation in ["findCompletedItems", "findItemsByKeywords"]:
            headers = {
                "X-EBAY-SOA-SECURITY-APPNAME": self.client_id,
                "X-EBAY-SOA-OPERATION-NAME": operation,
                "X-EBAY-SOA-RESPONSE-DATA-FORMAT": "JSON",
                "X-EBAY-SOA-GLOBAL-ID": "EBAY-US",
                # Pass OAuth token in standard Bearer format for Production stability
                "Authorization": f"Bearer {token}"
            }

            params = {
                "SERVICE-VERSION": "1.13.0",
                "keywords": query,
                "paginationInput.entriesPerPage": "10",
                "sortOrder": "PricePlusShippingLowest"
            }
            
            # Apply 'Sold' filter specifically for findCompletedItems
            if operation == "findCompletedItems":
                params["itemFilter(0).name"] = "SoldItemsOnly"
                params["itemFilter(0).value"] = "true"

            try:
                response = requests.get(self.endpoint, params=params, headers=headers, timeout=10)
                data = response.json()
                
                # Dynamic root key extraction
                root_key = f"{operation}Response"
                res = data.get(root_key, [{}])[0]
                
                # Check for successful item return
                search_result = res.get("searchResult", [{}])[0]
                items = search_result.get("item", [])

                if items:
                    # Mathematical analysis of market prices
                    prices = []
                    recent_sales = []

                    for i in items:
                        # Extract price regardless of currency
                        p_obj = i.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0]
                        price = float(p_obj.get("__value__", 0))
                        
                        if price > 0:
                            prices.append(price)
                            recent_sales.append({
                                "title": i.get("title", [""])[0],
                                "price": price,
                                "date": "LIVE" if operation == "findItemsByKeywords" else i.get("listingInfo", [{}])[0].get("endTime", [""])[0].split("T")[0],
                                "image": i.get("galleryURL", [""])[0]
                            })

                    return {
                        "success": True,
                        "metrics": {
                            "median": round(median(prices), 2) if prices else 0,
                            "count": len(recent_sales)
                        },
                        "recent_sales": recent_sales,
                        "source": "Sold Listings" if operation == "findCompletedItems" else "Active Listings"
                    }
            except Exception as e:
                print(f"Operation {operation} failed: {e}")
                continue

        return {"success": False, "error": "No data found for this product."}
