import logging
import re
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


class EbayDataSource:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        self.money_pattern = re.compile(r"\$\s?(\d[\d,]*(?:\.\d{1,2})?)")

    def _parse_money_values(self, text):
        values = []
        for token in self.money_pattern.findall(text or ""):
            try:
                value = float(token.replace(",", ""))
                if value > 0:
                    values.append(value)
            except ValueError:
                continue
        return values

    def _build_success(self, prices, recent_sales):
        prices = sorted(prices)
        median = prices[len(prices) // 2]
        return {
            "success": True,
            "metrics": {"median": median, "count": len(prices)},
            "recent_sales": recent_sales[:20],
        }

    def _fetch_from_ebay_html(self, query):
        url = (
            "https://www.ebay.com/sch/i.html"
            f"?_nkw={quote_plus(query)}&LH_Sold=1&LH_Complete=1&rt=nc"
        )
        response = self.session.get(url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        prices = []
        sales = []
        for item in soup.select("li.s-item"):
            title_el = item.select_one(".s-item__title")
            price_el = item.select_one(".s-item__price")
            if not title_el or not price_el:
                continue

            title = title_el.get_text(" ", strip=True)
            if not title or "Shop on eBay" in title:
                continue

            money_values = self._parse_money_values(price_el.get_text(" ", strip=True))
            if not money_values:
                continue

            price = money_values[0]
            prices.append(price)
            sales.append({"title": title, "price": price})

            if len(prices) >= 20:
                break

        return prices, sales

    def _fetch_from_ddg(self, query):
        query_variants = [
            f'site:ebay.com "{query}" sold',
            f'site:ebay.com "{query}" completed listings',
            f"ebay sold {query}",
        ]
        logger.info(f"Agent searching DDG query variants: {query_variants}")

        prices = []
        sales = []
        seen = set()
        for search_query in query_variants:
            try:
                with DDGS() as ddgs:
                    for r in ddgs.text(search_query, max_results=25):
                        title = (r.get("title") or "").strip()
                        body = (r.get("body") or "").strip()
                        href = (r.get("href") or "").strip()
                        dedupe_key = (title.lower(), href.lower())
                        if dedupe_key in seen:
                            continue
                        seen.add(dedupe_key)

                        combined = f"{title} {body}"
                        values = self._parse_money_values(combined)
                        for value in values:
                            prices.append(value)
                            sales.append({"title": title or "DDG Sale", "price": value})
                if len(prices) >= 12:
                    break
            except Exception as search_error:
                logger.warning(f"DDG search attempt failed for '{search_query}': {search_error}")

        return prices, sales

    def fetch(self, query):
        """Deterministic: eBay sold HTML first, DDG regex second."""
        try:
            ebay_prices, ebay_sales = self._fetch_from_ebay_html(query)
            if len(ebay_prices) >= 5:
                return self._build_success(ebay_prices, ebay_sales)

            ddg_prices, ddg_sales = self._fetch_from_ddg(query)
            if len(ddg_prices) >= 5:
                return self._build_success(ddg_prices, ddg_sales)

            combined_prices = ebay_prices + ddg_prices
            combined_sales = ebay_sales + ddg_sales
            if combined_prices:
                return self._build_success(combined_prices, combined_sales)

            return {
                "success": False,
                "error": "No sold price data found from eBay HTML or DDG parsing.",
            }

        except Exception as e:
            logger.error(f"Agentic Fetch Error: {str(e)}")
            return {"success": False, "error": str(e)}
