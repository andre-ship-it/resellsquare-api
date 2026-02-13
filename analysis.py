class ResellAnalyzer:
    def analyze(self, market_data, cost_price=0, shipping_cost=0):
        metrics = market_data.get('metrics', {})
        # Ensure we are pulling numbers, not strings
        median = float(metrics.get('median', 0.0)) 
        count = int(metrics.get('count', 0))
        
        if median <= 0:
            return {
                "success": True,
                "verdict": "RESEARCH REQUIRED",
                "color_code": "#94A3B8",
                "target_price": 0.00,
                "best_platform": "N/A",
                "demand_velocity": "No Data",
                "net_profit": 0,
                "roi": 0,
                "pricing_tiers": {"fast": 0, "balanced": 0, "max": 0}
            }

        # Calculation Engine
        fees = (median * 0.1325) + 0.30
        net_profit = round(median - cost_price - shipping_cost - fees, 2)
        roi = round((net_profit / (cost_price + shipping_cost)) * 100) if (cost_price + shipping_cost) > 0 else 0

        # These keys MUST match your dashboard labels exactly
        return {
            "success": True,
            "verdict": "LIST IT" if net_profit > 10 else "ABANDON",
            "color_code": "#10B981" if net_profit > 10 else "#EF4444",
            "target_price": median,
            "best_platform": "eBay",
            "demand_velocity": "High" if count > 10 else "Moderate",
            "net_profit": net_profit,
            "roi": roi,
            "pricing_tiers": {
                "fast": round(median * 0.90, 2),
                "balanced": round(median, 2),
                "max": round(median * 1.10, 2)
            },
            "recent_sales": market_data.get('recent_sales', [])
        }
