import os
import base64
from flask import Flask, render_template, request, jsonify
from cache import cache
from analysis import analyze_market_data

# Note: You would typically use 'google-cloud-vision' or 'openai' here
# For this example, we'll structure the vision logic for an API-based service
import requests 

app = Flask(__name__)

# Config
USE_DEMO = os.environ.get("USE_DEMO", "false").lower() == "true"
VISION_API_KEY = os.environ.get("VISION_API_KEY")

if USE_DEMO:
    from data_sources.demo import DemoDataSource
    data_source = DemoDataSource()
else:
    from data_sources.ebay import EbayDataSource
    data_source = EbayDataSource()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/identify-image', methods=['POST'])
def identify_image():
    """
    Receives base64 image, sends to Vision API, returns identified text.
    """
    try:
        data = request.get_json()
        image_data = data.get('image') # Base64 string from frontend

        if not image_data:
            return jsonify({'success': False, 'error': 'No image provided'}), 400

        # In a real implementation, you would send image_data to a Vision API.
        # Example using a placeholder for Google Vision/OpenAI:
        # identified_product = call_vision_api(image_data)
        
        # DEMO FALLBACK:
        identified_product = "Vintage Sony Walkman WM-D6C" 

        return jsonify({
            'success': True,
            'identified_product': identified_product
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        search_term = data.get('query', '').strip()
        cost = float(data.get('cost_price', 0) or 0)
        shipping_cost = float(data.get('shipping_cost', 0) or 0)

        # 1. Fetch Market Data
        cache_key = f"market:{search_term.lower()}"
        market_data = cache.get(cache_key)
        if not market_data:
            market_data = data_source.fetch(search_term)
            if market_data.get('success'):
                cache.set(cache_key, market_data)

        # 2. Analyze
        analysis = analyze_market_data(market_data, cost=cost, shipping_cost=shipping_cost)

        # 3. Final Synchronized Response
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
            },
            "metrics": analysis['metrics']
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
