#!/usr/bin/env python3
"""
Flask API for yfinance stock search and data fetching
Provides real-time stock data without storing in JSON
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf

app = Flask(__name__)
CORS(app)  # Enable CORS for browser access

@app.route('/api/search', methods=['GET'])
def search_stocks():
    """
    Search for stocks by symbol or name
    Usage: /api/search?q=TCS
    """
    query = request.args.get('q', '').strip().upper()
    
    if not query or len(query) < 1:
        return jsonify({'error': 'Query parameter required'}), 400
    
    results = []
    
    # Common Indian stock exchanges
    exchanges = ['.NS', '.BO', '']  # NSE, BSE, US stocks
    
    for exchange in exchanges:
        symbol = query + exchange if exchange else query
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # Check if valid stock data exists
            if info.get('symbol') and info.get('longName'):
                results.append({
                    'symbol': symbol,
                    'name': info.get('longName', symbol),
                    'exchange': info.get('exchange', 'NSE' if exchange == '.NS' else 'BSE' if exchange == '.BO' else 'US'),
                    'currency': info.get('currency', 'INR'),
                    'type': info.get('quoteType', 'EQUITY')
                })
        except:
            continue
    
    # Remove duplicates
    unique_results = []
    seen_names = set()
    for result in results:
        if result['name'] not in seen_names:
            unique_results.append(result)
            seen_names.add(result['name'])
    
    return jsonify({
        'query': query,
        'results': unique_results[:10]  # Limit to 10 results
    })

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock_data(symbol):
    """
    Get real-time data for a specific stock
    Usage: /api/stock/TCS.NS
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        history = stock.history(period="1d")
        
        if history.empty:
            return jsonify({'error': 'No data available for this symbol'}), 404
        
        current_price = history['Close'].iloc[-1]
        previous_close = info.get('previousClose', current_price)
        change = current_price - previous_close
        percent_change = (change / previous_close) * 100 if previous_close else 0
        
        return jsonify({
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
            'marketCap': info.get('marketCap', 0),
            'timestamp': history.index[-1].isoformat() if not history.empty else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stocks/batch', methods=['POST'])
def get_batch_stocks():
    """
    Get data for multiple stocks at once
    Usage: POST /api/stocks/batch with JSON body: {"symbols": ["TCS.NS", "RELIANCE.NS"]}
    """
    data = request.get_json()
    symbols = data.get('symbols', [])
    
    if not symbols:
        return jsonify({'error': 'Symbols array required'}), 400
    
    results = {}
    
    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            history = stock.history(period="1d")
            
            if not history.empty:
                current_price = history['Close'].iloc[-1]
                previous_close = info.get('previousClose', current_price)
                change = current_price - previous_close
                percent_change = (change / previous_close) * 100 if previous_close else 0
                
                results[symbol] = {
                    'symbol': symbol,
                    'name': info.get('longName', symbol),
                    'ltp': round(current_price, 2),
                    'change': round(change, 2),
                    'percent': round(percent_change, 2),
                    'exchange': info.get('exchange', 'NSE')
                }
        except Exception as e:
            results[symbol] = {'error': str(e)}
    
    return jsonify({'stocks': results})

@app.route('/api/indices', methods=['GET'])
def get_indices():
    """
    Get current data for major Indian indices
    """
    indices_symbols = {
        'NIFTY 50': '^NSEI',
        'NIFTY BANK': '^NSEBANK',
        'SENSEX': '^BSESN'
    }
    
    results = []
    
    for name, symbol in indices_symbols.items():
        try:
            index = yf.Ticker(symbol)
            history = index.history(period="1d")
            
            if not history.empty:
                current_price = history['Close'].iloc[-1]
                previous_close = history['Open'].iloc[0]
                change = current_price - previous_close
                percent_change = (change / previous_close) * 100 if previous_close else 0
                
                results.append({
                    'name': name,
                    'price': round(current_price, 2),
                    'change': round(change, 2),
                    'percent': round(percent_change, 2)
                })
        except:
            continue
    
    return jsonify({'indices': results})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'yfinance-api'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
