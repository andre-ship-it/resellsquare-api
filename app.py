import os
import hashlib
from flask import Flask, render_template, request, jsonify
from data_sources.ebay import EbayDataSource

app = Flask(__name__)

# Initialize ONLY the data source to prevent import crashes
ebay = EbayDataSource()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query')
    
    # Minimal response to stop the frontend from hanging
    if not query:
        return jsonify({"success": False, "error": "No query"}), 400

    # Fetch raw eBay data
    market_data = ebay.fetch(query)
    
    # If this returns data, your eBay keys are 100% correct
    return jsonify({
        "success": True,
        "verdict": "CONNECTION TEST",
        "color_code": "#3b82f6",
        "financials": {"profit": 0, "roi": 0},
        "recent_sales": market_data.get('recent_sales', []),
        "raw_debug": market_data
    })

@app.route('/marketplace-delete', methods=['GET', 'POST'])
def marketplace_delete():
    """Satisfies eBay compliance to prevent API blocking."""
    if request.method == 'GET':
        challenge_code = request.args.get('challenge_code')
        verification_token = os.environ.get('EBAY_VERIFICATION_TOKEN')
        endpoint = os.environ.get('EBAY_ENDPOINT')
        
        sha256 = hashlib.sha256()
        sha256.update(challenge_code.encode('utf-8'))
        sha256.update(verification_token.encode('utf-8'))
        sha256.update(endpoint.encode('utf-8'))
        return jsonify({"challengeResponse": sha256.hexdigest()}), 200
    return "", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
