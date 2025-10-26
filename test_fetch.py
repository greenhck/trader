#!/usr/bin/env python3
"""
Quick test script to verify yfinance is working properly
Run this to test the data fetching before deploying
"""
import yfinance as yf

def test_single_stock():
    """Test fetching a single stock"""
    print("Testing yfinance with TCS.NS...")
    try:
        tcs = yf.Ticker("TCS.NS")
        info = tcs.info
        history = tcs.history(period="1d")
        
        if not history.empty:
            print(f"✓ Successfully fetched data for TCS")
            print(f"  Current Price: ₹{history['Close'].iloc[-1]:.2f}")
            print(f"  Company: {info.get('longName', 'TCS')}")
            return True
        else:
            print("✗ No data available")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_index():
    """Test fetching an index"""
    print("\nTesting NIFTY 50 index...")
    try:
        nifty = yf.Ticker("^NSEI")
        history = nifty.history(period="1d")
        
        if not history.empty:
            print(f"✓ Successfully fetched NIFTY 50")
            print(f"  Current Value: {history['Close'].iloc[-1]:.2f}")
            return True
        else:
            print("✗ No data available")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("yfinance Test Script")
    print("=" * 50)
    
    stock_test = test_single_stock()
    index_test = test_index()
    
    print("\n" + "=" * 50)
    if stock_test and index_test:
        print("✓ All tests passed! Ready to use yfinance")
        print("\nRun: python fetch_market_data.py")
    else:
        print("✗ Some tests failed. Check your internet connection")
        print("  and ensure yfinance is installed correctly")
    print("=" * 50)
