class ResellAnalyzer:
    def analyze(self, market_data, cost_price=0, shipping_cost=0):
        # Extract metrics from the SerpApi-formatted response
        metrics = market_data.get('metrics', {})
        median = float(metrics.get('median', 0.0)) 
        count = int(metrics.get('count', 0))
        
        # If no data is found, return the "Research Required" state
        if median <= 0:
            return {
                "success": True,
                "verdict": "RESEARCH REQUIRED",
                "color_code": "#94A3B8",
                "best_platform": "N/A",
                "time_to_sell": "Unknown",
                "net_profit": 0,
                "roi": 0,
                "pricing_tiers": {"fast": 0, "balanced": 0, "max": 0},
                "metrics": {"median": 0, "count": 0}
            }

        # Calculate Fees (eBay standard 13.25% + $0.30)
        est_fees = (median * 0.1325) + 0.30
        net_profit = round(median - cost_price - shipping_cost - est_fees, 2)
        roi = round((net_profit / cost_price) * 100) if cost_price > 0 else 0

        # Logic for Best Platform
        if shipping_cost > (median * 0.25):
            platform = "FB Marketplace"
            action = "SELL LOCAL"
            color = "#3B82F6"
        else:
            platform = "eBay"
            action = "LIST IT" if net_profit > 5 else "ABANDON"
            color = "#10B981" if net_profit > 5 else "#EF4444"

        # Return the exact keys your frontend (index.html/js) is looking for
        return {
            "success": True,
            "verdict": action,
            "color_code": color,
            "best_platform": platform,
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
