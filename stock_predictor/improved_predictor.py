"""
Improved Stock Price Predictor

Enhanced version with better feature engineering, percentage returns,
and optimized models for improved accuracy.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.feature_selection import SelectKBest, f_regression
from typing import Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class ImprovedStockPredictor:
    """
    Improved predictor using percentage returns and better feature engineering.
    
    Key improvements:
    - Predicts percentage returns instead of absolute prices
    - Enhanced feature engineering (lagged features, rolling stats)
    - Feature selection
    - Better hyperparameter tuning
    - Robust scaling for outliers
    """
    
    def __init__(self, model_type: str = 'ensemble', use_feature_selection: bool = True):
        """
        Initialize the improved predictor.
        
        Args:
            model_type: 'rf', 'gb', or 'ensemble'
            use_feature_selection: Whether to use feature selection
        """
        self.model_type = model_type
        self.use_feature_selection = use_feature_selection
        self.rf_model = None
        self.gb_model = None
        self.scaler = RobustScaler()  # More robust to outliers than StandardScaler
        self.feature_selector = None
        self.feature_columns = None
        self.selected_features = None
        self.is_trained = False
        
    def create_enhanced_features(self, price_data: pd.DataFrame,
                                news_sentiment: Optional[Dict] = None,
                                social_sentiment: Optional[Dict] = None,
                                fundamental_data: Optional[Dict] = None) -> pd.DataFrame:
        """
        Create enhanced features with lagged values and rolling statistics.
        
        Args:
            price_data: DataFrame with prices and technical indicators
            news_sentiment: News sentiment metrics
            social_sentiment: Social media sentiment metrics
            fundamental_data: Fundamental analysis metrics
            
        Returns:
            DataFrame with enhanced features
        """
        features = price_data.copy()
        
        # Calculate percentage returns (more stable than absolute prices)
        if 'Close' in features.columns:
            features['pct_return_1d'] = features['Close'].pct_change(1)
            features['pct_return_5d'] = features['Close'].pct_change(5)
            features['pct_return_10d'] = features['Close'].pct_change(10)
            
            # Lagged returns (yesterday's return, 5 days ago, etc.)
            features['lag_return_1'] = features['pct_return_1d'].shift(1)
            features['lag_return_2'] = features['pct_return_1d'].shift(2)
            features['lag_return_5'] = features['pct_return_1d'].shift(5)
            
            # Rolling statistics
            features['rolling_mean_5'] = features['Close'].rolling(5).mean()
            features['rolling_mean_10'] = features['Close'].rolling(10).mean()
            features['rolling_std_5'] = features['Close'].rolling(5).std()
            features['rolling_std_10'] = features['Close'].rolling(10).std()
            
            # Price position in rolling window
            if 'rolling_mean_5' in features.columns and 'rolling_std_5' in features.columns:
                features['price_zscore_5'] = (features['Close'] - features['rolling_mean_5']) / (features['rolling_std_5'] + 1e-8)
        
        # Enhanced technical indicators
        if 'RSI' in features.columns:
            # RSI momentum
            features['RSI_change'] = features['RSI'].diff()
            features['RSI_oversold'] = (features['RSI'] < 30).astype(int)
            features['RSI_overbought'] = (features['RSI'] > 70).astype(int)
        
        if 'MACD' in features.columns and 'MACD_signal' in features.columns:
            # MACD momentum
            features['MACD_momentum'] = features['MACD'].diff()
            features['MACD_cross'] = ((features['MACD'] > features['MACD_signal']) & 
                                     (features['MACD'].shift(1) <= features['MACD_signal'].shift(1))).astype(int)
        
        # Volume features
        if 'Volume' in features.columns:
            features['volume_change'] = features['Volume'].pct_change()
            features['volume_zscore'] = (features['Volume'] - features['Volume'].rolling(20).mean()) / (features['Volume'].rolling(20).std() + 1e-8)
        
        # Add sentiment features
        if news_sentiment:
            features['news_sentiment'] = news_sentiment.get('average_sentiment', 0.0)
            features['news_positive_ratio'] = news_sentiment.get('positive_ratio', 0.0)
            features['news_negative_ratio'] = news_sentiment.get('negative_ratio', 0.0)
            features['news_article_count'] = min(news_sentiment.get('article_count', 0) / 10.0, 1.0)
        else:
            features['news_sentiment'] = 0.0
            features['news_positive_ratio'] = 0.0
            features['news_negative_ratio'] = 0.0
            features['news_article_count'] = 0.0
        
        if social_sentiment:
            features['social_sentiment'] = social_sentiment.get('average_sentiment', 0.0)
            features['social_positive_ratio'] = social_sentiment.get('positive_ratio', 0.0)
        else:
            features['social_sentiment'] = 0.0
            features['social_positive_ratio'] = 0.0
        
        # Add fundamental features
        if fundamental_data:
            features['pe_ratio'] = fundamental_data.get('pe_ratio', 0.0)
            features['dividend_yield'] = fundamental_data.get('dividend_yield', 0.0)
            features['price_to_book'] = fundamental_data.get('price_to_book', 0.0)
            
            current_price = features['Close'].iloc[-1] if len(features) > 0 else 0
            week_52_high = fundamental_data.get('52_week_high', current_price)
            week_52_low = fundamental_data.get('52_week_low', current_price)
            if week_52_high > week_52_low:
                features['price_in_52w_range'] = (current_price - week_52_low) / (week_52_high - week_52_low)
            else:
                features['price_in_52w_range'] = 0.5
        else:
            features['pe_ratio'] = 0.0
            features['dividend_yield'] = 0.0
            features['price_to_book'] = 0.0
            features['price_in_52w_range'] = 0.5
        
        # Select numeric feature columns
        exclude_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 
                       'Dividends', 'Stock Splits']
        
        feature_cols = [col for col in features.columns 
                       if col not in exclude_cols and features[col].dtype in ['float64', 'int64']]
        
        feature_df = features[feature_cols].copy()
        
        # Fill NaN values
        feature_df = feature_df.bfill().fillna(0)
        
        # Replace infinite values
        feature_df = feature_df.replace([np.inf, -np.inf], 0)
        
        self.feature_columns = feature_cols
        
        return feature_df
    
    def create_target(self, price_data: pd.DataFrame, days_ahead: int = 1) -> pd.Series:
        """
        Create target as percentage return (better than absolute price).
        
        Args:
            price_data: DataFrame with prices
            days_ahead: Days ahead to predict
            
        Returns:
            Series with percentage returns
        """
        # Calculate future return instead of future price
        current_price = price_data['Close']
        future_price = price_data['Close'].shift(-days_ahead)
        
        # Percentage return
        target = ((future_price - current_price) / current_price) * 100
        
        return target
    
    def train(self, price_data: pd.DataFrame,
              news_sentiment: Optional[Dict] = None,
              social_sentiment: Optional[Dict] = None,
              fundamental_data: Optional[Dict] = None,
              days_ahead: int = 1,
              test_size: float = 0.2) -> Dict[str, float]:
        """
        Train the improved model.
        
        Args:
            price_data: Historical price data
            news_sentiment: News sentiment metrics
            social_sentiment: Social media sentiment metrics
            fundamental_data: Fundamental analysis metrics
            days_ahead: Prediction horizon
            test_size: Test set proportion
            
        Returns:
            Performance metrics
        """
        # Create enhanced features
        features = self.create_enhanced_features(price_data, news_sentiment, social_sentiment, fundamental_data)
        target = self.create_target(price_data, days_ahead)
        
        # Remove NaN rows
        valid_mask = ~target.isna()
        X = features[valid_mask].values
        y = target[valid_mask].values
        
        if len(X) == 0:
            raise ValueError("No valid data for training")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False
        )
        
        # Feature selection
        if self.use_feature_selection and len(self.feature_columns) > 20:
            self.feature_selector = SelectKBest(f_regression, k=min(30, len(self.feature_columns)))
            X_train_selected = self.feature_selector.fit_transform(X_train, y_train)
            X_test_selected = self.feature_selector.transform(X_test)
            self.selected_features = self.feature_selector.get_support()
        else:
            X_train_selected = X_train
            X_test_selected = X_test
            self.selected_features = np.ones(X_train.shape[1], dtype=bool)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train_selected)
        X_test_scaled = self.scaler.transform(X_test_selected)
        
        metrics = {}
        
        # Train Random Forest with better hyperparameters
        if self.model_type in ['rf', 'ensemble']:
            self.rf_model = RandomForestRegressor(
                n_estimators=150,  # Balanced number of trees
                max_depth=12,  # Moderate depth to avoid overfitting
                min_samples_split=8,
                min_samples_leaf=4,
                max_features='sqrt',  # Better generalization
                random_state=42,
                n_jobs=-1
            )
            self.rf_model.fit(X_train_scaled, y_train)
            
            y_pred_rf = self.rf_model.predict(X_test_scaled)
            metrics['rf_mae'] = mean_absolute_error(y_test, y_pred_rf)
            metrics['rf_rmse'] = np.sqrt(mean_squared_error(y_test, y_pred_rf))
            metrics['rf_r2'] = r2_score(y_test, y_pred_rf)
        
        # Train Gradient Boosting with better hyperparameters
        if self.model_type in ['gb', 'ensemble']:
            self.gb_model = GradientBoostingRegressor(
                n_estimators=150,
                max_depth=5,
                learning_rate=0.08,  # Slightly higher for more signal
                subsample=0.85,  # Stochastic gradient boosting
                min_samples_split=8,
                min_samples_leaf=4,
                random_state=42
            )
            self.gb_model.fit(X_train_scaled, y_train)
            
            y_pred_gb = self.gb_model.predict(X_test_scaled)
            metrics['gb_mae'] = mean_absolute_error(y_test, y_pred_gb)
            metrics['gb_rmse'] = np.sqrt(mean_squared_error(y_test, y_pred_gb))
            metrics['gb_r2'] = r2_score(y_test, y_pred_gb)
        
        self.is_trained = True
        
        return metrics
    
    def predict(self, price_data: pd.DataFrame,
                news_sentiment: Optional[Dict] = None,
                social_sentiment: Optional[Dict] = None,
                fundamental_data: Optional[Dict] = None,
                days_ahead: int = 1) -> Dict[str, float]:
        """
        Predict future percentage return.
        
        Args:
            price_data: Historical price data
            news_sentiment: News sentiment metrics
            social_sentiment: Social media sentiment metrics
            fundamental_data: Fundamental analysis metrics
            days_ahead: Prediction horizon
            
        Returns:
            Dictionary with predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Create features
        features = self.create_enhanced_features(price_data, news_sentiment, social_sentiment, fundamental_data)
        latest_features = features.iloc[-1:].values
        
        # Apply feature selection if used
        if self.feature_selector:
            latest_features = self.feature_selector.transform(latest_features)
        
        # Scale
        latest_features_scaled = self.scaler.transform(latest_features)
        
        current_price = float(price_data['Close'].iloc[-1])
        predictions = {}
        
        # Make predictions
        if self.rf_model:
            pred_return_rf = self.rf_model.predict(latest_features_scaled)[0]
            predictions['rf_return_pct'] = float(pred_return_rf)
            predictions['rf_prediction'] = current_price * (1 + pred_return_rf / 100)
            
            # Get prediction intervals
            tree_preds = [tree.predict(latest_features_scaled)[0] 
                         for tree in self.rf_model.estimators_]
            predictions['rf_std'] = float(np.std(tree_preds))
            predictions['rf_lower'] = current_price * (1 + (pred_return_rf - 1.96 * predictions['rf_std']) / 100)
            predictions['rf_upper'] = current_price * (1 + (pred_return_rf + 1.96 * predictions['rf_std']) / 100)
        
        if self.gb_model:
            pred_return_gb = self.gb_model.predict(latest_features_scaled)[0]
            predictions['gb_return_pct'] = float(pred_return_gb)
            predictions['gb_prediction'] = current_price * (1 + pred_return_gb / 100)
        
        # Ensemble prediction
        if self.rf_model and self.gb_model:
            ensemble_return = (predictions['rf_return_pct'] + predictions['gb_return_pct']) / 2
            predictions['ensemble_return_pct'] = float(ensemble_return)
            predictions['ensemble_prediction'] = current_price * (1 + ensemble_return / 100)
            predictions['prediction'] = predictions['ensemble_prediction']
            predictions['return_pct'] = ensemble_return
        elif self.rf_model:
            predictions['prediction'] = predictions['rf_prediction']
            predictions['return_pct'] = predictions['rf_return_pct']
        elif self.gb_model:
            predictions['prediction'] = predictions['gb_prediction']
            predictions['return_pct'] = predictions['gb_return_pct']
        else:
            raise ValueError("No trained model available")
        
        return predictions

