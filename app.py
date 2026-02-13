import os
import hashlib
from flask import Flask, render_template, request, jsonify
from data_sources.ebay import EbayDataSource
from analysis import ResellAnalyzer

# Ensure the template folder is recognized correctly
app = Flask(__name__, template_folder='templates', static_folder='static')

ebay = EbayDataSource()
analyzer = ResellAnalyzer()

@app.route('/')
def index():
    """Forces the index.html to load from the templates folder."""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error loading index.html: {str(e)}", 500

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query')
    cost_price = float(data.get('cost_price', 0) or 0)
    shipping_cost = float(data.get('shipping_cost', 0) or 0)

    market_data = ebay.fetch(query)
    
    analysis_result = analyzer.analyze(
        market_data=market_data,
        cost_price=cost_price,
        shipping_cost=shipping_cost
    )

    return jsonify(analysis_result)

@app.errorhandler(404)
def page_not_found(e):
    """Custom handler to see if 404s are happening within Flask."""
    return "Flask is running, but this route is missing.", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
