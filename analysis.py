class ResellAnalyzer:
    def analyze(self, market_data, cost_price=0, shipping_cost=0):
        """
        Integrates your existing logic into the class structure required by app.py.
        """
        metrics = market_data.get('metrics', {})
        
        # Pull live values from the eBay API response
        median = float(metrics.get('median', 0.0)) 
        count = int(metrics.get('count', 0))
        
        # 2. Handle "No Data" scenarios (Triggers RESEARCH REQUIRED)
        if median <= 0:
            return {
                "success": True,
                "verdict": "RESEARCH REQUIRED",
                "color_code": "#94A3B8",
                "best_platform": "N/A",
                "time_to_sell": "Unknown",
                "tip": "No recent sold data found for this specific query.",
                "pricing_tiers": {"fast": 0, "balanced": 0, "max": 0},
                "net_profit": 0,
                "roi": 0,
                "metrics": {"median": 0, "count": 0}
            }

        # 3. Dynamic Platform & Verdict Logic
        if shipping_cost > (median * 0.30) or (median < 25 and shipping_cost > 12):
            action = "SELL LOCAL"
            color = "#3B82F6"
            platform = "FB Marketplace"
            time_to_sell = "1-3 Days"
            tip = "High shipping costs. Local selling will net you more cash."
        else:
            est_fees = (median * 0.1325) + 0.30
            if median > (cost_price + shipping_cost + est_fees + 5):
                action = "LIST IT"
                color = "#10B981"
                platform = "eBay"
                tip = "Strong market value. Verified sales suggest high demand."
            else:
                action = "DONATE / BUNDLE"
                color = "#EF4444"
                platform = "Local/Lot"
                tip = "Margins are too thin after fees and shipping."

        # Velocity based on volume
        time_to_sell = "1–2 weeks" if count > 15 else ("2–4 weeks" if count > 5 else "4–8 weeks")

        # 4. Financial Calculations
        est_fees = (median * 0.1325) + 0.30
        net_profit = round(median - cost_price - shipping_cost - est_fees, 2)
        roi = round((net_profit / cost_price) * 100) if cost_price > 0 else 0

        return {
            "success": True,
            "verdict": action,
            "color_code": color,
            "best_platform": platform,
            "time_to_sell": time_to_sell,
            "tip": tip,
            "pricing_tiers": {
                "fast": round(median * 0.90, 2),
                "balanced": round(median, 2),
                "max": round(median * 1.15, 2)
            },
            "net_profit": net_profit,
            "roi": roi,
            "metrics": {"median": median, "count": count},
            "recent_sales": market_data.get('recent_sales', [])
        }
