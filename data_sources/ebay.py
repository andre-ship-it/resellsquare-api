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
        self.sold_terms = ("sold", "completed", "ended")

    def _is_generic_ebay_title(self, title):
        lowered = (title or "").strip().lower()
        generic_phrases = (
            "for sale | ebay",
            "for sale - ebay",
            "shop on ebay",
            "on ebay",
        )
        return any(phrase in lowered for phrase in generic_phrases)

    def _is_likely_listing_url(self, href):
        lowered = (href or "").lower()
        return "/itm/" in lowered or "/p/" in lowered

    def _trim_outliers(self, sales):
        if len(sales) < 6:
            return sales

        sorted_prices = sorted(sale["price"] for sale in sales)
        n = len(sorted_prices)
        q1 = sorted_prices[n // 4]
        q3 = sorted_prices[(3 * n) // 4]
        iqr = q3 - q1
        if iqr <= 0:
            return sales

        lower_bound = max(0.0, q1 - (1.5 * iqr))
        upper_bound = q3 + (1.5 * iqr)
        filtered = [
            sale for sale in sales if lower_bound <= sale["price"] <= upper_bound
        ]
        # Avoid over-filtering small sets.
        return filtered if len(filtered) >= 5 else sales

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
        # Apply outlier filtering before median/count metrics.
        recent_sales = self._trim_outliers(recent_sales)
        prices = sorted(sale["price"] for sale in recent_sales)
        median = prices[len(prices) // 2]
        normalized_sales = []
        for sale in recent_sales[:20]:
            normalized_sales.append(
                {
                    "title": sale.get("title", "Sale"),
                    "price": float(sale.get("price", 0) or 0),
                    "date": sale.get("date") or "Recent",
                    "image": sale.get("image"),
                }
            )
        return {
            "success": True,
            "metrics": {"median": median, "count": len(prices)},
            "recent_sales": normalized_sales,
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
            if not title or self._is_generic_ebay_title(title):
                continue

            price_text = price_el.get_text(" ", strip=True)
            # Skip listing ranges (e.g., "$7.25 to $250.00") to avoid noisy mixed comps.
            if " to " in price_text.lower():
                continue

            money_values = self._parse_money_values(price_text)
            if not money_values:
                continue

            price = money_values[0]
            prices.append(price)
            sold_meta = item.get_text(" ", strip=True).lower()
            date_label = "Sold" if any(t in sold_meta for t in self.sold_terms) else "Recent"
            sales.append({"title": title, "price": price, "date": date_label})

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

                        if self._is_generic_ebay_title(title):
                            continue
                        if not self._is_likely_listing_url(href):
                            continue

                        combined = f"{title} {body}"
                        lowered = combined.lower()
                        if not any(term in lowered for term in self.sold_terms):
                            continue

                        values = self._parse_money_values(combined)
                        for value in values:
                            prices.append(value)
                            sales.append(
                                {"title": title or "DDG Sale", "price": value, "date": "Sold"}
                            )
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
