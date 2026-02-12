def analyze_market_data(market_data, cost=0, shipping_cost=0):
    """
    Consumer-Centric Decision Engine
    Calculates the 'Best Action' based on profit, velocity, and effort.
    """
    metrics = market_data.get('metrics', {})
    median = metrics.get('median', 0)
    count = metrics.get('count', 0)
    
    # 1. TIME TO SELL ESTIMATE (Velocity Proxy)
    # Based on recent sold volume in a 90-day window
    if count >= 20:
        time_to_sell = "1–2 weeks"
        velocity_label = "Fast"
    elif 10 <= count < 20:
        time_to_sell = "2–4 weeks"
        velocity_label = "Moderate"
    elif 3 <= count < 10:
        time_to_sell = "4–8 weeks"
        velocity_label = "Slow"
    else:
        time_to_sell = "May take months"
        velocity_label = "Very Slow"

    # 2. PRICING STRATEGY TIERS
    # Provides users with options based on how fast they want to move the item
    prices = {
        "fast": round(median * 0.92, 2),     # 8% below median
        "balanced": round(median, 2),
        "max": round(median * 1.08, 2)      # 8% above median
    }

    # 3. ACTION-BASED VERDICT LOGIC
    # Rough eBay fee estimate (13% + 0.30)
    est_fees = (median * 0.13) + 0.30
    net_profit = median - cost - shipping_cost - est_fees
    
    # Logic path for Action Recommendation
    if count < 3:
        action = "REFINE MODEL"
        tip = "Multiple variants detected. Select exact model for a better estimate."
        platform = "Manual Research"
        color_code = "#F59E0B" # Amber
    
    elif median < 15 or net_profit < 8:
        action = "DONATE OR BUNDLE"
        tip = "Not worth listing individually after fees and shipping effort."
        platform = "Local Donation"
        color_code = "#EF4444" # Red
        
    elif shipping_cost > (median * 0.35):
        action = "SELL LOCAL"
        tip = "Shipping costs eat too much profit. Try local buyers first."
        platform = "Facebook Marketplace"
        color_code = "#3B82F6" # Blue
        
    elif velocity_label == "Slow" or velocity_label == "Very Slow":
        action = "QUICK SALE"
        tip = "Low demand detected. Price under median to sell faster."
        platform = "eBay / Mercari"
        prices["balanced"] = prices["fast"] # Recommend aggressive price
        color_code = "#8B5CF6" # Purple
        
    else:
        action = "LIST IT"
        tip = "Strong demand and solid margins. This is a great opportunity."
        platform = "eBay"
        color_code = "#10B981" # Green

    return {
        "success": True,
        "verdict": action,
        "color_code": color_code,
        "tip": tip,
        "best_platform": platform,
        "time_to_sell": time_to_sell,
        "pricing_tiers": prices,
        "metrics": {
            "median": median,
            "count": count,
            "confidence_msg": f"Based on {count} recent sales (90 days)"
        }
    }
