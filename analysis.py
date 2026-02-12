"""
Analysis Layer for ResellSquare
Full pipeline: filter comps > segment condition > trim outliers > compute stats > verdict

Phase 1 accuracy fixes:
- Step 3: Filter out junk comps (parts, broken, etc.)
- Step 4: Segment by condition (never mix New/Used in same median)
- Step 5: IQR outlier trimming
- Step 6: Real confidence scoring (comp count, recency, spread, match quality)
- Step 7: Deterministic profit logic with transparent BUY/SKIP/MAYBE
- Step 8: Data mismatch / mixed variant warnings
"""

from typing import Dict, List, Any, Tuple
import statistics
import re


# ── Step 3: Junk comp filters ──────────────────────────────────────

HARD_FILTER_TERMS = [
        "for parts", "not working", "no power", "as-is", "as is",
        "icloud locked", "mdm locked", "mdm", "cracked", "broken",
        "parts only", "for repair", "read description", "read desc",
        "defective", "faulty", "damaged", "water damage",
        "salvage", "locked", "blacklisted", "bad esn",
]

SOFT_FILTER_TERMS = [
        "lot of", "bundle", "empty box", "box only",
        "manual only", "case only", "untested",
        "for display", "dummy", "replica", "fake",
]


def filter_junk_comps(
        titles: List[str],
        prices: List[float],
        conditions: List[str] = None,
        dates: List[str] = None,
        include_soft: bool = False,
) -> Tuple[List[str], List[float], List[str], List[str], dict]:
        """
            Remove junk/irrelevant comps from the dataset.
                Returns filtered lists + debug stats.
                    """
        if conditions is None:
                    conditions = [""] * len(titles)
                if dates is None:
                            dates = [""] * len(titles)

    filtered_titles = []
    filtered_prices = []
    filtered_conditions = []
    filtered_dates = []
    removed_hard = 0
    removed_soft = 0

    filter_terms = HARD_FILTER_TERMS[:]
    if include_soft:
                filter_terms.extend(SOFT_FILTER_TERMS)

    for i, title in enumerate(titles):
                title_lower = title.lower()
                is_junk = False

        for term in HARD_FILTER_TERMS:
                        if term in title_lower:
                                            is_junk = True
                                            removed_hard += 1
                                            break

                    if not is_junk and include_soft:
                                    for term in SOFT_FILTER_TERMS:
                                                        if term in title_lower:
                                                                                is_junk = True
                                                                                removed_soft += 1
                                                                                break

                                                if not is_junk:
                                                                filtered_titles.append(titles[i])
                                                                filtered_prices.append(prices[i])
            filtered_conditions.append(conditions[i] if i < len(conditions) else "")
            filtered_dates.append(dates[i] if i < len(dates) else "")

    debug = {
                "comps_total": len(titles),
                "comps_removed_hard": removed_hard,
                "comps_removed_soft": removed_soft,
                "comps_after_filter": len(filtered_prices),
    }

    return filtered_titles, filtered_prices, filtered_conditions, filtered_dates, debug


# ── Step 4: Condition segmentation ─────────────────────────────────

CONDITION_MAP_NEW = ["new", "brand new", "new with tags", "new with box", "new other"]
CONDITION_MAP_USED = [
        "used", "pre-owned", "very good", "good", "acceptable",
        "excellent", "like new", "refurbished", "certified refurbished",
        "seller refurbished", "manufacturer refurbished",
]


def segment_by_condition(
        titles: List[str],
        prices: List[float],
        conditions: List[str],
        dates: List[str],
    target_condition: str,
) -> Tuple[List[str], List[float], List[str], List[str]]:
        """
            Filter comps to only matching condition segment.
    target_condition: 'all', 'new', or 'used'
        """
    if target_condition == "all":
                return titles, prices, conditions, dates

    seg_titles = []
    seg_prices = []
    seg_conditions = []
    seg_dates = []

    for i, cond in enumerate(conditions):
        cond_lower = cond.lower().strip()
        match = False

        if target_condition == "new":
                        match = any(c in cond_lower for c in CONDITION_MAP_NEW)
elif target_condition == "used":
            match = any(c in cond_lower for c in CONDITION_MAP_USED)

        # If condition string is empty, try to infer from title
        if not cond_lower:
                        title_lower = titles[i].lower() if i < len(titles) else ""
            if target_condition == "new":
                                match = "new" in title_lower and "like new" not in title_lower
elif target_condition == "used":
                match = any(w in title_lower for w in ["used", "pre-owned", "refurbished", "like new"])
            # If we can't determine, include it for 'all' only
            if not match and target_condition != "all":
                                continue

        if match:
                        seg_titles.append(titles[i])
            seg_prices.append(prices[i])
            seg_conditions.append(conditions[i] if i < len(conditions) else "")
            seg_dates.append(dates[i] if i < len(dates) else "")

    return seg_titles, seg_prices, seg_conditions, seg_dates


# ── Step 5: IQR outlier trimming ───────────────────────────────────

def trim_outliers_iqr(prices: List[float], factor: float = 1.5) -> Tuple[List[float], int]:
        """
            Remove outliers using IQR method.
                Returns trimmed prices and count of removed outliers.
                    """
    if len(prices) < 4:
                return prices, 0

    sorted_p = sorted(prices)
    n = len(sorted_p)
    q1 = sorted_p[n // 4]
    q3 = sorted_p[(3 * n) // 4]
            iqr = q3 - q1

    lower_bound = q1 - factor * iqr
    upper_bound = q3 + factor * iqr

    trimmed = [p for p in prices if lower_bound <= p <= upper_bound]
    removed = len(prices) - len(trimmed)

    return trimmed, removed


# ── Step 6: Real confidence scoring ────────────────────────────────

def calculate_confidence(
        comps_used: int,
        price_spread_pct: float,
        match_quality: str = "keyword",
        time_window_days: int = 90,
) -> Dict[str, Any]:
        """
            Build a confidence score from real signals.
                """
    reasons = []

    # Comp count score (0-30)
    if comps_used >= 30:
                count_score = 30
        reasons.append(f"{comps_used} comps (strong sample)")
elif comps_used >= 15:
        count_score = 22
        reasons.append(f"{comps_used} comps (good sample)")
elif comps_used >= 8:
        count_score = 15
        reasons.append(f"{comps_used} comps (fair sample)")
elif comps_used >= 3:
        count_score = 8
        reasons.append(f"{comps_used} comps (thin sample)")
else:
        count_score = 3
        reasons.append(f"Only {comps_used} comps (very thin)")

    # Price spread score (0-30) — tighter = better
    if price_spread_pct <= 15:
                spread_score = 30
        reasons.append("Tight price range")
elif price_spread_pct <= 30:
        spread_score = 22
elif price_spread_pct <= 50:
        spread_score = 15
        reasons.append("Wide price range")
elif price_spread_pct <= 80:
        spread_score = 8
        reasons.append("Very wide price range")
else:
        spread_score = 3
        reasons.append("Extreme price variance")

    # Match quality score (0-25)
    if match_quality == "model_exact":
                quality_score = 25
        reasons.append("Exact model match")
elif match_quality == "model_partial":
        quality_score = 18
        reasons.append("Partial model match")
elif match_quality == "keyword":
        quality_score = 10
        reasons.append("Keyword match only")
else:
        quality_score = 5
        reasons.append("Loose match")

    # Recency score (0-15)
    if time_window_days <= 30:
                recency_score = 15
elif time_window_days <= 60:
        recency_score = 12
elif time_window_days <= 90:
        recency_score = 8
else:
        recency_score = 4

    total = count_score + spread_score + quality_score + recency_score

    if total >= 75:
                level = "High"
elif total >= 50:
        level = "Medium"
elif total >= 30:
        level = "Low"
else:
        level = "Very Low"

    return {
                "score": min(100, total),
                "level": level,
                "reasons": reasons,
                "comps_used": comps_used,
                "time_window_days": time_window_days,
                "match_quality": match_quality,
    }


# ── Step 8: Mixed variant detection ───────────────────────────────

# Common model-number patterns
MODEL_PATTERNS = [
        r'\b[Aa]\d{4}\b',                    # Apple Axxxx
        r'\b[Mm]\d{4}\b',                    # Apple Mxxxx
        r'\bMK\d{3,4}\w*\b',                 # Apple MKxxxx
        r'\bSM-[A-Z]\d{3,4}\w*\b',           # Samsung SM-Gxxx
        r'\bNX-?\d{3,4}\b',                  # Samsung NX
        r'\b\d{3,5}-\d{3,5}\b',              # Generic part numbers
]


def detect_mixed_variants(titles: List[str]) -> Dict[str, Any]:
        """
            Detect if comps contain mixed product variants/models.
                Returns warning info.
                    """
    model_numbers = set()

    for title in titles:
                for pattern in MODEL_PATTERNS:
                                matches = re.findall(pattern, title)
            model_numbers.update(m.upper() for m in matches)

                              mixed = len(model_numbers) > 1

    return {
                "mixed_variants": mixed,
                "unique_models": list(model_numbers)[:10],
                "model_count": len(model_numbers),
                "warning": (
                                "Mixed variants detected — refine model/spec for accuracy"
                                if mixed else None
                ),
    }


# ── Step 7: Deterministic profit logic ─────────────────────────────

EBAY_FEE_RATE = 0.1325  # 13.25% (final value + payment processing)


def compute_verdict(
        median_price: float,
        cost: float = 0,
        shipping_cost: float = 0,
        confidence_level: str = "Medium",
) -> Dict[str, Any]:
        """
            Deterministic BUY / SKIP / MAYBE verdict.
                Only called when cost is provided.
                    """
    expected_sale = median_price
    fees = round(expected_sale * EBAY_FEE_RATE, 2)
    revenue = expected_sale
    total_cost = cost + shipping_cost
    net_profit = round(revenue - fees - total_cost, 2)
    roi = round((net_profit / total_cost) * 100, 1) if total_cost > 0 else 0
    margin = round((net_profit / revenue) * 100, 1) if revenue > 0 else 0

    # Verdict rules
    if confidence_level in ("Low", "Very Low"):
                verdict = "MAYBE"
        verdict_reason = "Low confidence data — verify comps manually"
elif net_profit <= 0:
        verdict = "SKIP"
        verdict_reason = f"Negative profit: -${abs(net_profit):.2f}"
elif margin >= 20 and roi >= 30:
        verdict = "BUY"
        verdict_reason = f"${net_profit:.2f} profit, {roi}% ROI"
elif margin >= 10:
        verdict = "MAYBE"
        verdict_reason = f"Thin margin: {margin}% — worth it at scale?"
else:
        verdict = "SKIP"
        verdict_reason = f"Only {margin}% margin, {roi}% ROI"

    return {
                "verdict": verdict,
                "verdict_reason": verdict_reason,
                "expected_sale_price": expected_sale,
                "ebay_fees": fees,
                "net_profit": net_profit,
                "roi": roi,
                "margin": margin,
    }


# ── Main analysis pipeline ─────────────────────────────────────────

def analyze_market_data(
        raw_data: Dict[str, Any],
        condition: str = "all",
        cost: float = 0,
        shipping_cost: float = 0,
) -> Dict[str, Any]:
        """
            Full analysis pipeline:
                1. Extract raw data
                    2. Filter junk comps
                        3. Segment by condition
                            4. Trim outliers (IQR)
                                5. Compute stats
                                    6. Build confidence
                                        7. Detect mixed variants
                                            8. Compute verdict (if cost provided)
                                                """
    titles = raw_data.get("titles", [])
    prices = raw_data.get("prices", [])
    conditions = raw_data.get("conditions", [])
    dates = raw_data.get("dates", [])

    if not prices:
                return {
                                "success": False,
                                "error": "No pricing data available",
                }

    # Step 3: Filter junk comps
    titles, prices, conditions, dates, filter_debug = filter_junk_comps(
                titles, prices, conditions, dates, include_soft=True
    )

    if not prices:
                return {
                                "success": False,
                                "error": "All comps filtered out (junk/parts). Try a more specific search.",
            "debug": filter_debug,
                }

    # Step 4: Segment by condition
    seg_titles, seg_prices, seg_conditions, seg_dates = segment_by_condition(
                titles, prices, conditions, dates, condition
    )

    # Fall back to all if segmentation yields too few
    if len(seg_prices) < 3 and condition != "all":
                seg_titles, seg_prices, seg_conditions, seg_dates = titles, prices, conditions, dates
        condition_fallback = True
else:
        condition_fallback = False

    # Step 5: Trim outliers
    trimmed_prices, outliers_removed = trim_outliers_iqr(seg_prices)

    if not trimmed_prices:
                trimmed_prices = seg_prices
        outliers_removed = 0

    # Step 5b: Compute stats
    count = len(trimmed_prices)
    avg_price = round(statistics.mean(trimmed_prices), 2)
    median_price = round(statistics.median(trimmed_prices), 2)
    min_price = round(min(trimmed_prices), 2)
    max_price = round(max(trimmed_prices), 2)
    price_range = max_price - min_price
    spread_pct = round((price_range / avg_price) * 100, 1) if avg_price > 0 else 0

    # Step 6: Confidence
    confidence = calculate_confidence(
                comps_used=count,
                price_spread_pct=spread_pct,
                match_quality="keyword",
                time_window_days=90,
    )

    # Step 8: Mixed variant detection
    variant_info = detect_mixed_variants(seg_titles)

    # If mixed variants, degrade confidence
    if variant_info["mixed_variants"]:
                confidence["score"] = max(0, confidence["score"] - 15)
        if confidence["score"] < 50:
                        confidence["level"] = "Low"
elif confidence["score"] < 75:
            confidence["level"] = "Medium"
                                confidence["reasons"].append("Mixed variants detected")

    # Volatility
    volatility = spread_pct

    # Market signal
    if volatility <= 20:
                market_signal = "stable"
elif volatility >= 50:
        market_signal = "volatile"
else:
        market_signal = "moderate"

    # Step 7: Verdict (if cost provided)
    verdict_data = None
    if cost > 0:
                verdict_data = compute_verdict(
                                median_price=median_price,
                                cost=cost,
                                shipping_cost=shipping_cost,
                                confidence_level=confidence["level"],
                )

    # Build debug payload (Step 18)
    debug = {
                **filter_debug,
                "comps_removed_outliers": outliers_removed,
                "comps_used": count,
                "condition_requested": condition,
                "condition_fallback": condition_fallback,
                "match_quality": "keyword",
    }

    # Recent sales from filtered data (use seg_ arrays, pre-outlier for display)
    recent_sales = []
    for i in range(min(15, len(seg_titles))):
                sale = {
                                "title": seg_titles[i],
                                "price": seg_prices[i],
                }
        if i < len(seg_conditions) and seg_conditions[i]:
                        sale["condition"] = seg_conditions[i]
        if i < len(seg_dates) and seg_dates[i]:
                        sale["date"] = seg_dates[i]
        recent_sales.append(sale)

    return {
                "success": True,
                "pricing": {
                                "count": count,
                                "avg_price": avg_price,
                                "median_price": median_price,
                                "min_price": min_price,
                                "max_price": max_price,
                                "price_range": round(price_range, 2),
                },
                "velocity": {
                                "volatility": volatility,
                                "market_signal": market_signal,
                },
                "confidence": confidence,
                "variant_info": variant_info,
                "verdict": verdict_data,
                "recent_sales": recent_sales,
                "debug": debug,
    }
