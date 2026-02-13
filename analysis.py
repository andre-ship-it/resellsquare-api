class ResellAnalyzer:
    def analyze(self, market_data, cost_price=0, shipping_cost=0):
        # Extract metrics from the SerpApi-formatted response
        metrics = market_data.get('metrics', {})
        median = float(metrics.get('median', 0.0)) 
        count = int(metrics.get('count', 0))
        
        # Fallback if no data is found
        if median <= 0:
            return {
                "success": True,
                "verdict": "RESEARCH REQUIRED",
                "color_code": "#94A3B8",
                "best_platform": "N/A",
                "time_to_sell": "No Data",
                "net_profit": 0,
                "roi": 0,
                "pricing_tiers": {"fast": 0, "balanced": 0, "max": 0},
                "metrics": {"median": 0, "count": 0}
            }

        # Logic for Platform and Verdict
        est_fees = (median * 0.1325) + 0.30
        net_profit = round(median - cost_price - shipping_cost - est_fees, 2)
        roi = round((net_profit / (cost_price + shipping_cost)) * 100) if (cost_price + shipping_cost) > 0 else 0

        # Return exact keys needed by the dashboard
        return {
            "success": True,
            "verdict": "LIST IT" if net_profit > 5 else "ABANDON",
            "color_code": "#10B981" if net_profit > 5 else "#EF4444",
            "best_platform": "eBay",
            "time_to_sell": "High" if count > 10 else "Moderate",
            "net_profit": net_profit,
            "roi": roi,
            "pricing_tiers": {
                "fast": round(median * 0.90, 2),
                "balanced": round(median, 2),
                "max": round(median * 1.15, 2)
            },
            "metrics": {"median": median, "count": count},
            "recent_sales": market_data.get('recent_sales', [])
        }
