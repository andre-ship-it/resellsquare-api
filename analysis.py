def analyze_market_data(market_data, cost=0, shipping_cost=0):
    """
    Advanced Dynamic Decision Engine for ResellSquare.
    This version eliminates all hardcoded placeholders and reacts solely to live data.
    """
    # 1. Extract Live Metrics from the API response
    metrics = market_data.get('metrics', {})
    
    # CRITICAL FIX: Default to 0.0 to ensure no false $142 results
    median = float(metrics.get('median', 0.0)) 
    count = int(metrics.get('count', 0))
    
    # 2. Handle "No Data" scenarios (Prevents false positives)
    if median <= 0:
        return {
            "success": True,
            "verdict": "RESEARCH REQUIRED",
            "color_code": "#94A3B8", # Slate Grey
            "best_platform": "N/A",
            "time_to_sell": "Unknown",
            "tip": "No recent sold data found for this specific query.",
            "pricing_tiers": {"fast": 0, "balanced": 0, "max": 0},
            "net_profit": 0,
            "roi": 0,
            "metrics": {"median": 0, "count": 0}
        }

    # 3. Dynamic Platform & Verdict Logic
    # Switch to Local if shipping is > 30% of value or price is very low
    if shipping_cost > (median * 0.30) or (median < 25 and shipping_cost > 12):
        action = "SELL LOCAL"
        color = "#3B82F6" # Electric Blue
        platform = "FB Marketplace"
        time_to_sell = "1-3 Days"
        tip = "High shipping costs detected. Selling locally will net you more cash."
    else:
        # Standard List Logic
        est_fees = (median * 0.1325) + 0.30
        if median > (cost + shipping_cost + est_fees + 5): # Ensure at least $5 profit
            action = "LIST IT"
            color = "#10B981" # Emerald Green
            platform = "eBay"
            tip = "Strong market value. Verified sales suggest high demand."
        else:
            action = "DONATE / BUNDLE"
            color = "#EF4444" # Red
            platform = "Local/Lot"
            tip = "Margins are too thin after fees and shipping."

    # Velocity based on volume of verified sold comps
    if count > 15:
        time_to_sell = "1–2 weeks"
    elif count > 5:
        time_to_sell = "2–4 weeks"
    else:
        time_to_sell = "4–8 weeks"

    # 4. Dynamic Strategic Pricing Tiers
    prices = {
        "fast": round(median * 0.90, 2),      # 10% below market to undercut
        "balanced": round(median, 2),         # Fair market value
        "max": round(median * 1.15, 2)        # 15% above for patience
    }

    # 5. Financial Calculation Engine
    # Standard eBay fee estimate (approx 13%)
    est_fees = (median * 0.1325) + 0.30
    net_profit = round(median - cost - shipping_cost - est_fees, 2)
    roi = round((net_profit / cost) * 100) if cost > 0 else 0

    return {
        "success": True,
        "verdict": action,
        "color_code": color,
        "best_platform": platform,
        "time_to_sell": time_to_sell,
        "tip": tip,
        "pricing_tiers": prices,
        "net_profit": net_profit,
        "roi": roi,
        "metrics": {
            "median": median,
            "count": count
        }
    }
