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
    """Main dashboard entry point."""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    """Handles product search and financial analysis."""
    data = request.json
    query = data.get('query')
    cost_price = float(data.get('cost_price', 0) or 0)
    shipping_cost = float(data.get('shipping_cost', 0) or 0)

    if not query:
        return jsonify({"success": False, "error": "No query provided"}), 400

    # 1. Fetch live market data from eBay
    market_data = ebay.fetch(query)
    
    if not market_data['success']:
        return jsonify(market_data), 200

    # 2. Run decision intelligence logic
    analysis = analyzer.analyze(
        market_data=market_data,
        cost_price=cost_price,
        shipping_cost=shipping_cost
    )

    return jsonify(analysis)

@app.route('/marketplace-delete', methods=['GET', 'POST'])
def marketplace_delete():
    """
    Handles eBay's Mandatory Marketplace Account Deletion notifications.
    This fulfills the production requirement and stops the 404 errors.
    """
    if request.method == 'GET':
        challenge_code = request.args.get('challenge_code')
        verification_token = os.environ.get('EBAY_VERIFICATION_TOKEN')
        endpoint = os.environ.get('EBAY_ENDPOINT')

        if not challenge_code or not verification_token or not endpoint:
            return "Missing configuration parameters", 400

        # Create the response hash required by eBay
        sha256 = hashlib.sha256()
        sha256.update(challenge_code.encode('utf-8'))
        sha256.update(verification_token.encode('utf-8'))
        sha256.update(endpoint.encode('utf-8'))
        response_hash = sha256.hexdigest()

        return jsonify({"challengeResponse": response_hash}), 200

    if request.method == 'POST':
        # Acknowledge the notification
        return "", 200

if __name__ == '__main__':
    # Bind to 0.0.0.0 and use Railway's dynamic PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
