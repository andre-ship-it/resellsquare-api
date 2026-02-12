"""
ResellSquare Web App - Profit Decision Engine for Retail Arbitrage
Clean architecture: data source > cache > analysis pipeline > API

Phase 1 accuracy + Phase 2 Amazon-aligned pivot
"""

from flask import Flask, render_template, request, jsonify
from cache import cache
from analysis import analyze_market_data
import os
import hashlib
import requests as http_requests

app = Flask(__name__)

USE_DEMO = os.environ.get("USE_DEMO", "true").lower() == "true"

if USE_DEMO:
        from data_sources.demo import DemoDataSource
    data_source = DemoDataSource()
    DATA_SOURCE_LABEL = "demo"
else:
    from data_sources.ebay import EbayDataSource
    data_source = EbayDataSource()
        DATA_SOURCE_LABEL = "ebay"


# eBay Marketplace Account Deletion Notification config
EBAY_VERIFICATION_TOKEN = os.environ.get("EBAY_VERIFICATION_TOKEN", "")
EBAY_ENDPOINT = os.environ.get("EBAY_ENDPOINT", "")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/marketplace-delete', methods=['GET', 'POST'])
def marketplace_delete():
    """
        eBay Marketplace Account Deletion/Closure Notification endpoint.
            GET: Responds to eBay challenge code for endpoint verification.
                POST: Acknowledges account deletion notifications.
                    """
    if request.method == 'GET':
            challenge_code = request.args.get('challenge_code', '')
        if not challenge_code:
            return jsonify({'error': 'Missing challenge_code'}), 400
                    verification_token = EBAY_VERIFICATION_TOKEN
        endpoint = EBAY_ENDPOINT
        m = hashlib.sha256()
        m.update(challenge_code.encode('utf-8'))
        m.update(verification_token.encode('utf-8'))
        m.update(endpoint.encode('utf-8'))
        response_hash = m.hexdigest()
        return jsonify({'challengeResponse': response_hash}), 200
else:
        # POST - acknowledge the account deletion notification
        return '', 200


@app.route('/api/search', methods=['POST'])
    def search():
            data = request.get_json()
    search_term = data.get('search_term', '').strip()
        condition = data.get('condition', 'all').strip().lower()
    cost = float(data.get('cost', 0) or 0)
    shipping_cost = float(data.get('shipping_cost', 0) or 0)

                                               if not search_term:
        return jsonify({'success': False, 'error': 'Please enter a product name'}), 400

    if condition not in ('all', 'new', 'used'):
        condition = 'all'

    cache_key = f"{DATA_SOURCE_LABEL}:{condition}:{search_term.lower()}"

    cached_data = cache.get(cache_key)
    if cached_data:
        raw_data = cached_data
else:
        raw_data = data_source.fetch(search_term)
            if raw_data.get('status') == 'ok':
            cache.set(cache_key, raw_data)

    # Run the full analysis pipeline (Phase 1 steps 3-8)
    analysis = analyze_market_data(
        raw_data,
        condition=condition,
            cost=cost,
        shipping_cost=shipping_cost,
)

    if not analysis['success']:
                    return jsonify(analysis), 400

    pricing = analysis['pricing']
    confidence = analysis.get('confidence', {})
    variant_info = analysis.get('variant_info', {})
    verdict = analysis.get('verdict')
    recent_sales = analysis.get('recent_sales', [])
        debug = analysis.get('debug', {})

    response = {
        'success': True,
        'search_term': search_term,
        'condition': condition,
            'count': pricing['count'],
        'avg_price': pricing['avg_price'],
                   'median_price': pricing['median_price'],
        'min_price': pricing['min_price'],
            'max_price': pricing['max_price'],
                    'price_range': pricing.get('price_range', 0),
                    'recent_sales': recent_sales,
        'data_source': DATA_SOURCE_LABEL,
        # Phase 1 Step 6: Real confidence
        'confidence': confidence,
        # Phase 1 Step 8: Variant warnings
        'variant_info': variant_info,
        # Phase 1 Step 7: Verdict (if cost provided)
            'verdict': verdict,
        # Volatility
        'volatility': analysis.get('velocity', {}).get('volatility'),
                'market_signal': analysis.get('velocity', {}).get('market_signal'),
                # Phase 1 Step 18: Debug fields
                'debug': debug,
    }

    return jsonify(response)


@app.route('/api/upc-lookup', methods=['POST'])
def upc_lookup():
        """
            Look up product name from UPC/EAN barcode.
                Proxied through backend to avoid CORS issues.
                    Uses UPCitemdb trial API (100 req/day free).
                        """
    data = request.get_json()
    upc = data.get('upc', '').strip()

    if not upc:
                return jsonify({'success': False, 'error': 'No UPC provided'}), 400

    # Check cache first
    cache_key = f"upc:{upc}"
    cached = cache.get(cache_key)
    if cached:
                return jsonify(cached)

    try:
                resp = http_requests.get(
                                f"https://api.upcitemdb.com/prod/trial/lookup",
                                params={"upc": upc},
                                headers={
                                                    "Accept": "application/json",
                                                    "User-Agent": "ResellSquare/1.0"
                                },
            timeout=10
                )

        if resp.status_code == 200:
                        result = resp.json()
                        items = result.get('items', [])
                        if items:
                                            item = items[0]
                                            response = {
                                                'success': True,
                                                'upc': upc,
                                                'title': item.get('title', ''),
                                                'brand': item.get('brand', ''),
                                                'category': item.get('category', ''),
                    'description': item.get('description', ''),
                                            }
                                            # Cache UPC lookups for 7 days (they don't change)
                                            cache.set(cache_key, response)
                                            return jsonify(response)
        else:
                return jsonify({
                                        'success': False,
                                        'error': f'No product found for UPC: {upc}'
                })
        elif resp.status_code == 429:
            return jsonify({
                    'success': False,
                'error': 'UPC lookup rate limit reached. Try again later.'
}), 429
else:
            return jsonify({
                                'success': False,
                'error': 'UPC lookup failed'
}), 500

except http_requests.Timeout:
        return jsonify({'success': False, 'error': 'UPC lookup timed out'}), 504
except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health')
def health():
    return jsonify({
                'status': 'ok',
                'cache_active': True,
                'data_source': DATA_SOURCE_LABEL
    })
