import os
import logging
from openai import OpenAI
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class EbayDataSource:
    def __init__(self):
        # Uses your existing OpenAI key from Railway
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def fetch(self, query):
        """Uses an AI Agent to find sold prices via DuckDuckGo."""
        try:
            search_query = f"site:ebay.com {query} sold price"
            logger.info(f"Agent searching for: {search_query}")
            
            # 1. Get raw search results from the web
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(search_query, max_results=8):
                    results.append(f"Title: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}")

            if not results:
                return {"success": False, "error": "AI could not find web data."}

            # 2. Use OpenAI to extract the numbers from the text
            context = "\n---\n".join(results)
            prompt = f"""
            Extract exactly 5-10 recent sold prices for '{query}' from the text below.
            Return ONLY a comma-separated list of numbers. No currency symbols. 
            If no prices found, return '0'.
            Text: {context}
            """

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            price_str = response.choices[0].message.content.strip()
            # Clean and convert to float list
            prices = [float(p.strip()) for p in price_str.split(',') if p.strip().replace('.','',1).isdigit()]
            
            if not prices or sum(prices) == 0:
                return {"success": False, "error": "AI found no valid prices."}

            prices.sort()
            median = prices[len(prices)//2]

            # Return structure for analysis.py
            return {
                "success": True,
                "metrics": {"median": median, "count": len(prices)},
                "recent_sales": [{"title": "Web Result", "price": p} for p in prices]
            }

        except Exception as e:
            logger.error(f"Agent Error: {str(e)}")
            return {"success": False, "error": str(e)}
