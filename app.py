import os
import hashlib
from flask import Flask, render_template, request, jsonify
from data_sources.ebay import EbayDataSource

app = Flask(__name__)

# Initialize only the eBay source to verify connection
ebay = EbayDataSource()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query')

    if not query:
        return jsonify({"success": False, "error": "No query provided"}), 400

    # Fetch raw data to confirm Client ID and Secret are working
    market_data = ebay.fetch(query)
    return jsonify(market_data)

@app.route('/marketplace-delete', methods=['GET', 'POST'])
def marketplace_delete():
    if request.method == 'GET':
        challenge_code = request.args.get('challenge_code')
        verification_token = os.environ.get('EBAY_VERIFICATION_TOKEN')
        endpoint = os.environ.get('EBAY_ENDPOINT')
        if not challenge_code or not verification_token or not endpoint:
            return "Missing configuration", 400

        sha256 = hashlib.sha256()
        sha256.update(challenge_code.encode('utf-8'))
        sha256.update(verification_token.encode('utf-8'))
        sha256.update(endpoint.encode('utf-8'))
        return jsonify({"challengeResponse": sha256.hexdigest()}), 200
    return "", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
