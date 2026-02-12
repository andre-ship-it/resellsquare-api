"""
ResellSquare Web App - Profit Decision Engine with Discord Monitoring
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
DATA_SOURCE_LABEL = "demo" if USE_DEMO else "ebay"
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# Import correct data source
if USE_DEMO:
    from data_sources.demo import DemoDataSource
    data_source = DemoDataSource()
else:
    from data_sources.ebay import EbayDataSource
    data_source = EbayDataSource()

def send_discord_log(query, verdict, median, profit, roi):
    """Sends a formatted notification to Discord for monitoring"""
    if not DISCORD_WEBHOOK_URL:
        return

    # Color mapping: Green for BUY, Red for SKIP, Amber for others
    color = 3066993 if verdict == "BUY" else 15158332 if verdict == "SKIP" else 15105570
    
    payload = {
        "embeds": [{
            "title": f"🔍 New Search: {query}",
            "color": color,
            "fields": [
                {"name": "Verdict", "value": f"**{verdict}**", "inline": True},
                {"name": "Market Price", "value": f"${median}", "inline": True},
                {"name": "Est. Profit", "value": f"${profit} ({roi}%)", "inline": True}
            ],
            "footer": {"text": f"ResellSquare Beta | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Discord Logging Error: {e}")

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')    

@app.route('/api/search', methods=['POST'])
def search():
    try:
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
        analysis_result = analyze_market_data(
            cached_data, 
            condition=condition, 
            cost=cost, 
            shipping_cost=shipping_cost
        )

        if not analysis_result.get('success'):
            return jsonify(analysis_result), 400

        # 5. BRIDGE: Map Advanced Analysis Output -> Frontend JSON
        pricing = analysis_result.get('pricing', {})
        verdict_data = analysis_result.get('verdict') or {}
        confidence = analysis_result.get('confidence', {})
        variant = analysis_result.get('variant_info', {})

        response = {
            'success': True,
            'verdict': verdict_data.get('verdict', 'CHECK'), 
            'confidence': confidence.get('level', 'Low'),
            'confidence_reason': confidence.get('reasons', [''])[0],
            'variant_warning': variant.get('mixed_variants', False),
            'variant_warning_text': variant.get('warning', ''),
            'metrics': {
                'volume': pricing.get('count', 0),
                'median': pricing.get('median_price', 0),
                'range_low': pricing.get('min_price', 0),
                'range_high': pricing.get('max_price', 0)
            },
            'financials': {
                'fees': verdict_data.get('ebay_fees', 0),
                'shipping': shipping_cost,
                'profit': verdict_data.get('net_profit', 0),
                'roi': verdict_data.get('roi', 0)
            }
        }

        # 6. Log search to Discord
        send_discord_log(
            query=search_term,
            verdict=response['verdict'],
            median=response['metrics']['median'],
            profit=response['financials']['profit'],
            roi=response['financials']['roi']
        )

        return jsonify(response)

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Railway typically provides the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
