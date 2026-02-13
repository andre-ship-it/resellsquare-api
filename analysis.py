class ResellAnalyzer:
        def analyze(self, market_data, cost_price=0, shipping_cost=0):
                    metrics = market_data.get('metrics', {})
                    median = float(metrics.get('median', 0.0)) 
        count = int(metrics.get('count', 0))

            if median <= 0:
                            return {
                                                "success": True,
                                                "verdict": "RESEARCH REQUIRED",
                                                "color_code": "#94A3B8",
                                                "best_platform": "N/A",
                                                "time_to_sell": "Unknown",
                                                "tip": "No recent sold data found.",
                                                "pricing_tiers": {"fast": 0, "balanced": 0, "max": 0},
                                                "financials": {"profit": 0, "roi": 0},
                                                "metrics": {"median": 0, "count": 0}
                            }

        # Dynamic Platform Logic
        if shipping_cost > (median * 0.30):
                        action, platform, color = "SELL LOCAL", "FB Marketplace", "#3B82F6"
else:
            action, platform, color = "LIST IT", "eBay", "#10B981"

        # Velocity based on volume
            velocity = "High" if count > 10 else "Moderate"

        # Financials
            est_fees = (median * 0.1325) + 0.30
            net_profit = round(median - cost_price - shipping_cost - est_fees, 2)
            roi = round((net_profit / cost_price) * 100) if cost_price > 0 else 0

        return {
                        "success": True,
                        "verdict": action,
                        "color_code": color,
                        "best_platform": platform,
                        "time_to_sell": velocity,
                        "pricing_tiers": {
                                            "fast": round(median * 0.90, 2),
                                            "balanced": round(median, 2),
                                            "max": round(median * 1.15, 2)
                        },
                        "financials": {"profit": net_profit, "roi": roi},
                        "metrics": {"median": median, "count": count},
                        "recent_sales": market_data.get('recent_sales', [])
        }
