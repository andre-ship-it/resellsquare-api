"""
ResellSquare Web App - Profit Decision Engine
Clean architecture: data source > cache > analysis pipeline > API
"""
from flask import Flask, render_template, request, jsonify
from cache import cache
from analysis import analyze_market_data
import os
import hashlib
import requests as http_requests

app = Flask(__name__)

# Config
USE_DEMO = os.environ.get("USE_DEMO", "false").lower() == "true"
EBAY_VERIFICATION_TOKEN = os.environ.get("EBAY_VERIFICATION_TOKEN", "")
EBAY_ENDPOINT = os.environ.get("EBAY_ENDPOINT", "")

# Data Source Selection
if USE_DEMO:
    from data_sources.demo import DemoDataSource
    data_source = DemoDataSource()
    DATA_SOURCE_LABEL = "demo"
else:
    from data_sources.ebay import EbayDataSource
    data_source = EbayDataSource()
    DATA_SOURCE_LABEL = "ebay"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    
    # 1. Extract inputs
    search_term = data.get('query', '').strip()  # Frontend sends 'query'
    if not search_term: 
        # Fallback to 'search_term' for legacy calls
        search_term = data.get('search_term', '').strip()

    condition = data.get('condition', 'used').strip().lower()
    cost = float(data.get('cost_price', 0) or 0)
    shipping_cost = float(data.get('shipping_cost', 0) or 0)

    if not search_term:
        return jsonify({'success': False, 'error': 'Please enter a product name'}), 400

    # 2. Check Cache
    cache_key = f"{DATA_SOURCE_LABEL}:{condition}:{search_term.lower()}"
    cached_data = cache.get(cache_key)

    if cached_data:
        raw_data = cached_data
    else:
        # 3. Fetch fresh data
        raw_data = data_source.fetch(search_term)
        if raw_data.get('status') == 'ok':
            cache.set(cache_key, raw_data)

    # 4. RUN THE DECISION ENGINE (The Logic)
    analysis = analyze_market_data(
        raw_data, 
        condition=condition, 
        cost=cost, 
        shipping_cost=shipping_cost,
        search_query=search_term
    )

    if not analysis['success']:
        return jsonify(analysis), 400

    # 5. Format Response for Frontend
    response = {
        'success': True,
        'verdict': analysis.get('verdict', 'SKIP'),
        'confidence': analysis.get('confidence_level', 'Low'),
        'confidence_reason': analysis.get('confidence_reason', ''),
        
        # UI expects 'variant_warning' boolean and text
        'variant_warning': analysis.get('is_mixed_variant', False),
        'variant_warning_text': analysis.get('variant_reason', ''),

        'metrics': {
            'volume': analysis.get('comps_used', 0),
            'median': analysis.get('median_sold_price', 0),
            'range_low': analysis.get('range_low', 0),
            'range_high': analysis.get('range_high', 0)
        },

        'financials': {
            'fees': analysis.get('fees', 0),
            'shipping': analysis.get('shipping_cost', 0),
            'profit': analysis.get('net_profit', 0),
            'roi': analysis.get('roi', 0)
        }
    }

    return jsonify(response)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'source': DATA_SOURCE_LABEL})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
