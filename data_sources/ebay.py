def fetch(self, query):
    token = self.get_auth_token()
    if not token:
        return {"success": False, "error": "Auth Failed"}

    # We will try 'findCompletedItems' (Sold) first
    # If that fails, we automatically try 'findItemsByKeywords' (Active)
    for operation in ["findCompletedItems", "findItemsByKeywords"]:
        headers = {
            "X-EBAY-SOA-SECURITY-APPNAME": self.client_id,
            "X-EBAY-SOA-AUTHENTICATION-TOKEN": token,
            "X-EBAY-SOA-OPERATION-NAME": operation,
            "X-EBAY-SOA-RESPONSE-DATA-FORMAT": "JSON",
            "X-EBAY-SOA-GLOBAL-ID": "EBAY-US"
        }

        params = {
            "SERVICE-VERSION": "1.13.0",
            "keywords": query,
            "paginationInput.entriesPerPage": "10"
        }
        
        # Add the 'Sold' filter only for the first attempt
        if operation == "findCompletedItems":
            params["itemFilter(0).name"] = "SoldItemsOnly"
            params["itemFilter(0).value"] = "true"

        try:
            response = requests.get(self.endpoint, params=params, headers=headers, timeout=10)
            data = response.json()
            
            # Access the correct response key based on operation
            root_key = f"{operation}Response"
            res = data.get(root_key, [{}])[0]
            items = res.get("searchResult", [{}])[0].get("item", [])

            if items:
                prices = [float(i.get("sellingStatus",[{}])[0].get("currentPrice",[{}])[0].get("__value__", 0)) for i in items]
                recent_sales = [{
                    "title": i.get("title",[""])[0],
                    "price": float(i.get("sellingStatus",[{}])[0].get("currentPrice",[{}])[0].get("__value__", 0)),
                    "date": "Live" if operation == "findItemsByKeywords" else i.get("listingInfo",[{}])[0].get("endTime",[""])[0].split("T")[0],
                    "image": i.get("galleryURL",[""])[0]
                } for i in items]

                return {
                    "success": True,
                    "metrics": {"median": round(median(prices), 2), "count": len(recent_sales)},
                    "recent_sales": recent_sales,
                    "source": "Sold" if operation == "findCompletedItems" else "Active"
                }
        except:
            continue

    return {"success": False, "error": "No data found on eBay"}
