import os
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
    data = request.json
    query = data.get('query')
    cost_price = float(data.get('cost_price', 0) or 0)
    shipping_cost = float(data.get('shipping_cost', 0) or 0)

    if not query:
        return jsonify({"success": False, "error": "No query"}), 400

    # 1. Fetch data (Ensure your ebay.py is set up for SerpApi)
    market_data = ebay.fetch(query)
    
    if not market_data.get('success'):
        return jsonify(market_data), 200

    # 2. Run the decision logic
    analysis_result = analyzer.analyze(
        market_data=market_data,
        cost_price=cost_price,
        shipping_cost=shipping_cost
    )

    return jsonify(analysis_result)

if __name__ == '__main__':
    # Railway environment uses the PORT variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
