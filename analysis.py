def analyze_market_data(market_data, cost=0, shipping_cost=0):
    """
    Consumer-Centric Decision Engine
    """
    metrics = market_data.get('metrics', {})
    median = metrics.get('median', 0)
    count = metrics.get('count', 0)
    
    # 1. Velocity Proxy
    if count >= 20:
        time_to_sell = "1–2 weeks"
        velocity_label = "Fast"
    elif 10 <= count < 20:
        time_to_sell = "2–4 weeks"
        velocity_label = "Moderate"
    else:
        time_to_sell = "4–8 weeks"
        velocity_label = "Slow"

    # 2. Pricing Tiers
    prices = {
        "fast": round(median * 0.92, 2),
        "balanced": round(median, 2),
        "max": round(median * 1.08, 2)
    }

    # 3. Financial Calculations (FIX: Ensures non-zero profit)
    est_fees = (median * 0.13) + 0.30
    net_profit = round(median - cost - shipping_cost - est_fees, 2)
    roi = round((net_profit / cost) * 100) if cost > 0 else 0

    # 4. Action Logic
    if median < 15 or net_profit < 5:
        action = "DONATE OR BUNDLE"
        color = "#EF4444"
        tip = "Low margins detected. Effort may exceed profit."
        platform = "Local/Donation"
    elif shipping_cost > (median * 0.35):
        action = "SELL LOCAL"
        color = "#3B82F6"
        tip = "Shipping is too expensive for this item."
        platform = "FB Marketplace"
    else:
        action = "LIST IT"
        color = "#10B981"
        tip = "Strong demand and solid margins. Great opportunity."
        platform = "eBay"

    return {
        "verdict": action,
        "color_code": color,
        "tip": tip,
        "best_platform": platform,
        "time_to_sell": time_to_sell,
        "pricing_tiers": prices,
        "net_profit": net_profit,
        "roi": roi,
        "metrics": {
            "median": median,
            "count": count,
            "confidence_msg": f"Based on {count} recent sales"
        }
    }
