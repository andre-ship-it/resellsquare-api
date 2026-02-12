def analyze_market_data(market_data, cost=0, shipping_cost=0):
    """
    Advanced Dynamic Decision Engine for ResellSquare.
    Calculates verdicts and pricing based on live sold data metrics.
    """
    # 1. Extract Live Metrics
    metrics = market_data.get('metrics', {})
    # Default to 0 to avoid hardcoded static values
    median = float(metrics.get('median', 0)) 
    count = metrics.get('count', 0)
    
    # 2. Dynamic Platform & Verdict Logic
    # We switch platform based on weight/price ratio to maximize profit
    if median <= 0:
        action = "RESEARCH FURTHER"
        color = "#94A3B8" # Slate
        platform = "Manual Check"
        time_to_sell = "Unknown"
    elif shipping_cost > (median * 0.35) or (median < 20 and shipping_cost > 10):
        action = "SELL LOCAL"
        color = "#3B82F6" # Blue
        platform = "FB Marketplace"
        time_to_sell = "1-3 Days"
    elif median < (cost + shipping_cost + (median * 0.13)):
        action = "DONATE / BUNDLE"
        color = "#EF4444" # Red
        platform = "Thrift / Lot"
        time_to_sell = "N/A"
    else:
        action = "LIST IT"
        color = "#10B981" # Emerald Green
        platform = "eBay"
        # Velocity based on volume of sold comps
        time_to_sell = "1–2 weeks" if count > 15 else "2–4 weeks" if count > 5 else "4–8 weeks"

    # 3. Dynamic Strategic Pricing Tiers
    # Calculated as offsets from the live median
    prices = {
        "fast": round(median * 0.90, 2),      # 10% below market to undercut
        "balanced": round(median, 2),         # Fair market value
        "max": round(median * 1.15, 2)        # 15% above for patience
    }

    # 4. Financial Calculation Engine
    # Standard eBay fee estimate (13.25% + $0.30)
    est_fees = (median * 0.1325) + 0.30
    net_profit = round(median - cost - shipping_cost - est_fees, 2)
    roi = round((net_profit / cost) * 100) if cost > 0 else 0

    return {
        "success": True,
        "verdict": action,
        "color_code": color,
        "best_platform": platform,
        "time_to_sell": time_to_sell,
        "pricing_tiers": prices,
        "net_profit": net_profit,
        "roi": roi,
        "metrics": {
            "median": median,
            "count": count,
            "label": f"Based on {count} verified solds"
        }
    }
