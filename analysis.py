class ResellAnalyzer:
    MIN_COMPS_FOR_CONFIDENCE = 5

    def _time_to_sell(self, count):
        if count >= 10:
            return "1–2 weeks"
        if count >= 5:
            return "2–4 weeks"
        if count > 0:
            return "4–8 weeks"
        return "No Data"

    def analyze(self, market_data, cost_price=0, shipping_cost=0):
        metrics = market_data.get("metrics", {})
        median = float(metrics.get("median", 0.0))
        count = int(metrics.get("count", 0))
        recent_sales = market_data.get("recent_sales", []) or []

        if median <= 0:
            return self.fallback_response()
        if count < self.MIN_COMPS_FOR_CONFIDENCE:
            return self.low_confidence_response(median, recent_sales, count)

        # Resell Logic (eBay Fees approx 13.25% + $0.30)
        fees = (median * 0.1325) + 0.30
        net_profit = round(median - cost_price - shipping_cost - fees, 2)
        roi = (
            round((net_profit / (cost_price + shipping_cost)) * 100)
            if (cost_price + shipping_cost) > 0
            else 0
        )

        time_to_sell = self._time_to_sell(count)

        # Include both legacy and current keys so frontend templates remain compatible.
        return {
            "success": True,
            "verdict": "LIST IT" if net_profit > 10 else "ABANDON",
            "color_code": "#10B981" if net_profit > 10 else "#EF4444",
            "market_consensus": f"${median:,.2f}",
            "target_price": median,
            "best_platform": "eBay",
            "demand_velocity": "High" if count > 5 else "Moderate",
            "time_to_sell": time_to_sell,
            "net_profit": net_profit,
            "roi": roi,
            "financials": {"profit": net_profit, "roi": roi},
            "pricing_tiers": {
                "fast": round(median * 0.90, 2),
                "balanced": round(median, 2),
                "max": round(median * 1.15, 2),
            },
            "recent_sales": recent_sales,
        }

    def low_confidence_response(self, median, recent_sales, count):
        response = self.fallback_response()
        response.update(
            {
                "market_consensus": f"${median:,.2f}",
                "target_price": median,
                "best_platform": "eBay",
                "demand_velocity": "Low Confidence",
                "time_to_sell": self._time_to_sell(count),
                "pricing_tiers": {
                    "fast": round(median * 0.90, 2),
                    "balanced": round(median, 2),
                    "max": round(median * 1.15, 2),
                },
                "recent_sales": recent_sales,
            }
        )
        return response

    def fallback_response(self):
        return {
            "success": True,
            "verdict": "RESEARCH REQUIRED",
            "color_code": "#94A3B8",
            "market_consensus": "N/A",
            "target_price": 0.0,
            "best_platform": "Unknown",
            "demand_velocity": "No Data",
            "time_to_sell": "No Data",
            "net_profit": 0,
            "roi": 0,
            "financials": {"profit": 0, "roi": 0},
            "pricing_tiers": {"fast": 0, "balanced": 0, "max": 0},
            "recent_sales": [],
        }
