#!/usr/bin/env python3
"""
Update Firebase Firestore with real-time stock data from yfinance
Runs via GitHub Actions every 15 minutes

Firebase Structure:
  artifacts/default-app-id/
    ├── users/{userId}/
    │   ├── watchlists/{watchlistId} - User watchlists (READ from here)
    │   └── stocks/{symbol} - User-specific stock data (WRITE here)
    └── indices/{symbol} - Market indices (WRITE here)
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

def get_stocks_from_root_users(db, users):
    """Get stocks from root-level users collection (alternative structure)"""
    user_stocks_map = {}  # user_id -> set of stock symbols
    watchlist_count = 0
    user_count = len(users)
    
    for user_doc in users:
        user_id = user_doc.id
        
        # Get watchlists for this user at root level
        watchlists_ref = db.collection('users').document(user_id).collection('watchlists')
        watchlists = list(watchlists_ref.stream())
        
        for watchlist_doc in watchlists:
            data = watchlist_doc.to_dict()
            if 'stocks' in data and isinstance(data['stocks'], list):
                if user_id not in user_stocks_map:
                    user_stocks_map[user_id] = set()
                user_stocks_map[user_id].update(data['stocks'])
                watchlist_count += 1
                print(f"   → User {user_id[:8]}... has {len(data['stocks'])} stock(s) in watchlist '{watchlist_doc.id}'")
    
    total_stocks = sum(len(stocks) for stocks in user_stocks_map.values())
    if user_stocks_map:
        print(f"\n   ✓ Found {user_count} user(s), {watchlist_count} watchlist(s) with {total_stocks} stock assignments")
    else:
        print(f"\n   ℹ️  Found {user_count} user(s) but no stocks in any watchlists")
    
    return user_stocks_map

def get_stocks_from_watchlists(db):
    """Get all user-specific stock symbols from user watchlists"""
    try:
        # First, let's see ALL collections at root level
        print("   🔍 Checking Firebase structure...")
        print("   📁 Listing all root-level collections...")
        
        collections = db.collections()
        collection_names = []
        for collection in collections:
            collection_names.append(collection.id)
            print(f"      → Found collection: '{collection.id}'")
        
        if not collection_names:
            print("      ⚠️  No collections found at root level!")
            print("      💡 Check Firebase security rules and service account permissions")
            return {}, None
        
        # Now check if artifacts exists
        artifacts_ref = db.collection('artifacts')
        artifacts_docs = list(artifacts_ref.stream())
        
        if not artifacts_docs:
            print("   ⚠️  'artifacts' collection exists but is empty or no documents accessible")
            print("   💡 This is likely a security rules issue")
            print("   🔧 Trying direct path: artifacts/default-app-id/users...")
            
            # Try accessing the known path directly even if we can't list it
            try:
                users_ref = db.collection('artifacts').document('default-app-id').collection('users')
                users = list(users_ref.stream())
                
                if users:
                    print(f"   ✓ SUCCESS! Found {len(users)} user(s) via direct path")
                    app_id = 'default-app-id'
                    
                    user_stocks_map = {}  # user_id -> set of stock symbols
                    watchlist_count = 0
                    user_count = len(users)
                    
                    for user_doc in users:
                        user_id = user_doc.id
                        watchlists_ref = db.collection('artifacts').document(app_id).collection('users').document(user_id).collection('watchlists')
                        watchlists = list(watchlists_ref.stream())
                        
                        for watchlist_doc in watchlists:
                            data = watchlist_doc.to_dict()
                            if 'stocks' in data and isinstance(data['stocks'], list):
                                if user_id not in user_stocks_map:
                                    user_stocks_map[user_id] = set()
                                user_stocks_map[user_id].update(data['stocks'])
                                watchlist_count += 1
                                print(f"   → User {user_id[:8]}... has {len(data['stocks'])} stock(s) in watchlist '{watchlist_doc.id}'")
                    
                    total_stocks = sum(len(stocks) for stocks in user_stocks_map.values())
                    if user_stocks_map:
                        print(f"\n   ✓ Found {user_count} user(s), {watchlist_count} watchlist(s) with {total_stocks} stock assignments")
                        return user_stocks_map, app_id
                    else:
                        print(f"\n   ℹ️  Found {user_count} user(s) but no stocks in any watchlists")
                        return {}, app_id
                        
            except Exception as e:
                print(f"   ⚠️  Direct path failed: {e}")
            
            print("   💡 Checking if data is at root level instead...")
            
            # Try root-level users collection
            users_ref = db.collection('users')
            users = list(users_ref.stream())
            
            if users:
                print(f"   ✓ Found {len(users)} user(s) at root level")
                user_stocks_map = get_stocks_from_root_users(db, users)
                return user_stocks_map, None  # None means root level, no app_id
            else:
                print("   ℹ️  No users found in Firebase")
                return {}, None
        
        # List all app IDs in artifacts
        print(f"\n   ✓ Found artifacts collection with {len(artifacts_docs)} app(s)")
        for app_doc in artifacts_docs:
            print(f"      → App ID: '{app_doc.id}'")
            
            # List subcollections for this app
            app_ref = db.collection('artifacts').document(app_doc.id)
            subcollections = app_ref.collections()
            subcolls = list(subcollections)
            if subcolls:
                for subcoll in subcolls:
                    print(f"         └── Subcollection: '{subcoll.id}'")
        
        # Try to find the correct app ID (try default-app-id first, then others)
        app_id = 'default-app-id'
        users_ref = db.collection('artifacts').document(app_id).collection('users')
        users = list(users_ref.stream())
        
        # If no users found with default-app-id, try the first app ID we found
        if not users and artifacts_docs:
            app_id = artifacts_docs[0].id
            print(f"   🔄 Trying app ID: '{app_id}'")
            users_ref = db.collection('artifacts').document(app_id).collection('users')
            users = list(users_ref.stream())
        
        if not users:
            print(f"   ℹ️  No users found in artifacts/{app_id}/users")
            return {}, app_id
        
        user_stocks_map = {}  # user_id -> set of stock symbols
        watchlist_count = 0
        user_count = 0
        
        print(f"   ✓ Found {len(users)} user(s) in artifacts/{app_id}/users")
        
        # Iterate through all users
        for user_doc in users:
            user_id = user_doc.id
            user_count += 1
            
            # Get watchlists for this user
            watchlists_ref = db.collection('artifacts').document(app_id).collection('users').document(user_id).collection('watchlists')
            watchlists = list(watchlists_ref.stream())
            
            for watchlist_doc in watchlists:
                data = watchlist_doc.to_dict()
                if 'stocks' in data and isinstance(data['stocks'], list):
                    if user_id not in user_stocks_map:
                        user_stocks_map[user_id] = set()
                    user_stocks_map[user_id].update(data['stocks'])
                    watchlist_count += 1
                    print(f"   → User {user_id[:8]}... has {len(data['stocks'])} stock(s) in watchlist '{watchlist_doc.id}'")
        
        total_stocks = sum(len(stocks) for stocks in user_stocks_map.values())
        if user_stocks_map:
            print(f"\n   ✓ Found {user_count} user(s), {watchlist_count} watchlist(s) with {total_stocks} stock assignments")
        else:
            print(f"\n   ℹ️  Found {user_count} user(s) but no stocks in any watchlists")
        
        # Return both user_stocks_map and app_id
        return user_stocks_map, app_id
    
    except Exception as e:
        print(f"⚠️  Error getting watchlist stocks: {e}")
        import traceback
        traceback.print_exc()
        return {}, None

def update_stock_in_firebase(db, stock_data, user_id, app_id=None):
    """Update or create a stock document in Firebase for a specific user"""
    try:
        symbol = stock_data['symbol']
        
        if app_id:
            # Save to: artifacts/{app_id}/users/{user_id}/stocks/{symbol}
            stock_ref = db.collection('artifacts').document(app_id).collection('users').document(user_id).collection('stocks').document(symbol)
        else:
            # Save to root level: users/{user_id}/stocks/{symbol}
            stock_ref = db.collection('users').document(user_id).collection('stocks').document(symbol)
        
        stock_ref.set(stock_data, merge=True)
        return True
    
    except Exception as e:
        print(f"⚠️  Error updating {stock_data['symbol']} for user {user_id[:8]}...: {e}")
        return False

def update_indices_in_firebase(db, app_id=None):
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
                
                if app_id:
                    # Store in: artifacts/{app_id}/indices/{symbol}
                    index_ref = db.collection('artifacts').document(app_id).collection('indices').document(symbol)
                else:
                    # Store at root level: indices/{symbol}
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
    
    # Get user-specific stock symbols from watchlists
    print("📊 Fetching stocks from user watchlists...\n")
    
    # Get mapping of user_id -> stock symbols
    user_stocks_map, app_id = get_stocks_from_watchlists(db)
    
    if app_id:
        print(f"\n💾 Using Firebase path: artifacts/{app_id}/users/{{userId}}/stocks/")
    else:
        print("\n💾 Using root-level Firebase collections: users/{{userId}}/stocks/")
    
    # If no stocks found, skip stock updates
    if not user_stocks_map:
        print("\n⚠️  No stocks found in user watchlists!")
        print("   💡 Add stocks to your watchlist in the web app first.")
        print("   📊 Indices will still be updated.\n")
    else:
        # Count total stock-user pairs
        total_updates = sum(len(stocks) for stocks in user_stocks_map.values())
        print(f"\n📈 Total {total_updates} stock update(s) across {len(user_stocks_map)} user(s)\n")
    
    # Update each stock for each user
    updated_count = 0
    failed_count = 0
    
    for user_id, symbols in user_stocks_map.items():
        print(f"\n👤 Updating stocks for user {user_id[:8]}...")
        for symbol in symbols:
            print(f"  Fetching {symbol}...", end=" ")
            stock_data = fetch_stock_data(symbol)
            
            if stock_data:
                if update_stock_in_firebase(db, stock_data, user_id, app_id):
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
    indices_updated = update_indices_in_firebase(db, app_id)
    
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
