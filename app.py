import os
from flask import Flask, render_template, request, jsonify
from cache import cache
from analysis import analyze_market_data

app = Flask(__name__)

# Config
USE_DEMO = os.environ.get("USE_DEMO", "false").lower() == "true"
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
        search_term = data.get('query', '').strip()
        cost = float(data.get('cost_price', 0) or 0)
        shipping_cost = float(data.get('shipping_cost', 0) or 0)

        # 1. Fetch
        cache_key = f"market:{search_term.lower()}"
        market_data = cache.get(cache_key)
        if not market_data:
            market_data = data_source.fetch(search_term)
            if market_data.get('success'):
                cache.set(cache_key, market_data)

        # 2. Analyze
        analysis = analyze_market_data(market_data, cost=cost, shipping_cost=shipping_cost)

        # 3. Synchronized Response
        return jsonify({
            "success": True,
            "verdict": analysis['verdict'],
            "color_code": analysis['color_code'],
            "best_platform": analysis['best_platform'],
            "time_to_sell": analysis['time_to_sell'],
            "pricing_tiers": analysis['pricing_tiers'],
            "recent_sales": market_data.get('recent_sales', []),
            "financials": {
                "profit": analysis['net_profit'],
                "roi": analysis['roi']
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
