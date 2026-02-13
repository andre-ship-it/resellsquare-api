import os
import requests
from statistics import median

class EbayDataSource:
    def __init__(self):
        self.client_id = os.environ.get("EBAY_CLIENT_ID") #
        self.client_secret = os.environ.get("EBAY_CLIENT_SECRET") #
        self.endpoint = "https://svcs.ebay.com/services/search/FindingService/v1"

    def get_access_token(self):
        """Fetches a fresh OAuth Application Access Token."""
        url = "https://api.ebay.com/identity/v1/oauth2/token"
        auth_str = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_str}"
        }
        
        payload = {"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}
        
        try:
            res = requests.post(url, data=payload, headers=headers)
            return res.json().get("access_token")
        except:
            return None

    def fetch(self, query):
        token = self.get_access_token() #
        if not token:
            return {"success": False, "error": "Auth Failed"}

        headers = {
            "X-EBAY-SOA-SECURITY-APPNAME": self.client_id, #
            "X-EBAY-SOA-AUTHENTICATION-TOKEN": token, #
            "X-EBAY-SOA-OPERATION-NAME": "findCompletedItems",
            "X-EBAY-SOA-RESPONSE-DATA-FORMAT": "JSON",
            "X-EBAY-SOA-GLOBAL-ID": "EBAY-US"
        }

        params = {
            "SERVICE-VERSION": "1.13.0",
            "keywords": query,
            "itemFilter(0).name": "SoldItemsOnly",
            "itemFilter(0).value": "true",
            "paginationInput.entriesPerPage": "10"
        }

        try:
            response = requests.get(self.endpoint, params=params, headers=headers)
            data = response.json()
            
            # ... (rest of logic to parse items and calculate median)
            # If searchResult count is "0", verify keywords or token scopes.
