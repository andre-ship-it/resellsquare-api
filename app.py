import os

from flask import Flask, jsonify, render_template, request

from analysis import ResellAnalyzer
from data_sources.ebay import EbayDataSource

app = Flask(__name__)
ebay = EbayDataSource()
analyzer = ResellAnalyzer()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search", methods=["POST"])
def search():
    try:
        data = request.get_json(silent=True) or {}
        query = data.get("query")
        if not query or not str(query).strip():
            return jsonify({"success": False, "error": "Query is required."}), 400

        cost = float(data.get("cost_price", 0) or 0)
        ship = float(data.get("shipping_cost", 0) or 0)

        market_data = ebay.fetch(query)

        if not market_data.get("success", False):
            fallback = analyzer.fallback_response()
            fallback.update(
                {
                    "success": False,
                    "error": market_data.get("error", "Unknown fetch error."),
                    "source": "ebay_agent",
                }
            )
            # Return a UI-compatible shape so frontend labels do not become undefined.
            return jsonify(fallback), 502

        result = analyzer.analyze(market_data, cost, ship)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
