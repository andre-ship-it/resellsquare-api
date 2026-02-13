import os
import logging
from flask import Flask, render_template, request, jsonify
from data_sources.ebay import EbayDataSource
from analysis import ResellAnalyzer

# Setup logging to see eBay's raw response in Railway
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize components
ebay = EbayDataSource()
analyzer = ResellAnalyzer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    """Handles product search and decision intelligence."""
    try:
        data = request.json
        query = data.get('query')
        cost_price = float(data.get('cost_price', 0) or 0)
        shipping_cost = float(data.get('shipping_cost', 0) or 0)

        if not query:
            return jsonify({"success": False, "error": "No query provided"}), 400

        # 1. Fetch live market data from SerpApi
        market_data = ebay.fetch(query)
        
        # Log the data to Railway so we can see why it's $0.00
        logger.info(f"Search Query: {query}")
        logger.info(f"Market Data Success: {market_data.get('success')}")
        logger.info(f"Median Found: {market_data.get('metrics', {}).get('median')}")

        if not market_data.get('success'):
            return jsonify(market_data), 200

        # 2. Run decision intelligence logic
        analysis = analyzer.analyze(
            market_data=market_data,
            cost_price=cost_price,
            shipping_cost=shipping_cost
        )

        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Search Error: {str(e)}")
        return jsonify({"success": False, "error": "Internal Server Error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
