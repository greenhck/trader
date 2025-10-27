// API Configuration - Direct Yahoo Finance API (No backend needed!)
// 100% Serverless - Works directly from browser
// Just host on GitHub Pages and it works!

const API_CONFIG = {
    YAHOO_FINANCE_API: 'https://query1.finance.yahoo.com/v1',
    YAHOO_FINANCE_API_V7: 'https://query1.finance.yahoo.com/v7',
    YAHOO_FINANCE_API_V8: 'https://query2.finance.yahoo.com/v8'
};

// Stock Search Function - Direct Yahoo Finance API
async function searchStocksAPI(query) {
    try {
        // Yahoo Finance autocomplete/search API
        const searchUrl = `https://corsproxy.io/?https://query2.finance.yahoo.com/v1/finance/search?q=${encodeURIComponent(query)}&quotesCount=10&newsCount=0`;
        
        const response = await fetch(searchUrl, {
            headers: {
                'User-Agent': 'Mozilla/5.0'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Search failed: ${response.status}`);
        }
        
        const data = await response.json();
        const quotes = data.quotes || [];
        
        // Format results to match our expected structure
        return quotes.map(quote => ({
            symbol: quote.symbol,
            name: quote.longname || quote.shortname || quote.symbol,
            exchange: quote.exchange || quote.exchDisp || 'Unknown',
            type: quote.quoteType || 'EQUITY',
            currency: quote.currency || 'USD'
        }));
        
    } catch (error) {
        console.error('Error searching stocks:', error);
        return [];
    }
}

// Fetch Single Stock Data - Direct Yahoo Finance API
async function fetchStockData(symbol) {
    try {
        // Yahoo Finance quote API
        const quoteUrl = `https://corsproxy.io/?https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?interval=1d&range=1d`;
        
        const response = await fetch(quoteUrl);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch ${symbol}: ${response.status}`);
        }
        
        const data = await response.json();
        const result = data.chart.result[0];
        
        if (!result) {
            throw new Error('No data available for this symbol');
        }
        
        const meta = result.meta;
        const quote = result.indicators.quote[0];
        
        // Calculate current price and changes
        const currentPrice = meta.regularMarketPrice || quote.close[quote.close.length - 1];
        const previousClose = meta.previousClose || meta.chartPreviousClose;
        const change = currentPrice - previousClose;
        const percentChange = (change / previousClose) * 100;
        
        return {
            symbol: symbol,
            name: meta.longName || meta.shortName || symbol,
            ltp: parseFloat(currentPrice.toFixed(2)),
            change: parseFloat(change.toFixed(2)),
            percent: parseFloat(percentChange.toFixed(2)),
            exchange: meta.exchangeName || meta.exchange || 'Unknown',
            previousClose: parseFloat(previousClose.toFixed(2)),
            high: quote.high ? Math.max(...quote.high.filter(v => v !== null)) : currentPrice,
            low: quote.low ? Math.min(...quote.low.filter(v => v !== null)) : currentPrice,
            volume: quote.volume ? quote.volume.reduce((a, b) => (a || 0) + (b || 0), 0) : 0
        };
    } catch (error) {
        console.error(`Error fetching stock ${symbol}:`, error);
        return null;
    }
}

// Fetch Multiple Stocks in Batch - Direct Yahoo Finance API
async function fetchBatchStocks(symbols) {
    try {
        // Fetch all stocks in parallel
        const promises = symbols.map(symbol => fetchStockData(symbol));
        const results = await Promise.all(promises);
        
        // Convert array to object
        const stocksObject = {};
        symbols.forEach((symbol, index) => {
            if (results[index]) {
                stocksObject[symbol] = results[index];
            } else {
                stocksObject[symbol] = { error: 'Failed to fetch' };
            }
        });
        
        return stocksObject;
    } catch (error) {
        console.error('Error fetching batch stocks:', error);
        return {};
    }
}

// Fetch Market Indices - Direct Yahoo Finance API
async function fetchIndices() {
    try {
        const indices = [
            { symbol: '^NSEI', name: 'NIFTY 50' },
            { symbol: '^NSEBANK', name: 'NIFTY BANK' },
            { symbol: '^BSESN', name: 'SENSEX' }
        ];
        
        const results = await Promise.all(
            indices.map(async (index) => {
                try {
                    const data = await fetchStockData(index.symbol);
                    if (data) {
                        return {
                            name: index.name,
                            price: data.ltp,
                            change: data.change,
                            percent: data.percent
                        };
                    }
                    return null;
                } catch (error) {
                    console.error(`Error fetching index ${index.symbol}:`, error);
                    return null;
                }
            })
        );
        
        return results.filter(r => r !== null);
    } catch (error) {
        console.error('Error fetching indices:', error);
        return [];
    }
}

// Export functions
window.searchStocksAPI = searchStocksAPI;
window.fetchStockData = fetchStockData;
window.fetchBatchStocks = fetchBatchStocks;
window.fetchIndices = fetchIndices;
window.API_CONFIG = API_CONFIG;
