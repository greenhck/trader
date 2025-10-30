import json
import os
import sys
import yfinance as yf
from datetime import datetime
import gspread 
from google.oauth2.service_account import Credentials

# ==========================================================
# ⭐⭐⭐ आपकी जानकारी (पहले से भरी हुई) ⭐⭐⭐
# ==========================================================
# 1. आपकी Google Sheet ID (दोनों वॉचलिस्ट और लाइव डेटा के लिए)
SHEET_ID = '1UANOBVncsHF-B_BURxm-dfGmho9pIhZPE2TcN_OK0Ws' 

# 2. वॉचलिस्ट शीट में वह कॉलम नाम जहाँ स्टॉक्स लिखे हैं
STOCKS_COLUMN_NAME = 'Stocks' 

# 3. वॉचलिस्ट डेटा टैब का नाम
WATCHLIST_TAB_NAME = 'Watchlists' 

# 4. लाइव डेटा शीट का टैब नाम (जहाँ डेटा लिखा जाएगा)
LIVE_DATA_TAB_NAME = 'LivePrices'
# ==========================================================

def initialize_google_sheets_client():
    """Initializes gspread client using the service account JSON."""
    try:
        # हम मानते हैं कि GitHub Secret 'GCP_SHEETS_SERVICE_ACCOUNT' में JSON है
        cred_json = os.environ.get('GCP_SHEETS_SERVICE_ACCOUNT')
        if not cred_json:
            raise ValueError("❌ Error: GCP_SHEETS_SERVICE_ACCOUNT GitHub Secret not found.")
        
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 
                  'https://www.googleapis.com/auth/drive']
        
        creds_info = json.loads(cred_json)
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        print("✓ Google Sheets client initialized successfully.")
        return client
        
    except Exception as e:
        print(f"❌ Error initializing Google Sheets client: {e}")
        # सुनिश्चित करें कि आपने SERVICE ACCOUNT JSON को सही ढंग से कॉपी किया है
        sys.exit(1)

def get_unique_stocks_from_sheets(gc):
    """Reads all unique stock symbols from the Watchlist Sheet."""
    try:
        spreadsheet = gc.open_by_key(SHEET_ID)
        # Tab का नाम उपयोग करें
        worksheet = spreadsheet.worksheet(WATCHLIST_TAB_NAME) 
        
        # get_all_records() headers का उपयोग करके डेटा को डिक्शनरी के रूप में पढ़ता है
        data = worksheet.get_all_records()
        unique_stocks = set()
        
        for row in data:
            stocks_string = row.get(STOCKS_COLUMN_NAME, '') 
            if stocks_string:
                # स्टॉक्स को कॉमा से अलग करें
                stocks_list = [s.strip() for s in stocks_string.split(',') if s.strip()]
                unique_stocks.update(stocks_list)

        print(f"✓ Found {len(unique_stocks)} unique stock symbols from Sheet.")
        return list(unique_stocks)
        
    except Exception as e:
        print(f"❌ Error reading data from Watchlist Sheet: {e}. Check TAB Name or Column Name.")
        # यदि टैब मौजूद नहीं है तो यहाँ एरर आएगा
        return []

def fetch_stock_data(symbol):
    """Fetch real-time data for a single stock"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        history = stock.history(period="1d") 
        
        if history.empty: return None
        
        current_price = history['Close'].iloc[-1]
        previous_close = info.get('previousClose', current_price) 
        
        try:
            prev_close_history = stock.history(period="2d", interval="1d")
            if len(prev_close_history) > 1:
                previous_close = prev_close_history['Close'].iloc[-2]
        except Exception:
             pass

        change = current_price - previous_close
        percent_change = (change / previous_close) * 100 if previous_close else 0
        
        return {
            'symbol': symbol,
            'ltp': round(current_price, 2),
            'change': round(change, 2),
            'percent': round(percent_change, 2),
            'lastUpdated': datetime.now().isoformat(),
        }
    
    except Exception as e:
        print(f"⚠️  Error fetching {symbol}: {e}")
        return None

def update_data_in_sheets(gc, all_stock_data):
    """Writes all live stock data to the Live Data Sheet."""
    try:
        spreadsheet = gc.open_by_key(SHEET_ID)
        worksheet = spreadsheet.worksheet(LIVE_DATA_TAB_NAME) 
        
        headers = ['symbol', 'ltp', 'change', 'percent', 'lastUpdated']
        
        data_rows = [headers]
        for symbol, data in all_stock_data.items():
            if data:
                data_rows.append([data.get(h) for h in headers])

        # पुराने डेटा को साफ़ करें और नया डेटा लिखें
        worksheet.clear()
        worksheet.update('A1', data_rows) 
        
        print(f"\n✓ Successfully updated {len(all_stock_data)} stock prices in Google Sheet '{LIVE_DATA_TAB_NAME}'.")
        return True
        
    except Exception as e:
        print(f"❌ Error updating Live Data Sheet: {e}. Check TAB Name or Sheet permissions.")
        # यदि 'LivePrices' टैब मौजूद नहीं है या शेयरिंग में कोई समस्या है तो यहाँ एरर आएगा।
        return False

def main():
    print("\n" + "="*60)
    print("🔄 Starting Google Sheets Stock Data Update")
    print("="*60 + "\n")
    
    gc = initialize_google_sheets_client()
    
    print("📊 Fetching unique stocks from Watchlist Sheet...")
    unique_symbols = get_unique_stocks_from_sheets(gc)
    
    if not unique_symbols:
        print("\n⚠️  No stocks found in the Watchlist Sheet. Skipping stock update.")
        # यह सुनिश्चित करें कि Watchlists टैब में डेटा है
        return

    print(f"\n📈 Fetching data for {len(unique_symbols)} unique stock(s)...")
    all_stock_data = {}
    
    for symbol in unique_symbols:
        stock_data = fetch_stock_data(symbol)
        if stock_data:
            all_stock_data[symbol] = stock_data
        # यदि yfinance से डेटा नहीं मिलता है, तो हम आगे बढ़ेंगे, त्रुटि को नज़रअंदाज़ करेंगे

    print("\n💾 Writing live data back to Google Sheet...")
    update_data_in_sheets(gc, all_stock_data)
    
    print("\n" + "="*60)
    print("📋 Update Summary")
    print("="*60)
    print(f"✓ Stocks fetched: {len(all_stock_data)}")
    print(f"🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()

# EOF
