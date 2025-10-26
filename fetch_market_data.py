#!/usr/bin/env python3
"""
Fetch real-time stock market data using yfinance and save to JSON
"""
import json
import yfinance as yf
from datetime import datetime

def fetch_stock_data(symbols):
    """Fetch stock data for given symbols"""
    stocks = {}
    
    for symbol_id, ticker_symbol in symbols.items():
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            history = stock.history(period="1d")
            
            if not history.empty:
                current_price = history['Close'].iloc[-1]
                previous_close = info.get('previousClose', current_price)
                change = current_price - previous_close
                percent_change = (change / previous_close) * 100 if previous_close else 0
                
                stocks[symbol_id] = {
                    'id': symbol_id,
                    'name': info.get('longName', ticker_symbol),
                    'ltp': round(current_price, 2),
                    'change': round(change, 2),
                    'percent': round(percent_change, 2),
                    'index': 'NSE',
                    'holding': 0  # Default, can be customized
                }
            else:
                print(f"No data available for {ticker_symbol}")
        except Exception as e:
            print(f"Error fetching {ticker_symbol}: {e}")
    
    return stocks

def fetch_indices_data(indices):
    """Fetch index data for major indices"""
    indices_data = []
    
    for index_name, ticker_symbol in indices.items():
        try:
            index = yf.Ticker(ticker_symbol)
            history = index.history(period="1d")
            
            if not history.empty:
                current_price = history['Close'].iloc[-1]
                previous_close = history['Open'].iloc[0]
                change = current_price - previous_close
                percent_change = (change / previous_close) * 100 if previous_close else 0
                
                indices_data.append({
                    'name': index_name,
                    'price': round(current_price, 2),
                    'change': round(change, 2),
                    'percent': round(percent_change, 2)
                })
            else:
                print(f"No data available for {index_name}")
        except Exception as e:
            print(f"Error fetching {index_name}: {e}")
    
    return indices_data

def main():
    # Define stock symbols (Indian stocks with .NS suffix for NSE)
    stock_symbols = {
        's1': 'TCS.NS',        # TCS Limited
        's2': 'RELIANCE.NS',   # Reliance Industries
        's3': 'HDFCBANK.NS',   # HDFC Bank
        's4': 'INFY.NS',       # Infosys
        's5': 'WIPRO.NS',      # Wipro
        's6': 'TECHM.NS',      # Tech Mahindra
        's7': 'ICICIBANK.NS',  # ICICI Bank
    }
    
    # Define index symbols
    index_symbols = {
        'NIFTY 50': '^NSEI',
        'NIFTY BANK': '^NSEBANK',
        'SENSEX': '^BSESN',
    }
    
    print("Fetching stock data...")
    stocks = fetch_stock_data(stock_symbols)
    
    print("Fetching indices data...")
    indices = fetch_indices_data(index_symbols)
    
    # Combine all data
    market_data = {
        'stocks': stocks,
        'indices': indices,
        'lastUpdated': datetime.now().isoformat(),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Save to JSON file
    with open('market_data.json', 'w') as f:
        json.dump(market_data, f, indent=2)
    
    print(f"✓ Market data saved successfully!")
    print(f"  - {len(stocks)} stocks fetched")
    print(f"  - {len(indices)} indices fetched")
    print(f"  - Last updated: {market_data['timestamp']}")

if __name__ == '__main__':
    main()
