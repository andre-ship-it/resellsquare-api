"""
ResellSquare Web App - Synchronized Decision Assistant
"""
import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from cache import cache
from analysis import analyze_market_data

app = Flask(__name__)

# Config
USE_DEMO = os.environ.get("USE_DEMO", "false").lower() == "true"
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# Import correct data source
if USE_DEMO:
    from data_sources.demo import DemoDataSource
    data_source = DemoDataSource()
else:
    from data_sources.ebay import EbayDataSource
    data_source = EbayDataSource()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        
        # 1. Extract inputs
        search_term = data.get('query', '').strip()
        cost = float(data.get('cost_price', 0) or 0)
        shipping_cost = float(data.get('shipping_cost', 0) or 0)

        if not search_term:
            return jsonify({'success': False, 'error': 'No search term provided'}), 400

        # 2. Check Cache
        cache_key = f"market:{search_term.lower()}"
        market_data = cache.get(cache_key)

        if not market_data:
            # 3. Fetch fresh data (Sold Items only)
            market_data = data_source.fetch(search_term)
            if market_data.get('success'):
                cache.set(cache_key, market_data)

        # 4. Run the Consumer Decision Engine
        # This now returns action verdicts, pricing tiers, and colors
        analysis = analyze_market_data(market_data, cost=cost, shipping_cost=shipping_cost)

        # 5. Final Synchronized JSON for the Premium UI
        return jsonify({
            "success": True,
            "verdict": analysis['verdict'],
            "color_code": analysis['color_code'],
            "tip": analysis['tip'],
            "best_platform": analysis['best_platform'],
            "time_to_sell": analysis['time_to_sell'],
            "pricing_tiers": analysis['pricing_tiers'], # For Strategy Toggles
            "recent_sales": market_data.get('recent_sales', []), # For Evidence Feed
            "financials": {
                "profit": analysis.get('net_profit', 0),
                "roi": analysis.get('roi', 0)
            },
            "metrics": analysis['metrics']
        })

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
