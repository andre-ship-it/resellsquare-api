"""
ResellSquare Web App
Clean architecture with cache + analysis layers
"""

from flask import Flask, render_template, request, jsonify
from cache import cache
from analysis import analyze_market_data
from data_sources.demo import DemoDataSource
import os

app = Flask(__name__)

# Initialize data source (demo for now)
data_source = DemoDataSource()


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/search', methods=['POST'])
def search():
    """
    Handle search requests with proper architecture:
    1. Check cache
    2. If stale/missing, fetch from data source
    3. Analyze data
    4. Return results
    """
    data = request.get_json()
    search_term = data.get('search_term', '').strip()
    
    if not search_term:
        return jsonify({
            'success': False,
            'error': 'Please enter a product name'
        }), 400
    
    # Create cache key
    cache_key = f"demo:{search_term.lower()}"
    
    # Check cache first
    cached_data = cache.get(cache_key)
    
    if cached_data:
        print(f"✓ Cache HIT for '{search_term}'")
        raw_data = cached_data
    else:
        print(f"✗ Cache MISS for '{search_term}' - fetching fresh data")
        
        # Fetch from data source
        raw_data = data_source.fetch(search_term)
        
        # Cache it (12 hour TTL)
        if raw_data['status'] == 'ok':
            cache.set(cache_key, raw_data)
    
    # Analyze the data
    analysis = analyze_market_data(raw_data)
    
    if not analysis['success']:
        return jsonify(analysis), 400
    
    # Build response with recent sales
    response = {
        'success': True,
        'search_term': search_term,
        'count': analysis['pricing']['count'],
        'avg_price': analysis['pricing']['avg_price'],
        'median_price': analysis['pricing']['median_price'],
        'min_price': analysis['pricing']['min_price'],
        'max_price': analysis['pricing']['max_price'],
        'recent_sales': [
            {
                'title': raw_data['titles'][i],
                'price': raw_data['prices'][i]
            }
            for i in range(min(5, len(raw_data['titles'])))
        ]
    }
    
    return jsonify(response)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'cache_active': True,
        'data_source': 'demo'
    })


