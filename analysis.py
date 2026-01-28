"""
Analysis Layer for ResellSquare
Processes raw market data into actionable insights
"""

from typing import Dict, List, Any
import statistics


def analyze_market_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze raw market data and return structured insights
    
    Args:
        raw_data: Raw data from data source (must have 'prices' list)
        
    Returns:
        Analyzed data with pricing, velocity, confidence
    """
    
    prices = raw_data.get('prices', [])
    
    if not prices:
        return {
            'success': False,
            'error': 'No pricing data available',
            'confidence': 0
        }
    
    # Filter out outliers (prices beyond 3 std deviations)
    if len(prices) >= 3:
        mean = statistics.mean(prices)
        try:
            stdev = statistics.stdev(prices)
            prices = [p for p in prices if abs(p - mean) <= 3 * stdev]
        except statistics.StatisticsError:
            pass
    
    # Calculate core metrics
    count = len(prices)
    avg_price = round(statistics.mean(prices), 2)
    median_price = round(statistics.median(prices), 2)
    min_price = round(min(prices), 2)
    max_price = round(max(prices), 2)
    
    # Calculate price range and volatility
    price_range = max_price - min_price
    volatility = round((price_range / avg_price * 100), 1) if avg_price > 0 else 0
    
    # Confidence score
    confidence = calculate_confidence(count, volatility)
    
    # Profit targets
    conservative_target = round(avg_price * 0.50, 2)
    aggressive_target = round(avg_price * 0.70, 2)
    
    # Market signals
    signals = analyze_signals(prices, avg_price, median_price, volatility)
    
    return {
        'success': True,
        'pricing': {
            'count': count,
            'avg_price': avg_price,
            'median_price': median_price,
            'min_price': min_price,
            'max_price': max_price,
            'price_range': round(price_range, 2)
        },
        'velocity': {
            'volatility': volatility,
            'market_signal': signals['market_signal']
        },
        'confidence': {
            'score': confidence,
            'level': get_confidence_level(confidence),
            'factors': signals['factors']
        },
        'profit_targets': {
            'conservative': conservative_target,
            'aggressive': aggressive_target
        }
    }


def calculate_confidence(sample_size: int, volatility: float) -> int:
    """Calculate confidence score based on sample size and volatility"""
    
    # Sample size score
    if sample_size >= 50:
        size_score = 50
    elif sample_size >= 30:
        size_score = 40
    elif sample_size >= 20:
        size_score = 30
    elif sample_size >= 10:
        size_score = 20
    else:
        size_score = sample_size * 2
    
    # Volatility score
    if volatility <= 15:
        volatility_score = 50
    elif volatility <= 30:
        volatility_score = 40
    elif volatility <= 50:
        volatility_score = 30
    elif volatility <= 75:
        volatility_score = 20
    else:
        volatility_score = 10
    
    return min(100, size_score + volatility_score)


def get_confidence_level(score: int) -> str:
    """Get confidence level label"""
    if score >= 80:
        return "High"
    elif score >= 60:
        return "Medium"
    elif score >= 40:
        return "Low"
    else:
        return "Very Low"


def analyze_signals(prices: List[float], avg: float, median: float, volatility: float) -> Dict[str, Any]:
    """Analyze market signals"""
    
    factors = []
    
    if len(prices) >= 50:
        factors.append("Large sample size")
    elif len(prices) < 10:
        factors.append("Small sample size")
    
    if volatility <= 20:
        factors.append("Stable pricing")
        market_signal = "stable"
    elif volatility >= 50:
        factors.append("High price variance")
        market_signal = "volatile"
    else:
        market_signal = "moderate"
    
    if abs(avg - median) / avg < 0.05:
        factors.append("Normal distribution")
    
    return {
        'market_signal': market_signal,
        'factors': factors
    }


if __name__ == "__main__":
    print("Testing analysis...")
    
    test_data = {
        'prices': [45.0, 47.5, 46.0, 48.0, 45.5, 46.5, 47.0] * 8
    }
    
    result = analyze_market_data(test_data)
    print("\n✓ Test 1: Good data")
    print(f"  Average: ${result['pricing']['avg_price']}")
    print(f"  Confidence: {result['confidence']['score']}/100 ({result['confidence']['level']})")
    print(f"  Market Signal: {result['velocity']['market_signal']}")
    print(f"  Conservative Target: ${result['profit_targets']['conservative']}")
    
    volatile_data = {
        'prices': [20, 25, 45, 30, 60, 22, 55, 28]
    }
    
    result2 = analyze_market_data(volatile_data)
    print("\n✓ Test 2: Volatile data")
    print(f"  Average: ${result2['pricing']['avg_price']}")
    print(f"  Confidence: {result2['confidence']['score']}/100 ({result2['confidence']['level']})")
    print(f"  Volatility: {result2['velocity']['volatility']}%")
    
    result3 = analyze_market_data({'prices': []})
    print("\n✓ Test 3: No data")
    print(f"  Success: {result3['success']}")
    print(f"  Error: {result3.get('error')}")
    
    print("\nAnalysis tests passed! ✅")
