import statistics

def analyze_market_data(raw_data, condition='used', cost=0.0, shipping_cost=0.0):
    """
    Advanced Decision Engine Logic
    1. Filter junk (parts/broken)
    2. Segment by condition (New vs Used)
    3. Remove outliers (IQR method)
    4. Compute Profit & Verdict
    """
    
    # --- 1. SETUP & BASIC CHECKS ---
    listings = raw_data.get('listings', [])
    if not listings:
        return {'success': False, 'error': 'No data found'}

    # Clean inputs
    condition = condition.lower().strip()
    
    # Define filters
    junk_terms = [
        'parts', 'repair', 'broken', 'defective', 'bad esn', 'icloud', 
        'locked', 'read', 'as-is', 'untested', 'box only', 'case only', 'dummy'
    ]
    
    clean_prices = []
    
    # --- 2. FILTERING PIPELINE ---
    for item in listings:
        title = item.get('title', '').lower()
        price = float(item.get('price', 0))
        item_condition = item.get('condition', 'used').lower()

        # A. Junk Filter
        if any(term in title for term in junk_terms):
            continue
            
        # B. Condition Segmentation
        # If user wants "New", only allow New.
        if condition == 'new' and 'new' not in item_condition:
            continue
        # If user wants "Used", reject New (skew) and Parts (junk)
        if condition == 'used' and 'new' in item_condition:
            continue

        clean_prices.append(price)

    # --- 3. STATISTICAL ANALYSIS ---
    count = len(clean_prices)
    
    if count < 2:
        return {
            'success': True,
            'verdict': {'verdict': 'SKIP', 'net_profit': 0, 'roi': 0, 'ebay_fees': 0},
            'pricing': {'count': 0, 'median_price': 0, 'min_price': 0, 'max_price': 0},
            'confidence': {'level': 'Low', 'reasons': ['Not enough data']},
            'variant_info': {'mixed_variants': False, 'warning': ''}
        }

    # Sort
    clean_prices.sort()

    # Outlier Removal (Interquartile Range - IQR)
    if count >= 4:
        q1_idx = int(count * 0.25)
        q3_idx = int(count * 0.75)
        q1 = clean_prices[q1_idx]
        q3 = clean_prices[q3_idx]
        iqr = q3 - q1
        
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        
        # Keep only prices inside the bounds
        clean_prices = [p for p in clean_prices if lower_bound <= p <= upper_bound]
        
    # Re-calculate after trimming
    final_count = len(clean_prices)
    if final_count == 0:
        # Fallback if aggressive trimming killed everything
        return {'success': False, 'error': 'Data too volatile'}

    median_price = statistics.median(clean_prices)
    min_price = clean_prices[0]
    max_price = clean_prices[-1]

    # --- 4. FINANCIAL MATH ---
    # eBay Fees (~13.25% + $0.30)
    fees = (median_price * 0.1325) + 0.30
    
    # Net Profit
    net_profit = median_price - fees - shipping_cost - cost
    
    # ROI
    roi = (net_profit / cost * 100) if cost > 0 else 0

    # --- 5. VERDICT GENERATION ---
    verdict = "SKIP"
    reasons = []

    # Confidence Score
    confidence_level = "Medium"
    if final_count > 15: confidence_level = "High"
    if final_count < 5: confidence_level = "Low"
    
    # Verdict Rules
    if cost == 0:
        verdict = "CHECK"
        reasons.append("Enter cost to see profit")
    elif net_profit > 15 and roi > 25:
        verdict = "BUY"
        reasons.append(f"Strong profit (${net_profit:.2f})")
    elif net_profit > 5 and roi > 10:
        verdict = "MAYBE"
        reasons.append("Thin margins")
    else:
        verdict = "SKIP"
        reasons.append(f"Low/Neg profit (${net_profit:.2f})")

    # --- 6. RETURN STRUCTURE (Matches app.py) ---
    return {
        'success': True,
        'pricing': {
            'count': final_count,
            'median_price': median_price,
            'min_price': min_price,
            'max_price': max_price
        },
        'verdict': {
            'verdict': verdict,
            'net_profit': round(net_profit, 2),
            'roi': int(roi),
            'ebay_fees': round(fees, 2)
        },
        'confidence': {
            'level': confidence_level,
            'reasons': reasons
        },
        'variant_info': {
            'mixed_variants': False, # Todo: Add variant logic later
            'warning': ''
        }
    }
