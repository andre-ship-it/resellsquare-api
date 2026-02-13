import os
from flask import Flask, render_template, request, jsonify
from data_sources.ebay import EbayDataSource
from analysis import ResellAnalyzer

app = Flask(__name__)
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

    # 1. Fetch from SerpApi
    market_data = ebay.fetch(query)
    
    if not market_data.get('success'):
        return jsonify(market_data)

    # 2. Run Decision Logic
    # CRITICAL: We return the analysis result, not the raw market_data
    analysis_result = analyzer.analyze(
        market_data=market_data,
        cost_price=cost_price,
        shipping_cost=shipping_cost
    )

    return jsonify(analysis_result)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
