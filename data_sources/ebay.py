import requests
import os
import urllib.parse

class EbayDataSource:
    def __init__(self):
        self.client_id = os.environ.get("EBAY_CLIENT_ID", "")
        self.client_secret = os.environ.get("EBAY_CLIENT_SECRET", "")
        self.token = None

    def get_token(self):
        """Fetch application access token (Client Credentials Grant)"""
        url = "https://api.ebay.com/identity/v1/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }
        
        try:
            resp = requests.post(url, data=data, auth=(self.client_id, self.client_secret))
            if resp.status_code == 200:
                self.token = resp.json().get("access_token")
                return self.token
            print(f"Token Error: {resp.text}")
            return None
        except Exception as e:
            print(f"Auth Exception: {e}")
            return None

    def fetch(self, query):
        """
        Search for sold items on eBay
        Returns normalized dictionary for analysis.py
        """
        if not self.token:
            self.get_token()
            
        if not self.token:
            return {'success': False, 'error': 'Failed to authenticate with eBay'}

        # Encode query
        encoded_query = urllib.parse.quote(query)
        
        # Search for SOLD items (completed + sold)
        # itemFilter.name=SoldItemsOnly&itemFilter.value=true
        url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
        
        params = {
            'q': query,
            'limit': 50,
            'sort': '-price', # Sort by price (high to low) to grab range, or -date
            'filter': 'buyingOptions:{FIXED_PRICE|BEST_OFFER},deliveryCountry:US,price:[5..5000],priceCurrency:USD'
        }
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }

        try:
            # Note: The Browse API doesn't support "sold items" filtering directly in the same way 
            # Finding API did. For a real production app, you often need the Finding API (Legacy) 
            # or to scrape. For this MVP, we will search *current* active listings 
            # as a proxy, OR use the "completed" filter if available.
            #
            # HACK for MVP: We will stick to searching active listings for now 
            # to verify the pipeline works, since Browse API 'sold' filtering is complex.
            
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            if 'itemSummaries' not in data:
                return {'success': False, 'error': 'No items found', 'listings': []}
                
            listings = []
            for item in data['itemSummaries']:
                price_str = item.get('price', {}).get('value', '0')
                title = item.get('title', 'No Title')
                condition = item.
