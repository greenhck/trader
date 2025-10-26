// API Configuration for yfinance backend
// Update API_URL with your deployed backend URL
const API_CONFIG = {
    API_URL: 'http://localhost:5000',  // Change to your deployed URL
    
    // API Endpoints
    endpoints: {
        search: '/api/search',
        stock: '/api/stock',
        batchStocks: '/api/stocks/batch',
        indices: '/api/indices'
    }
};

// Stock Search Function
async function searchStocksAPI(query) {
    try {
        const url = `${API_CONFIG.API_URL}${API_CONFIG.endpoints.search}?q=${encodeURIComponent(query)}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Search failed: ${response.status}`);
        }
        
        const data = await response.json();
        return data.results || [];
    } catch (error) {
        console.error('Error searching stocks:', error);
        return [];
    }
}

// Fetch Single Stock Data
async function fetchStockData(symbol) {
    try {
        const url = `${API_CONFIG.API_URL}${API_CONFIG.endpoints.stock}/${symbol}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch ${symbol}: ${response.status}`);
        }
        
        const data = await response.json();
        return {
            symbol: data.symbol,
            name: data.name,
            ltp: data.ltp,
            change: data.change,
            percent: data.percent,
            exchange: data.exchange,
            previousClose: data.previousClose,
            high: data.high,
            low: data.low,
            volume: data.volume
        };
    } catch (error) {
        console.error(`Error fetching stock ${symbol}:`, error);
        return null;
    }
}

// Fetch Multiple Stocks in Batch
async function fetchBatchStocks(symbols) {
    try {
        const url = `${API_CONFIG.API_URL}${API_CONFIG.endpoints.batchStocks}`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ symbols })
        });
        
        if (!response.ok) {
            throw new Error(`Batch fetch failed: ${response.status}`);
        }
        
        const data = await response.json();
        return data.stocks || {};
    } catch (error) {
        console.error('Error fetching batch stocks:', error);
        return {};
    }
}

// Fetch Market Indices
async function fetchIndices() {
    try {
        const url = `${API_CONFIG.API_URL}${API_CONFIG.endpoints.indices}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch indices: ${response.status}`);
        }
        
        const data = await response.json();
        return data.indices || [];
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
