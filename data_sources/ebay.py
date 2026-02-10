"""
eBay data source for ResellSquare
Uses eBay Browse API (official API) to fetch sold/completed listing data
"""

import os
import requests
import base64
import time


class EbayDataSource:
    """Data source that fetches real eBay data via the Browse API"""

    def __init__(self):
        self.app_id = os.environ.get("EBAY_APP_ID", "")
        self.cert_id = os.environ.get("EBAY_CERT_ID", "")
        self.access_token = None
        self.token_expiry = 0

    def _get_oauth_token(self):
        """Get OAuth token using Client Credentials grant"""
        if self.access_token and time.time() < self.token_expiry:
            return self.access_token

        credentials = base64.b64encode(
            f"{self.app_id}:{self.cert_id}".encode()
        ).decode()

        try:
            resp = requests.post(
                "https://api.ebay.com/identity/v1/oauth2/token",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {credentials}",
                },
                data={
                    "grant_type": "client_credentials",
                    "scope": "https://api.ebay.com/oauth/api_scope",
                },
                timeout=10,
            )
            resp.raise_for_status()
            token_data = resp.json()
            self.access_token = token_data["access_token"]
            self.token_expiry = time.time() + token_data.get("expires_in", 7200) - 60
            return self.access_token
        except Exception as e:
            return None

    def fetch(self, search_term: str) -> dict:
        """
        Fetch eBay listing data for a search term using Browse API.
        Returns data in the format expected by app.py
        """
        token = self._get_oauth_token()
        if not token:
            return {
                "status": "error",
                "search_term": search_term,
                "error": "Failed to authenticate with eBay API",
                "titles": [],
                "prices": [],
            }

        try:
            resp = requests.get(
                "https://api.ebay.com/buy/browse/v1/item_summary/search",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
                    "X-EBAY-C-ENDUSERCTX": "affiliateCampaignId=<ePNCampaignId>,affiliateReferenceId=<referenceId>",
                },
                params={
                    "q": search_term,
                    "filter": "buyingOptions:{FIXED_PRICE},conditions:{NEW|USED|VERY_GOOD|GOOD|ACCEPTABLE}",
                    "sort": "newlyListed",
                    "limit": "50",
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            items = data.get("itemSummaries", [])
            if not items:
                return {
                    "status": "error",
                    "search_term": search_term,
                    "error": "No listings found - try a different search term",
                    "titles": [],
                    "prices": [],
                }

            titles = []
            prices = []
            conditions = []
            for item in items:
                title = item.get("title", "")
                price_info = item.get("price", {})
                price_val = price_info.get("value")
                if title and price_val:
                    try:
                        price = float(price_val)
                        if 0.01 < price < 100000:
                            titles.append(title[:100])
                            prices.append(price)
                            cond = item.get("condition", "")
                            conditions.append(cond)
                    except (ValueError, TypeError):
                        continue

            if not prices:
                return {
                    "status": "error",
                    "search_term": search_term,
                    "error": "No valid pricing data found",
                    "titles": [],
                    "prices": [],
                }

            return {
                "status": "ok",
                "search_term": search_term,
                "titles": titles,
                "prices": prices,
                "conditions": conditions,
            }

        except requests.exceptions.HTTPError as e:
            error_msg = f"eBay API error: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                errors = error_detail.get("errors", [])
                if errors:
                    error_msg = f"eBay API: {errors[0].get('message', str(e))}"
            except Exception:
                pass
            return {
                "status": "error",
                "search_term": search_term,
                "error": error_msg,
                "titles": [],
                "prices": [],
            }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "search_term": search_term,
                "error": "eBay API request timed out",
                "titles": [],
                "prices": [],
            }
        except Exception as e:
            return {
                "status": "error",
                "search_term": search_term,
                "error": f"Error fetching eBay data: {str(e)}",
                "titles": [],
                "prices": [],
            }
