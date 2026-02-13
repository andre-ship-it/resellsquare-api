import os
import hashlib
from flask import Flask, render_template, request, jsonify
from data_sources.ebay import EbayDataSource
from analysis import ResellAnalyzer

app = Flask(__name__)

# Initialize components
ebay = EbayDataSource()
analyzer = ResellAnalyzer()

@app.route('/')
def index():
        return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
        """Handles production search and runs the resell intelligence engine."""
        data = request.json
        query = data.get('query')
        cost_price = float(data.get('cost_price', 0) or 0)
        shipping_cost = float(data.get('shipping_cost', 0) or 0)

    if not query:
                return jsonify({"success": False, "error": "No query provided"}), 400

    # 1. Fetch live market data
    market_data = ebay.fetch(query)

    if not market_data['success']:
                # Return a frontend-safe structured response instead of raw error
                error_msg = market_data.get('error', 'Market data unavailable')
                return jsonify({
                    "success": True,
                    "verdict": "MARKET DATA UNAVAILABLE",
                    "color_code": "#94A3B8",
                    "best_platform": "N/A",
                    "time_to_sell": "Unknown",
                    "tip": error_msg,
                    "pricing_tiers": {"fast": 0, "balanced": 0, "max": 0},
                    "financials": {"profit": 0, "roi": 0},
                    "metrics": {"median": 0, "count": 0},
                    "recent_sales": []
                }), 200

    # 2. Run your new ResellAnalyzer logic
    analysis = analyzer.analyze(
                market_data=market_data,
                cost_price=cost_price,
                shipping_cost=shipping_cost
    )

    return jsonify(analysis)

@app.route('/marketplace-delete', methods=['GET', 'POST'])
def marketplace_delete():
        """Satisfies eBay compliance to stop 404 errors and maintain production access."""
        if request.method == 'GET':
                    challenge_code = request.args.get('challenge_code')
                    verification_token = os.environ.get('EBAY_VERIFICATION_TOKEN')
                    endpoint = os.environ.get('EBAY_ENDPOINT')

            if not challenge_code or not verification_token:
                            return "Missing params", 400

        sha256 = hashlib.sha256()
        sha256.update(challenge_code.encode('utf-8'))
        sha256.update(verification_token.encode('utf-8'))
        sha256.update(endpoint.encode('utf-8'))

        return jsonify({"challengeResponse": sha256.hexdigest()}), 200

    return "", 200

if __name__ == '__main__':
        port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
