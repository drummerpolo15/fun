"""
Performance Database

Stores predictions, actual results, and performance metrics
for tracking model accuracy over time.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
import os


class PerformanceDB:
    """Database for storing stock predictions and performance metrics."""
    
    def __init__(self, db_path: str = "stock_predictions.db"):
        """
        Initialize the performance database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                prediction_date DATE NOT NULL,
                current_price REAL NOT NULL,
                predicted_price REAL NOT NULL,
                predicted_return_pct REAL,
                actual_price REAL,
                actual_return_pct REAL,
                price_error_pct REAL,
                direction_correct INTEGER,
                confidence REAL,
                model_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, prediction_date)
            )
        ''')
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                test_date DATE NOT NULL,
                avg_price_error_pct REAL,
                avg_return_error REAL,
                direction_accuracy REAL,
                test_days INTEGER,
                model_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Feature importance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feature_importance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                feature_name TEXT NOT NULL,
                importance_score REAL,
                model_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_prediction(self, symbol: str, prediction_date: str,
                       current_price: float, predicted_price: float,
                       predicted_return_pct: float, confidence: float,
                       model_type: str = 'ensemble',
                       actual_price: Optional[float] = None,
                       actual_return_pct: Optional[float] = None):
        """
        Save a prediction to the database.
        
        Args:
            symbol: Stock ticker
            prediction_date: Date of prediction (YYYY-MM-DD)
            current_price: Current stock price
            predicted_price: Predicted future price
            predicted_return_pct: Predicted return percentage
            confidence: Confidence score
            model_type: Type of model used
            actual_price: Actual price (if known)
            actual_return_pct: Actual return (if known)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate errors if actual is provided
        price_error_pct = None
        direction_correct = None
        
        if actual_price:
            price_error_pct = abs((predicted_price - actual_price) / actual_price) * 100
            if actual_return_pct is not None and predicted_return_pct is not None:
                direction_correct = 1 if np.sign(actual_return_pct) == np.sign(predicted_return_pct) else 0
        
        cursor.execute('''
            INSERT OR REPLACE INTO predictions 
            (symbol, prediction_date, current_price, predicted_price, predicted_return_pct,
             actual_price, actual_return_pct, price_error_pct, direction_correct,
             confidence, model_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, prediction_date, current_price, predicted_price, predicted_return_pct,
              actual_price, actual_return_pct, price_error_pct, direction_correct,
              confidence, model_type))
        
        conn.commit()
        conn.close()
    
    def update_actual_result(self, symbol: str, prediction_date: str,
                            actual_price: float, actual_return_pct: float):
        """
        Update a prediction with actual results.
        
        Args:
            symbol: Stock ticker
            prediction_date: Date of prediction
            actual_price: Actual price
            actual_return_pct: Actual return percentage
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the prediction
        cursor.execute('''
            SELECT predicted_price, predicted_return_pct FROM predictions
            WHERE symbol = ? AND prediction_date = ?
        ''', (symbol, prediction_date))
        
        result = cursor.fetchone()
        if result:
            predicted_price, predicted_return_pct = result
            price_error_pct = abs((predicted_price - actual_price) / actual_price) * 100
            direction_correct = 1 if np.sign(actual_return_pct) == np.sign(predicted_return_pct) else 0
            
            cursor.execute('''
                UPDATE predictions
                SET actual_price = ?, actual_return_pct = ?, price_error_pct = ?,
                    direction_correct = ?
                WHERE symbol = ? AND prediction_date = ?
            ''', (actual_price, actual_return_pct, price_error_pct, direction_correct,
                  symbol, prediction_date))
        
        conn.commit()
        conn.close()
    
    def get_performance_stats(self, symbol: Optional[str] = None,
                             days: int = 30) -> Dict:
        """
        Get performance statistics.
        
        Args:
            symbol: Stock ticker (None for all stocks)
            days: Number of recent days to analyze
            
        Returns:
            Dictionary with performance statistics
        """
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                AVG(price_error_pct) as avg_error,
                AVG(CASE WHEN direction_correct = 1 THEN 1.0 ELSE 0.0 END) * 100 as direction_accuracy,
                COUNT(*) as total_predictions
            FROM predictions
            WHERE actual_price IS NOT NULL
        '''
        
        params = []
        if symbol:
            query += ' AND symbol = ?'
            params.append(symbol)
        
        query += ' AND prediction_date >= date("now", "-{} days")'.format(days)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if len(df) > 0:
            return {
                'avg_error_pct': float(df['avg_error'].iloc[0]) if df['avg_error'].iloc[0] else 0.0,
                'direction_accuracy': float(df['direction_accuracy'].iloc[0]) if df['direction_accuracy'].iloc[0] else 0.0,
                'total_predictions': int(df['total_predictions'].iloc[0])
            }
        else:
            return {
                'avg_error_pct': 0.0,
                'direction_accuracy': 0.0,
                'total_predictions': 0
            }
    
    def save_performance_metrics(self, symbol: str, metrics: Dict, model_type: str = 'ensemble'):
        """Save performance metrics from a backtest."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO performance_metrics
            (symbol, test_date, avg_price_error_pct, avg_return_error,
             direction_accuracy, test_days, model_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, datetime.now().strftime('%Y-%m-%d'),
              metrics.get('avg_price_error_pct', 0),
              metrics.get('avg_return_error', 0),
              metrics.get('direction_accuracy', 0),
              metrics.get('test_days', 0),
              model_type))
        
        conn.commit()
        conn.close()


# Import numpy for the update function
import numpy as np

