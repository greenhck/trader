# Paper Trading Web App

A real-time paper trading application for Indian stock markets with live data from Yahoo Finance using yfinance.

## Features

- 📊 Real-time stock data from NSE/BSE via yfinance
- 🔄 Automatic data updates via GitHub Actions
- 📱 Mobile-first responsive design
- 🔥 Firebase integration for user data
- 📝 Notes and alerts for stocks
- 📈 GTT (Good Till Triggered) order creation
- 👁️ Multiple watchlists support

## Setup Instructions

### 1. Local Development

To run this locally and test the data fetching:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Fetch market data manually
python fetch_market_data.py
```

### 2. GitHub Actions Setup

The app uses GitHub Actions to automatically fetch market data every 15 minutes during market hours (9:15 AM to 3:30 PM IST, Monday-Friday).

**Steps to enable:**

1. **Push this repository to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit with yfinance integration"
   git branch -M main
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Enable GitHub Actions:**
   - Go to your repository on GitHub
   - Click on the "Actions" tab
   - If prompted, enable GitHub Actions for your repository
   - The workflow will automatically run on schedule and on every push to main

3. **Manual Trigger (Optional):**
   - Go to Actions tab → "Update Market Data" workflow
   - Click "Run workflow" to fetch data immediately

### 3. Hosting

You can host this app on:
- **GitHub Pages:** Enable in Settings → Pages → Source: main branch
- **Netlify/Vercel:** Connect your GitHub repo for automatic deployments
- **Firebase Hosting:** Use Firebase CLI to deploy

## How It Works

1. **Python Script (`fetch_market_data.py`):**
   - Uses yfinance to fetch real-time data for Indian stocks (NSE)
   - Fetches major indices (NIFTY 50, NIFTY BANK, SENSEX)
   - Saves data to `market_data.json`

2. **GitHub Actions (`.github/workflows/update_market_data.yml`):**
   - Runs automatically every 15 minutes during market hours
   - Executes the Python script
   - Commits and pushes updated `market_data.json` to the repository

3. **Web App (`rockettrader.html`):**
   - Fetches `market_data.json` on page load
   - Displays real-time stock prices and changes
   - Updates automatically when GitHub Actions updates the JSON file

## Stock Symbols

Current stocks tracked (customizable in `fetch_market_data.py`):

- **s1:** TCS Limited (TCS.NS)
- **s2:** Reliance Industries (RELIANCE.NS)
- **s3:** HDFC Bank (HDFCBANK.NS)
- **s4:** Infosys (INFY.NS)
- **s5:** Wipro (WIPRO.NS)
- **s6:** Tech Mahindra (TECHM.NS)
- **s7:** ICICI Bank (ICICIBANK.NS)

## Customization

### Add More Stocks

Edit `fetch_market_data.py`:

```python
stock_symbols = {
    's1': 'TCS.NS',
    's2': 'RELIANCE.NS',
    # Add your stocks here
    's8': 'SYMBOL.NS',  # Use .NS for NSE, .BO for BSE
}
```

### Change Update Frequency

Edit `.github/workflows/update_market_data.yml`:

```yaml
schedule:
  - cron: '*/30 3-10 * * 1-5'  # Every 30 minutes instead of 15
```

## Technologies Used

- **Frontend:** HTML, Tailwind CSS, JavaScript
- **Backend/Data:** Python, yfinance
- **Database:** Firebase Firestore
- **Authentication:** Firebase Auth
- **CI/CD:** GitHub Actions
- **Icons:** Font Awesome

## Notes

- Market data updates only during NSE trading hours (9:15 AM - 3:30 PM IST)
- yfinance fetches data from Yahoo Finance (may have ~15 minute delay)
- For real-time data with no delay, consider using paid APIs (NSE, BSE official APIs)

## License

MIT License - Feel free to use and modify!
