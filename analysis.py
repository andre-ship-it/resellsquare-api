class ResellAnalyzer:
    def analyze(self, market_data, cost_price=0, shipping_cost=0):
        metrics = market_data.get('metrics', {})
        median = float(metrics.get('median', 0.0)) 
        count = int(metrics.get('count', 0))
        
        # If no data is found
        if median <= 0:
            return {
                "success": True,
                "verdict": "RESEARCH REQUIRED",
                "color_code": "#94A3B8",
                "market_consensus": "N/A",  # Matches dashboard label
                "best_platform": "Unknown", # Matches dashboard label
                "demand_velocity": "Unknown", # Matches dashboard label
                "net_profit": 0,
                "roi": 0,
                "pricing_tiers": {"fast": 0, "balanced": 0, "max": 0}
            }

        # CALCULATIONS
        est_fees = (median * 0.1325) + 0.30
        net_profit = round(median - cost_price - shipping_cost - est_fees, 2)
        roi = round((net_profit / (cost_price + shipping_cost)) * 100) if (cost_price + shipping_cost) > 0 else 0

        # Return exact names for your dashboard
        return {
            "success": True,
            "verdict": "LIST IT" if net_profit > 10 else "ABANDON",
            "color_code": "#10B981" if net_profit > 10 else "#EF4444",
            "market_consensus": f"${median:,.2f}", # Displays as "$1,200.00"
            "target_price": median,
            "best_platform": "eBay" if shipping_cost < (median * 0.2) else "Local",
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
