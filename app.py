"""
ResellSquare Web App - Profit Decision Engine with Discord Monitoring
"""
import os
import base64
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from cache import cache
from analysis import analyze_market_data

app = Flask(__name__)

# Config
USE_DEMO = os.environ.get("USE_DEMO", "false").lower() == "true"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# Import data source
if USE_DEMO:
    from data_sources.demo import DemoDataSource
    data_source = DemoDataSource()
else:
    from data_sources.ebay import EbayDataSource
    data_source = EbayDataSource()

def send_discord_log(query, verdict, median, profit, roi, image_url=None):
    """
    Sends a formatted notification to Discord for monitoring.
    """
    if not DISCORD_WEBHOOK_URL:
        return

    # Color mapping for visual urgency (Green for LIST IT, Blue for LOCAL, Red for others)
    color = 65280 if verdict == "LIST IT" else 3447003 if verdict == "SELL LOCAL" else 16711680
    
    payload = {
        "embeds": [{
            "title": f"🔍 New Intelligence: {query}",
            "color": color,
            "fields": [
                {"name": "Verdict", "value": f"**{verdict}**", "inline": True},
                {"name": "Target Price", "value": f"${median}", "inline": True},
                {"name": "Net Profit", "value": f"${profit} ({roi}% ROI)", "inline": False},
            ],
            "thumbnail": {"url": image_url} if image_url else None,
            "footer": {"text": f"ResellSquare Engine | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
        }]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Discord Logging Error: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/identify-image', methods=['POST'])
def identify_image():
    """
    Receives base64 image, sends to OpenAI GPT-4o Vision, returns identified text.
    """
    try:
        data = request.get_json()
        base64_image = data.get('image')

        if not base64_image:
            return jsonify({'success': False, 'error': 'No image provided'}), 400

        if "," in base64_image:
            base64_image = base64_image.split(",")[1]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Identify the exact product in this image. Return ONLY the brand and model name. Be concise."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }],
            "max_tokens": 40
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        res_json = response.json()
        identified_product = res_json['choices'][0]['message']['content'].strip().replace('"', '')

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

        # 2. Run the Dynamic Decision Engine
        analysis = analyze_market_data(market_data, cost=cost, shipping_cost=shipping_cost)

        # 3. Log to Discord
        first_comp_image = market_data.get('recent_sales', [{}])[0].get('image')
        send_discord_log(
            query=search_term,
            verdict=analysis['verdict'],
            median=analysis['metrics']['median'],
            profit=analysis['net_profit'],
            roi=analysis['roi'],
            image_url=first_comp_image
        )

        # 4. Final Synchronized Response for index.html
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
        print(f"Server Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
