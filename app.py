"""
ResellSquare Web App - Profit Decision Engine for Retail Arbitrage
Clean architecture: data source > cache > analysis > API
"""

from flask import Flask, render_template, request, jsonify
from cache import cache
from analysis import analyze_market_data
import os
import requests as http_requests

app = Flask(__name__)

USE_DEMO = os.environ.get("USE_DEMO", "true").lower() == "true"

if USE_DEMO:
    from data_sources.demo import DemoDataSource
    data_source = DemoDataSource()
    DATA_SOURCE_LABEL = "demo"
else:
    from data_sources.demo import DemoDataSource
    data_source = DemoDataSource()
    DATA_SOURCE_LABEL = "ebay"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    search_term = data.get('search_term', '').strip()
    condition = data.get('condition', 'all').strip().lower()

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

    analysis = analyze_market_data(raw_data)

    if not analysis['success']:
        return jsonify(analysis), 400

    pricing = analysis['pricing']
    count = pricing['count']

    recent_sales = []
    for i in range(min(15, len(raw_data.get('titles', [])))):
        sale = {
            'title': raw_data['titles'][i],
            'price': raw_data['prices'][i],
        }
        if raw_data.get('conditions') and i < len(raw_data['conditions']):
            sale['condition'] = raw_data['conditions'][i]
        if raw_data.get('dates') and i < len(raw_data['dates']):
            sale['date'] = raw_data['dates'][i]
        recent_sales.append(sale)

    response = {
        'success': True,
        'search_term': search_term,
        'count': count,
        'avg_price': pricing['avg_price'],
        'median_price': pricing['median_price'],
        'min_price': pricing['min_price'],
        'max_price': pricing['max_price'],
        'recent_sales': recent_sales,
        'data_source': DATA_SOURCE_LABEL,
    }

    if analysis.get('confidence'):
        response['confidence'] = analysis['confidence']
    if analysis.get('velocity'):
        response['volatility'] = analysis['velocity'].get('volatility')

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
