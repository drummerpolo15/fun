# Stock Predictor - Usage Guide

## Quick Start

### Use Improved Model (Automatically Saves to Database)
```bash
python main.py SYMBOL --use-improved --period 5y
```

**Example:**
```bash
python main.py SPY --use-improved --period 5y
python main.py AAPL --use-improved --period 2y
python main.py MSFT --use-improved --period max
```

**What this does:**
- ✅ Uses the improved model (96% better accuracy)
- ✅ Automatically saves prediction to database
- ✅ Uses 5 years of historical data
- ✅ Includes news sentiment analysis
- ✅ Includes fundamental analysis (P/E ratio, etc.)

### Standard Model (No Database)
```bash
python main.py SYMBOL --period 5y
```

**Example:**
```bash
python main.py SPY --period 5y
```

**What this does:**
- Uses the standard model
- Does NOT save to database
- Good for quick predictions

### Standard Model with Database
```bash
python main.py SYMBOL --save-to-db --period 5y
```

## Command Options

### Required
- `SYMBOL` - Stock ticker symbol (e.g., SPY, AAPL, MSFT, TSLA)

### Optional Flags
- `--use-improved` - Use improved model (automatically saves to DB)
- `--save-to-db` - Save prediction to database (only needed for standard model)
- `--period` - Historical data period:
  - `1y` - 1 year (default)
  - `2y` - 2 years
  - `5y` - 5 years (recommended)
  - `10y` - 10 years
  - `max` - Maximum available
- `--days-ahead` - Prediction horizon (default: 1 day)
- `--model-type` - Model type: `rf`, `gb`, or `ensemble` (default: ensemble)
- `--news-api-key` - NewsAPI key (optional, Yahoo Finance is free)
- `--no-reddit` - Skip Reddit analysis
- `--no-twitter` - Skip Twitter analysis

## Examples

### Basic Improved Model Usage
```bash
# Predict SPY for tomorrow
python main.py SPY --use-improved

# Predict AAPL with 5 years of data
python main.py AAPL --use-improved --period 5y

# Predict MSFT for 5 days ahead
python main.py MSFT --use-improved --days-ahead 5
```

### View Database Performance
```python
from performance_db import PerformanceDB

db = PerformanceDB()

# Get performance stats for a stock
stats = db.get_performance_stats(symbol='SPY', days=30)
print(f"Average error: {stats['avg_error_pct']:.2f}%")
print(f"Direction accuracy: {stats['direction_accuracy']:.1f}%")
print(f"Total predictions: {stats['total_predictions']}")
```

### Run Backtests
```bash
# Test multiple stocks
python comprehensive_backtest.py SPY AAPL MSFT

# Compare old vs new model
python test_improvements.py SPY AAPL
```

## Database Location

The database file is created in the same directory:
- **File**: `stock_predictions.db`
- **Type**: SQLite database
- **Tables**: 
  - `predictions` - All predictions
  - `performance_metrics` - Aggregate statistics
  - `feature_importance` - Feature importance scores

## Recommended Usage

**For best accuracy:**
```bash
python main.py SYMBOL --use-improved --period 5y
```

This gives you:
- ✅ Best model (96% better accuracy)
- ✅ Automatic database tracking
- ✅ Optimal historical data period
- ✅ Full analysis (news, fundamentals, technical)

## Troubleshooting

### Database Errors
If you see database errors, the database file will be created automatically. Make sure you have write permissions in the directory.

### No News Data
If news sentiment shows 0 articles, Yahoo Finance may be rate-limited. Wait a few minutes and try again.

### SSL Certificate Errors
If you see SSL errors, the system will try to work around them automatically. If problems persist, update your Python certificates.

## Performance Tips

1. **Use 5-year period** for best balance of data and relevance
2. **Use improved model** for significantly better accuracy
3. **Save to database** to track performance over time
4. **Run backtests** to validate model performance

