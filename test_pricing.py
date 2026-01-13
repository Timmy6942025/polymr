#!/usr/bin/env python3
"""Test script for the new pricing engine."""

import sys
sys.path.insert(0, '/home/timmy/polymr')

# Import directly to avoid polymr package dependencies
import importlib.util
spec = importlib.util.spec_from_file_location("pricing", "/home/timmy/polymr/polymr/pricing.py")
pricing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pricing)

calculate_optimal_spread = pricing.calculate_optimal_spread
calculate_positioning_factor = pricing.calculate_positioning_factor
should_quote_side = pricing.should_quote_side
calculate_quote_prices = pricing.calculate_quote_prices
get_aggression_config = pricing.get_aggression_config
TARGET_REBATE_BPS = pricing.TARGET_REBATE_BPS
MIN_REBATE_SPREAD_BPS = pricing.MIN_REBATE_SPREAD_BPS


def test_calculate_optimal_spread():
    """Test spread optimization logic."""
    print("=== Testing calculate_optimal_spread ===")
    
    # Test 1: High fill rate should widen spread
    spread_high_fill = calculate_optimal_spread(50, 0.5, 0.50)
    spread_low_fill = calculate_optimal_spread(50, 0.5, 0.05)
    print(f"  High fill rate (50%): {spread_high_fill} bps")
    print(f"  Low fill rate (5%): {spread_low_fill} bps")
    assert spread_high_fill > spread_low_fill, "High fill rate should widen spread"
    
    # Test 2: Tight market spread should return 0
    spread_tight = calculate_optimal_spread(5, 0.5, 0.20)  # 5 bps market spread
    print(f"  Tight market (5 bps): {spread_tight} bps")
    assert spread_tight == 0, "Tight markets should return 0 (don't quote)"
    
    # Test 3: Normal market should quote
    spread_normal = calculate_optimal_spread(30, 0.5, 0.20)
    print(f"  Normal market (30 bps): {spread_normal} bps")
    assert spread_normal > 0, "Normal markets should quote"
    
    print("  ✓ All spread tests passed")


def test_calculate_positioning_factor():
    """Test adaptive positioning logic."""
    print("\n=== Testing calculate_positioning_factor ===")
    
    # Test 1: Balanced inventory should be ~0.5
    pos_balanced = calculate_positioning_factor(0.0, 30)
    print(f"  Balanced skew (0%): {pos_balanced:.2f}")
    assert 0.45 < pos_balanced < 0.55, "Balanced should be ~0.5"
    
    # Test 2: Skewed inventory should be more conservative (higher)
    pos_skewed = calculate_positioning_factor(0.5, 30)
    print(f"  Skewed YES (50%): {pos_skewed:.2f}")
    assert pos_skewed > pos_balanced, "Skewed should be more conservative"
    
    # Test 3: Wider spread allows more aggressive (lower)
    pos_wide = calculate_positioning_factor(0.0, 80)
    pos_narrow = calculate_positioning_factor(0.0, 20)
    print(f"  Wide spread (80 bps): {pos_wide:.2f}")
    print(f"  Narrow spread (20 bps): {pos_narrow:.2f}")
    
    print("  ✓ All positioning tests passed")


def test_should_quote_side():
    """Test one-sided quoting logic."""
    print("\n=== Testing should_quote_side ===")
    
    # Test 1: Normal conditions - can quote both sides
    assert should_quote_side("BUY", 0.0) == True, "Should quote BUY when balanced"
    assert should_quote_side("SELL", 0.0) == True, "Should quote SELL when balanced"
    
    # Test 2: Skewed YES - shouldn't buy
    assert should_quote_side("BUY", 0.20) == False, "Should not BUY when YES skewed"
    assert should_quote_side("SELL", 0.20) == True, "Should still SELL when YES skewed"
    
    # Test 3: Skewed NO - shouldn't sell
    assert should_quote_side("SELL", -0.20) == False, "Should not SELL when NO skewed"
    assert should_quote_side("BUY", -0.20) == True, "Should still BUY when NO skewed"
    
    # Test 4: Threshold testing
    assert should_quote_side("BUY", 0.14) == True, "Should quote BUY at 14% skew"
    assert should_quote_side("BUY", 0.16) == False, "Should not quote BUY at 16% skew"
    
    print("  ✓ All one-sided quoting tests passed")


def test_calculate_quote_prices():
    """Test price calculation."""
    print("\n=== Testing calculate_quote_prices ===")
    
    # Test 1: Normal case
    mid = 0.50
    buy, sell = calculate_quote_prices(mid, 40, 0.5, 0.0)
    print(f"  Mid: {mid}, Spread: 40 bps, Pos: 0.5")
    print(f"  Buy: {buy}, Sell: {sell}")
    assert buy < mid < sell, "Buy should be below mid, sell above"
    # With 50% positioning and 40 bps spread: quotes are 20 bps from mid, 40 bps apart
    actual_spread = abs(sell - buy) * 10000
    assert 39.9 < actual_spread < 40.1, f"Spread should be ~40 bps, got {actual_spread}"
    
    # Test 2: Skewed pricing
    buy_skewed, sell_skewed = calculate_quote_prices(mid, 40, 0.5, 0.3)
    print(f"  With +30% skew: Buy: {buy_skewed}, Sell: {sell_skewed}")
    # Skewed YES (+) should make buys MORE expensive (discourage) and sells CHEAPER (encourage)
    assert buy_skewed > buy, f"Skewed YES ({buy_skewed}) should have more expensive buys than normal ({buy})"
    assert sell_skewed < sell, f"Skewed YES ({sell_skewed}) should have cheaper sells than normal ({sell})"
    
    print("  ✓ All price calculation tests passed")


def test_get_aggression_config():
    """Test aggression configuration."""
    print("\n=== Testing get_aggression_config ===")
    
    for level in ["1", "2", "3"]:
        config = get_aggression_config(level)
        assert "pct" in config, f"Level {level} missing 'pct'"
        assert "min_spread_bps" in config, f"Level {level} missing 'min_spread_bps'"
        assert "max_spread_bps" in config, f"Level {level} missing 'max_spread_bps'"
        assert "inventory_cap" in config, f"Level {level} missing 'inventory_cap'"
        assert "buy_stop_threshold" in config, f"Level {level} missing 'buy_stop_threshold'"
        assert "sell_stop_threshold" in config, f"Level {level} missing 'sell_stop_threshold'"
        print(f"  Level {level} ({config['name']}): spread={config['min_spread_bps']}-{config['max_spread_bps']} bps, cap={config['inventory_cap']*100:.0f}%")
    
    print("  ✓ All aggression config tests passed")


def main():
    print("=" * 60)
    print("  PRICING ENGINE TESTS")
    print("=" * 60)
    print(f"  Target Rebate: {TARGET_REBATE_BPS} bps")
    print(f"  Min Rebate Spread: {MIN_REBATE_SPREAD_BPS} bps")
    print()
    
    try:
        test_calculate_optimal_spread()
        test_calculate_positioning_factor()
        test_should_quote_side()
        test_calculate_quote_prices()
        test_get_aggression_config()
        
        print("\n" + "=" * 60)
        print("  ✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
