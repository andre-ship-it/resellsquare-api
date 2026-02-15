class ResellAnalyzer:
    def analyze(self, market_data, cost_price=0, shipping_cost=0):
        metrics = market_data.get("metrics", {})
        median = float(metrics.get("median", 0.0))
        count = int(metrics.get("count", 0))

        if median <= 0:
            return self.fallback_response()

        # Resell Logic (eBay Fees approx 13.25% + $0.30)
        fees = (median * 0.1325) + 0.30
        net_profit = round(median - cost_price - shipping_cost - fees, 2)
        roi = (
            round((net_profit / (cost_price + shipping_cost)) * 100)
            if (cost_price + shipping_cost) > 0
            else 0
        )

        # This dictionary maps directly to your HTML/JS labels
        return {
            "success": True,
            "verdict": "LIST IT" if net_profit > 10 else "ABANDON",
            "color_code": "#10B981" if net_profit > 10 else "#EF4444",
            "market_consensus": f"${median:,.2f}",
            "target_price": median,
            "best_platform": "eBay",
            "demand_velocity": "High" if count > 5 else "Moderate",
            "net_profit": net_profit,
            "roi": roi,
            "pricing_tiers": {
                "fast": round(median * 0.90, 2),
                "balanced": round(median, 2),
                "max": round(median * 1.15, 2),
            },
            "recent_sales": market_data.get("recent_sales", []),
        }

    def fallback_response(self):
        return {
            "success": True,
            "verdict": "RESEARCH REQUIRED",
            "color_code": "#94A3B8",
            "market_consensus": "N/A",
            "target_price": 0.0,
            "best_platform": "Unknown",
            "demand_velocity": "No Data",
            "net_profit": 0,
            "roi": 0,
            "pricing_tiers": {"fast": 0, "balanced": 0, "max": 0},
        }
