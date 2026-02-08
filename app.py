"""
ResellSquare Web App — Profit Decision Engine for Retail Arbitrage
Clean architecture: data source → cache → analysis → API

Data source is swappable:
  - DemoDataSource (current) for testing
  - EbayApiDataSource (coming) for live eBay Browse API data
"""

from flask import Flask, render_template, request, jsonify
from cache import cache
from analysis import analyze_market_data
import os

app = Flask(__name__)

# -------------------------------------------------------
# Data Source Selection
# Set USE_DEMO=true in env to use demo data for testing.
# When eBay API keys are ready, set EBAY_CLIENT_ID and
# EBAY_CLIENT_SECRET in env and remove USE_DEMO.
# -------------------------------------------------------
USE_DEMO = os.environ.get("USE_DEMO", "true").lower() == "true"

if USE_DEMO:
    from data_sources.demo import DemoDataSource
    data_source = DemoDataSource()
    DATA_SOURCE_LABEL = "demo"
else:
    # Future: from data_sources.ebay_api import EbayApiDataSource
    # data_source = EbayApiDataSource(
    #     client_id=os.environ["EBAY_CLIENT_ID"],
    #     client_secret=os.environ["EBAY_CLIENT_SECRET"]
    # )
    from data_sources.demo import DemoDataSource
    data_source = DemoDataSource()
    DATA_SOURCE_LABEL = "ebay"


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/search', methods=['POST'])
def search():
    """
    Profit analysis endpoint.

    Accepts:
        search_term (str): Product name
        condition (str): 'all', 'new', or 'used' (optional)

    Returns:
        JSON with pricing stats, confidence, and recent sales
    """
    data = request.get_json()
    search_term = data.get('search_term', '').strip()
    condition = data.get('condition', 'all').strip().lower()

    if not search_term:
        return jsonify({
            'success': False,
            'error': 'Please enter a product name'
        }), 400

    if condition not in ('all', 'new', 'used'):
        condition = 'all'

    # Cache key includes condition
    cache_key = f"{DATA_SOURCE_LABEL}:{condition}:{search_term.lower()}"

    # Check cache
    cached_data = cache.get(cache_key)
    if cached_data:
        raw_data = cached_data
    else:
        raw_data = data_source.fetch(search_term)

        # Cache successful results (12 hour TTL)
        if raw_data.get('status') == 'ok':
            cache.set(cache_key, raw_data)

    # Run analysis
    analysis = analyze_market_data(raw_data)

    if not analysis['success']:
        return jsonify(analysis), 400

    # Build response
    pricing = analysis['pricing']
    count = pricing['count']

    # Build recent sales list with condition info if available
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

    # Include analysis extras if available
    if analysis.get('confidence'):
        response['confidence'] = analysis['confidence']
    if analysis.get('velocity'):
        response['volatility'] = analysis['velocity'].get('volatility')

    return jsonify(response)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'cache_active': True,
        'data_source': DATA_SOURCE_LABEL
    })
