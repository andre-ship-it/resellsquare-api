import os
from flask import Flask, render_template, request, jsonify
from data_sources.ebay import EbayDataSource
from analysis import ResellAnalyzer

app = Flask(__name__)
ebay = EbayDataSource()
analyzer = ResellAnalyzer()

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query')
    cost_price = float(data.get('cost_price', 0) or 0)
    shipping_cost = float(data.get('shipping_cost', 0) or 0)

    # 1. Fetch from SerpApi (via your updated ebay.py)
    market_data = ebay.fetch(query)
    
    # 2. Run the logic engine
    # We return ONLY the analysis_result to the frontend
    analysis_result = analyzer.analyze(
        market_data=market_data,
        cost_price=cost_price,
        shipping_cost=shipping_cost
    )

    return jsonify(analysis_result)
