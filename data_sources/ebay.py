def fetch(self, query):
    # Use the specific 'ebay_search' engine parameters
    params = {
        "engine": "ebay",
        "_nkw": query,
        "ebay_domain": "ebay.com",
        "api_key": self.api_key,
        "listing_type": "sold", # Try this more direct filter
    }

    try:
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        # Check for search_metadata to see if the request actually worked
        if "error" in data:
            logger.error(f"SerpApi Error: {data['error']}")
            return {"success": False, "error": data["error"]}

        # SerpApi sometimes nests results under 'shopping_results' or 'ebay_results'
        listings = data.get('ebay_results', [])
        
        if not listings:
            # Fallback check: if 'ebay_results' is empty, look at the whole data object
            logger.warning(f"No results found for {query}. Keys present: {list(data.keys())}")
            return {"success": False, "error": "No sold listings found."}

        # ... (rest of your existing logic to calculate median and build recent_sales)
