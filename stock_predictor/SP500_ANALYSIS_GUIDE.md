# S&P 500 Stock Analysis Guide

## Quick Start

### Analyze Top 500 S&P 500 Stocks
```bash
python analyze_sp500.py
```

This will:
- Analyze up to 500 S&P 500 stocks
- Rank them by predicted return and confidence
- Save results to CSV file
- Save predictions to database (automatically)

### Customize Analysis
```bash
# Analyze only top 100 stocks
python analyze_sp500.py --limit 100

# Use 2 years of data instead of 5
python analyze_sp500.py --period 2y

# Only show stocks with confidence >= 60%
python analyze_sp500.py --min-confidence 0.6

# Don't save to database
python analyze_sp500.py --no-db
```

## Command Options

### Required
None - runs with defaults

### Optional Flags
- `--limit N` - Maximum number of stocks to analyze (default: 500)
- `--period PERIOD` - Historical data period:
  - `2y` - 2 years
  - `5y` - 5 years (default, recommended)
  - `10y` - 10 years
  - `max` - Maximum available
- `--min-confidence FLOAT` - Minimum confidence threshold 0.0-1.0 (default: 0.5)
- `--no-db` - Don't save predictions to database

## Examples

### Basic Analysis
```bash
# Analyze all 500 stocks (default)
python analyze_sp500.py
```

### Quick Analysis (Top 50)
```bash
# Analyze only top 50 stocks (faster)
python analyze_sp500.py --limit 50
```

### High Confidence Only
```bash
# Only stocks with 70%+ confidence
python analyze_sp500.py --min-confidence 0.7
```

### Custom Period
```bash
# Use 2 years of data
python analyze_sp500.py --period 2y
```

## Output

The script will:
1. **Display progress** as it analyzes each stock
2. **Show top 20 opportunities** ranked by composite score
3. **Save full results** to CSV file: `sp500_analysis_YYYYMMDD.csv`
4. **Save to database** (unless `--no-db` is used)

### Output Format
```
Rank    Symbol   Return %     Confidence   Price        Rec    P/E
------------------------------------------------------------------
1       AAPL     +2.45%       85.3%        $175.23      BUY   28.5
2       MSFT     +1.89%       82.1%        $378.45      BUY   32.1
...
```

### CSV File Columns
- `symbol` - Stock ticker
- `current_price` - Current stock price
- `predicted_price` - Predicted price
- `predicted_return_pct` - Expected return percentage
- `confidence` - Model confidence (0-1)
- `recommendation` - BUY/SELL/HOLD
- `risk_level` - LOW/MEDIUM/HIGH
- `pe_ratio` - P/E ratio
- `dividend_yield` - Dividend yield
- `news_sentiment` - News sentiment score
- `composite_score` - Combined return × confidence score

## Performance

### Time Estimates
- **50 stocks**: ~15-20 minutes
- **100 stocks**: ~30-40 minutes
- **500 stocks**: ~2-3 hours

The script includes delays to avoid rate limiting. Each stock takes ~30-60 seconds to analyze.

### Tips for Faster Analysis
1. Start with `--limit 50` to test
2. Use `--period 2y` for faster data fetching
3. Increase `--min-confidence` to filter results early

## Database Integration

All predictions are automatically saved to `stock_predictions.db`:
- Track performance over time
- Compare predictions vs actual results
- Analyze model accuracy

Query the database:
```python
from performance_db import PerformanceDB

db = PerformanceDB()
stats = db.get_performance_stats(symbol='AAPL', days=30)
```

## Troubleshooting

### Rate Limiting
If you see errors about rate limiting:
- The script includes delays, but you may need to wait longer
- Try analyzing fewer stocks at once (`--limit 50`)

### Missing Stocks
Some stocks may fail due to:
- Insufficient historical data
- Delisted stocks
- Data availability issues

The script will skip these and continue.

### Wikipedia Access
If Wikipedia is blocked, the script will use a sample list of common S&P 500 stocks. For the full list, ensure internet access.

## Best Practices

1. **Start Small**: Test with `--limit 50` first
2. **Use 5-year period**: Best balance of data and relevance
3. **Filter by confidence**: Use `--min-confidence 0.6` for higher quality
4. **Review CSV**: Check the full results in the CSV file
5. **Track over time**: Use database to see how predictions perform

## Example Workflow

```bash
# 1. Quick test with 20 stocks
python analyze_sp500.py --limit 20

# 2. Full analysis of top opportunities
python analyze_sp500.py --limit 200 --min-confidence 0.6

# 3. Review results
# Check sp500_analysis_YYYYMMDD.csv

# 4. Check database performance later
python -c "from performance_db import PerformanceDB; db = PerformanceDB(); print(db.get_performance_stats())"
```

