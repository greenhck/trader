#!/usr/bin/env python3
"""
Update Firebase Firestore with real-time stock data from yfinance
Runs via GitHub Actions every 15 minutes
"""
import json
import os
import sys
import yfinance as yf
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Get Firebase credentials from environment variable
        cred_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if not cred_json:
            print("❌ Error: FIREBASE_SERVICE_ACCOUNT environment variable not found")
            sys.exit(1)
        
        # Parse credentials
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
        
        # Initialize Firebase app
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        
        print("✓ Firebase initialized successfully")
        return db
    
    except Exception as e:
        print(f"❌ Error initializing Firebase: {e}")
        sys.exit(1)

def fetch_stock_data(symbol):
    """Fetch real-time data for a single stock"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        history = stock.history(period="1d")
        
        if history.empty:
            return None
        
        current_price = history['Close'].iloc[-1]
        previous_close = info.get('previousClose', current_price)
        change = current_price - previous_close
        percent_change = (change / previous_close) * 100 if previous_close else 0
        
        return {
            'symbol': symbol,
            'name': info.get('longName', symbol),
            'ltp': round(current_price, 2),
            'change': round(change, 2),
            'percent': round(percent_change, 2),
            'previousClose': round(previous_close, 2),
            'open': round(history['Open'].iloc[0], 2) if not history.empty else 0,
            'high': round(history['High'].max(), 2) if not history.empty else 0,
            'low': round(history['Low'].min(), 2) if not history.empty else 0,
            'volume': int(history['Volume'].sum()) if not history.empty else 0,
            'exchange': info.get('exchange', 'NSE'),
            'currency': info.get('currency', 'INR'),
            'lastUpdated': datetime.now().isoformat(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    except Exception as e:
        print(f"⚠️  Error fetching {symbol}: {e}")
        return None

def get_stocks_from_watchlists(db):
    """Get all unique stock symbols from all watchlists"""
    try:
        watchlists_ref = db.collection('watchlists')
        docs = list(watchlists_ref.stream())
        
        if not docs:
            print("   ℹ️  No watchlists found in Firebase")
            return []
        
        all_symbols = set()
        watchlist_count = 0
        
        for doc in docs:
            data = doc.to_dict()
            if 'stocks' in data and isinstance(data['stocks'], list):
                all_symbols.update(data['stocks'])
                watchlist_count += 1
        
        print(f"   ✓ Found {watchlist_count} watchlist(s) with {len(all_symbols)} unique stock(s)")
        return list(all_symbols)
    
    except Exception as e:
        print(f"⚠️  Error getting watchlist stocks: {e}")
        return []

def update_stock_in_firebase(db, stock_data):
    """Update or create a stock document in Firebase"""
    try:
        symbol = stock_data['symbol']
        stock_ref = db.collection('stocks').document(symbol)
        stock_ref.set(stock_data, merge=True)
        return True
    
    except Exception as e:
        print(f"⚠️  Error updating {stock_data['symbol']}: {e}")
        return False

def update_indices_in_firebase(db):
    """Update major Indian market indices"""
    indices_symbols = {
        'NIFTY 50': '^NSEI',
        'NIFTY BANK': '^NSEBANK',
        'SENSEX': '^BSESN'
    }
    
    updated_count = 0
    
    for name, symbol in indices_symbols.items():
        try:
            index = yf.Ticker(symbol)
            history = index.history(period="1d")
            
            if not history.empty:
                current_price = history['Close'].iloc[-1]
                previous_close = history['Open'].iloc[0]
                change = current_price - previous_close
                percent_change = (change / previous_close) * 100 if previous_close else 0
                
                index_data = {
                    'name': name,
                    'symbol': symbol,
                    'price': round(current_price, 2),
                    'change': round(change, 2),
                    'percent': round(percent_change, 2),
                    'lastUpdated': datetime.now().isoformat()
                }
                
                # Store in 'indices' collection
                index_ref = db.collection('indices').document(symbol)
                index_ref.set(index_data, merge=True)
                updated_count += 1
        
        except Exception as e:
            print(f"⚠️  Error updating {name}: {e}")
    
    return updated_count

def main():
    """Main function to update Firebase with latest stock data"""
    print("\n" + "="*60)
    print("🔄 Starting Firebase Stock Data Update")
    print("="*60 + "\n")
    
    # Initialize Firebase
    db = initialize_firebase()
    
    # Get all unique stock symbols from user watchlists only
    print("📊 Fetching stocks from user watchlists...\n")
    
    # Only get stocks from watchlists (not from 'stocks' collection)
    all_symbols = get_stocks_from_watchlists(db)
    
    # If no stocks found, skip stock updates
    if not all_symbols:
        print("\n⚠️  No stocks found in user watchlists!")
        print("   💡 Add stocks to your watchlist in the web app first.")
        print("   📊 Indices will still be updated.\n")
    else:
        print(f"\n📈 Total {len(all_symbols)} unique stock(s) to update\n")
    
    # Update each stock
    updated_count = 0
    failed_count = 0
    
    for symbol in all_symbols:
        print(f"Fetching {symbol}...", end=" ")
        stock_data = fetch_stock_data(symbol)
        
        if stock_data:
            if update_stock_in_firebase(db, stock_data):
                print(f"✓ Updated (₹{stock_data['ltp']}, {stock_data['percent']:+.2f}%)")
                updated_count += 1
            else:
                print("✗ Failed to update Firebase")
                failed_count += 1
        else:
            print("✗ Failed to fetch data")
            failed_count += 1
    
    # Update indices
    print("\n📊 Updating market indices...")
    indices_updated = update_indices_in_firebase(db)
    
    # Summary
    print("\n" + "="*60)
    print("📋 Update Summary")
    print("="*60)
    print(f"✓ Stocks updated: {updated_count}")
    print(f"✓ Indices updated: {indices_updated}")
    print(f"✗ Failed: {failed_count}")
    print(f"🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("="*60 + "\n")
    
    if failed_count > 0:
        sys.exit(1)

if __name__ == '__main__':
    main()
