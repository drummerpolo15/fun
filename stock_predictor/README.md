# Stock Price Predictor

A comprehensive Python tool that uses predictive statistical models to analyze historical stock prices, recent news, and social media posts to generate buy/sell/hold recommendations with price predictions.

## Features

- **Historical Price Analysis**: Fetches historical stock data and calculates technical indicators (RSI, MACD, Bollinger Bands, Moving Averages)
- **News Sentiment Analysis**: Analyzes recent news articles about stocks using NewsAPI
- **Social Media Sentiment**: Analyzes Reddit and Twitter/X posts for public sentiment
- **Machine Learning Predictions**: Uses ensemble models (Random Forest + Gradient Boosting) to predict future prices
- **Trading Recommendations**: Combines all signals to generate BUY/SELL/HOLD recommendations with confidence scores

## Installation

1. Clone or download this repository

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Download TextBlob corpora (for sentiment analysis):
```bash
python -m textblob.download_corpora
```

## API Keys Setup

The tool works with stock price data out of the box (using yfinance), but for full functionality you'll need API keys:

### NewsAPI (Recommended)
1. Get a free API key from [newsapi.org](https://newsapi.org/)
2. Either:
   - Pass it as argument: `--news-api-key YOUR_KEY`
   - Set environment variable: `export NEWS_API_KEY=YOUR_KEY`

### Reddit API (Optional)
1. Create a Reddit app at [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Set environment variables:
```bash
export REDDIT_CLIENT_ID=your_client_id
export REDDIT_CLIENT_SECRET=your_client_secret
export REDDIT_USER_AGENT="StockPredictor/1.0"
```

### Twitter/X API (Optional)
1. Apply for Twitter Developer account at [developer.twitter.com](https://developer.twitter.com/)
2. Create an app and get Bearer Token
3. Set environment variable:
```bash
export TWITTER_BEARER_TOKEN=your_bearer_token
```

## Usage

### Basic Usage
```bash
python main.py AAPL
```

### Advanced Usage
```bash
# Predict 5 days ahead
python main.py TSLA --days-ahead 5

# Use different historical period
python main.py MSFT --period 2y

# Skip social media analysis
python main.py GOOGL --no-reddit --no-twitter

# Use specific model type
python main.py AAPL --model-type rf  # Random Forest only
python main.py AAPL --model-type gb  # Gradient Boosting only
python main.py AAPL --model-type ensemble  # Both (default)

# With NewsAPI key
python main.py AAPL --news-api-key YOUR_KEY
```

### Command Line Arguments

- `symbol` (required): Stock ticker symbol (e.g., AAPL, TSLA, MSFT)
- `--days-ahead`: Number of days ahead to predict (default: 1)
- `--period`: Historical data period - '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max' (default: '1y')
- `--news-api-key`: NewsAPI key for news analysis
- `--no-reddit`: Skip Reddit analysis
- `--no-twitter`: Skip Twitter analysis
- `--model-type`: ML model type - 'rf', 'gb', or 'ensemble' (default: 'ensemble')

## Output

The script provides:

1. **Current Stock Price**: Latest market price
2. **Predicted Price**: ML model prediction for the target date
3. **Expected Return**: Percentage gain/loss expected
4. **Recommendation**: BUY, SELL, or HOLD with confidence score
5. **Risk Level**: LOW, MEDIUM, or HIGH based on volatility
6. **Signal Breakdown**: Individual scores from technical, sentiment, and prediction signals
7. **Prediction Interval**: 95% confidence interval for the prediction

### Example Output

```
======================================================================
  TRADING RECOMMENDATION
======================================================================

RECOMMENDATION: BUY
Confidence: 75.3%

Current Price: $150.25
Predicted Price: $155.80
Expected Return: +3.69%
Risk Level: MEDIUM

Reasoning: Strong positive signals from multiple sources

Prediction Interval (95% confidence):
  Lower: $152.30
  Upper: $159.30

Signal Breakdown:
  Technical: +0.45 (strength: 0.72)
  Sentiment: +0.38 (strength: 0.65)
  Prediction: +0.52 (strength: 0.85)
  Combined: +0.48
```

## How It Works

### 1. Price Data Collection
- Fetches historical OHLCV (Open, High, Low, Close, Volume) data
- Calculates technical indicators:
  - Simple and Exponential Moving Averages
  - Relative Strength Index (RSI)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - Volume indicators
  - Volatility metrics

### 2. News Analysis
- Fetches recent news articles (last 7 days by default)
- Performs sentiment analysis on article titles and descriptions
- Calculates aggregate sentiment metrics

### 3. Social Media Analysis
- Searches Reddit posts from relevant subreddits (r/stocks, r/investing, etc.)
- Searches Twitter/X for recent tweets about the stock
- Analyzes sentiment of posts and tweets

### 4. Machine Learning Prediction
- Uses ensemble of Random Forest and Gradient Boosting models
- Features include:
  - Historical price patterns
  - Technical indicators
  - News sentiment signals
  - Social media sentiment signals
- Trains on historical data and predicts future price

### 5. Recommendation Engine
- Combines signals with weighted importance:
  - Prediction signal (50% weight)
  - Sentiment signal (30% weight)
  - Technical signal (20% weight)
- Generates BUY/SELL/HOLD recommendation
- Calculates confidence score and risk level

## Model Architecture

The system uses an ensemble approach:

- **Random Forest**: Captures non-linear relationships and feature interactions
- **Gradient Boosting**: Sequential learning for complex patterns
- **Ensemble**: Averages predictions from both models for better accuracy

## Limitations and Disclaimers

⚠️ **IMPORTANT**: This tool is for educational and research purposes only. It is NOT financial advice.

- Stock predictions are inherently uncertain and past performance doesn't guarantee future results
- The model is trained on historical data and may not account for unexpected events
- API rate limits may affect data collection
- Always do your own research and consult with financial advisors before making investment decisions
- The tool uses free/public APIs which may have limitations

## Troubleshooting

### "No data found for symbol"
- Verify the ticker symbol is correct
- Some symbols may not be available in yfinance

### "NewsAPI key is required"
- Get a free key from newsapi.org
- Free tier has rate limits (100 requests/day)

### "Reddit client not initialized"
- Set up Reddit API credentials (see API Keys Setup section)
- Or use `--no-reddit` to skip Reddit analysis

### "Twitter client not initialized"
- Set up Twitter Developer account and get Bearer Token
- Or use `--no-twitter` to skip Twitter analysis

### Model training errors
- Ensure you have enough historical data (at least 50-100 days)
- Try a longer period: `--period 2y`

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is provided as-is for educational purposes.

