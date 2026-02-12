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
        url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
        
        params = {
            'q': query,
            'limit': 50,
            'sort': '-price',
            'filter': 'buyingOptions:{FIXED_PRICE|BEST_OFFER},deliveryCountry:US,price:[5..5000],priceCurrency:USD'
        }
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            if 'itemSummaries' not in data:
                return {'success': False, 'error': 'No items found', 'listings': []}
                
            listings = []
            for item in data['itemSummaries']:
                price_str = item.get('price', {}).get('value', '0')
                title = item.get('title', 'No Title')
                condition = item.get('condition', 'Used')
                
                listings.append({
                    'title': title,
                    'price': float(price_str),
                    'condition': condition,
                    'date': '2024-01-01'
                })
                
            return {
                'success': True,
                'listings': listings,
                'source': 'ebay_api'
            }

        except Exception as e:
            print(f"eBay API Error: {e}")
            return {'success': False, 'error': str(e)}
