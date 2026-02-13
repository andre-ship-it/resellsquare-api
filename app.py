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

if USE_DEMO:
    from data_sources.demo import DemoDataSource
    data_source = DemoDataSource()
else:
    from data_sources.ebay import EbayDataSource
    data_source = EbayDataSource()

def send_discord_log(query, verdict, median, profit, roi, image_url=None):
    if not DISCORD_WEBHOOK_URL: return
    color = 65280 if verdict == "LIST IT" else 3447003 if verdict == "SELL LOCAL" else 16711680
    payload = {
        "embeds": [{
            "title": f"🔍 New Search: {query}",
            "color": color,
            "fields": [
                {"name": "Verdict", "value": f"**{verdict}**", "inline": True},
                {"name": "Market Price", "value": f"${median}", "inline": True},
                {"name": "Est. Profit", "value": f"${profit} ({roi}%)", "inline": False}
            ],
            "thumbnail": {"url": image_url} if image_url else None,
            "footer": {"text": f"ResellSquare | {datetime.now().strftime('%H:%M:%S')}"}
        }]
    }
    try: requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except: pass

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

        cache_key = f"market:{search_term.lower()}"
        market_data = cache.get(cache_key)
        if not market_data:
            market_data = data_source.fetch(search_term)
            if market_data.get('success'):
                cache.set(cache_key, market_data)

        analysis = analyze_market_data(market_data, cost=cost, shipping_cost=shipping_cost)

        send_discord_log(
            query=search_term,
            verdict=analysis['verdict'],
            median=analysis['metrics']['median'],
            profit=analysis['net_profit'],
            roi=analysis['roi'],
            image_url=market_data.get('recent_sales', [{}])[0].get('image')
        )

        return jsonify({
            "success": True,
            "verdict": analysis['verdict'],
            "color_code": analysis['color_code'],
            "best_platform": analysis['best_platform'],
            "time_to_sell": analysis['time_to_sell'],
            "pricing_tiers": analysis['pricing_tiers'],
            "recent_sales": market_data.get('recent_sales', []),
            "financials": {"profit": analysis['net_profit'], "roi": analysis['roi']},
            "metrics": analysis['metrics']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
