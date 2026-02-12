"""
ResellSquare Web App - Profit Decision Engine
"""
from flask import Flask, render_template, request, jsonify
from cache import cache
from analysis import analyze_market_data
import os

app = Flask(__name__)

# Config
USE_DEMO = os.environ.get("USE_DEMO", "false").lower() == "true"
DATA_SOURCE_LABEL = "demo" if USE_DEMO else "ebay"

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
    
@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')    

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    
    # 1. Extract inputs
    search_term = data.get('query', '').strip()
    condition = data.get('condition', 'used').strip().lower()
    cost = float(data.get('cost_price', 0) or 0)
    shipping_cost = float(data.get('shipping_cost', 0) or 0)

    if not search_term:
        return jsonify({'success': False, 'error': 'Please enter a product name'}), 400

    # 2. Check Cache
    cache_key = f"{DATA_SOURCE_LABEL}:{condition}:{search_term.lower()}"
    cached_data = cache.get(cache_key)

    if not cached_data:
        # 3. Fetch fresh data if not cached
        cached_data = data_source.fetch(search_term)
        if cached_data.get('success') or cached_data.get('status') == 'ok':
            cache.set(cache_key, cached_data)

    # 4. Run the Advanced Decision Engine
    # Note: We do NOT pass search_term here as your advanced analysis.py doesn't use it as an arg
    analysis = analyze_market_data(
        cached_data, 
        condition=condition, 
        cost=cost, 
        shipping_cost=shipping_cost
    )

    if not analysis.get('success'):
        return jsonify(analysis), 400

    # 5. BRIDGE: Map Advanced Analysis Output -> Frontend JSON
    # Your analysis returns nested dicts ('pricing', 'verdict', 'confidence'), 
    # but frontend expects specific keys. We map them here.
    
    pricing = analysis.get('pricing', {})
    verdict_data = analysis.get('verdict') or {} # Might be None if cost=0
    confidence = analysis.get('confidence', {})
    variant = analysis.get('variant_info', {})

    response = {
        'success': True,
        
        # Verdict (Handle case where cost is 0 and verdict is None)
        'verdict': verdict_data.get('verdict', 'CHECK'), 
        
        # Confidence
        'confidence': confidence.get('level', 'Low'),
        'confidence_reason': confidence.get('reasons', [''])[0], # Take top reason
        
        # Warnings
        'variant_warning': variant.get('mixed_variants', False),
        'variant_warning_text': variant.get('warning', ''),

        # Metrics for Dashboard
        'metrics': {
            'volume': pricing.get('count', 0),
            'median': pricing.get('median_price', 0),
            'range_low': pricing.get('min_price', 0),
            'range_high': pricing.get('max_price', 0)
        },

        # Financials
        'financials': {
            'fees': verdict_data.get('ebay_fees', 0),
            'shipping': shipping_cost,
            'profit': verdict_data.get('net_profit', 0),
            'roi': verdict_data.get('roi', 0)
        }
    }

    return jsonify(response)

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
