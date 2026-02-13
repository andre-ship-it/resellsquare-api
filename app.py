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
    try:
        data = request.json
        query = data.get('query')
        cost = float(data.get('cost_price', 0) or 0)
        ship = float(data.get('shipping_cost', 0) or 0)

        # 1. Fetch via Agentic Search (Web Scrape + OpenAI)
        market_data = ebay.fetch(query)
        
        # 2. Run the decision engine
        result = analyzer.analyze(market_data, cost, ship)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
