"""
Stock Price Prediction Model Module

Uses machine learning and statistical models to predict future stock prices
based on historical price data, technical indicators, and external signals.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from typing import Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class StockPricePredictor:
    """
    Predicts future stock prices using machine learning models.
    
    Uses ensemble methods (Random Forest and Gradient Boosting) to predict
    stock prices based on:
    - Historical price patterns
    - Technical indicators
    - External sentiment signals (news, social media)
    """
    
    def __init__(self, model_type: str = 'ensemble'):
        """
        Initialize the price predictor.
        
        Args:
            model_type: Type of model to use ('rf' for Random Forest, 
                       'gb' for Gradient Boosting, 'ensemble' for both)
        """
        self.model_type = model_type
        self.rf_model = None
        self.gb_model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.is_trained = False
        
    def prepare_features(self, price_data: pd.DataFrame, 
                        news_sentiment: Optional[Dict] = None,
                        social_sentiment: Optional[Dict] = None,
                        fundamental_data: Optional[Dict] = None) -> pd.DataFrame:
        """
        Prepare features for the prediction model.
        
        Combines price data, technical indicators, and sentiment signals
        into a feature matrix suitable for machine learning.
        
        Args:
            price_data: DataFrame with historical prices and technical indicators
            news_sentiment: Dictionary with news sentiment metrics
            social_sentiment: Dictionary with social media sentiment metrics
            
        Returns:
            DataFrame with features ready for model training/prediction
        """
        features = price_data.copy()
        
        # Add sentiment features if available
        # For training: use recent sentiment (applies to recent rows)
        # For prediction: use current sentiment
        if news_sentiment:
            avg_sentiment = news_sentiment.get('average_sentiment', 0.0)
            pos_ratio = news_sentiment.get('positive_ratio', 0.0)
            neg_ratio = news_sentiment.get('negative_ratio', 0.0)
            article_count = news_sentiment.get('article_count', 0)
            
            # Apply sentiment to all rows (for training, this represents recent sentiment)
            # In a more sophisticated version, we could align sentiment by date
            features['news_sentiment'] = avg_sentiment
            features['news_positive_ratio'] = pos_ratio
            features['news_negative_ratio'] = neg_ratio
            features['news_article_count'] = min(article_count / 10.0, 1.0)  # Normalize article count
        else:
            features['news_sentiment'] = 0.0
            features['news_positive_ratio'] = 0.0
            features['news_negative_ratio'] = 0.0
            features['news_article_count'] = 0.0
        
        if social_sentiment:
            features['social_sentiment'] = social_sentiment.get('average_sentiment', 0.0)
            features['social_positive_ratio'] = social_sentiment.get('positive_ratio', 0.0)
            features['reddit_sentiment'] = social_sentiment.get('reddit_sentiment', 0.0)
            features['twitter_sentiment'] = social_sentiment.get('twitter_sentiment', 0.0)
        else:
            features['social_sentiment'] = 0.0
            features['social_positive_ratio'] = 0.0
            features['reddit_sentiment'] = 0.0
            features['twitter_sentiment'] = 0.0
        
        # Add fundamental analysis features if available
        # These are static values that apply to all rows (current fundamentals)
        if fundamental_data:
            # Valuation ratios
            features['pe_ratio'] = fundamental_data.get('pe_ratio', 0.0)
            features['peg_ratio'] = fundamental_data.get('peg_ratio', 0.0)
            features['price_to_book'] = fundamental_data.get('price_to_book', 0.0)
            features['price_to_sales'] = fundamental_data.get('price_to_sales', 0.0)
            
            # Dividend metrics
            features['dividend_yield'] = fundamental_data.get('dividend_yield', 0.0)
            features['payout_ratio'] = fundamental_data.get('payout_ratio', 0.0)
            
            # Financial health
            features['debt_to_equity'] = fundamental_data.get('debt_to_equity', 0.0)
            features['current_ratio'] = fundamental_data.get('current_ratio', 0.0)
            features['profit_margins'] = fundamental_data.get('profit_margins', 0.0)
            
            # Growth metrics
            features['revenue_growth'] = fundamental_data.get('revenue_growth', 0.0)
            features['earnings_growth'] = fundamental_data.get('earnings_growth', 0.0)
            
            # Price position relative to 52-week range
            current_price = price_data['Close'].iloc[-1] if len(price_data) > 0 else 0
            week_52_high = fundamental_data.get('52_week_high', current_price)
            week_52_low = fundamental_data.get('52_week_low', current_price)
            if week_52_high > week_52_low:
                features['price_vs_52w_high'] = (current_price - week_52_high) / week_52_high
                features['price_vs_52w_low'] = (current_price - week_52_low) / week_52_low
                features['price_in_52w_range'] = (current_price - week_52_low) / (week_52_high - week_52_low)
            else:
                features['price_vs_52w_high'] = 0.0
                features['price_vs_52w_low'] = 0.0
                features['price_in_52w_range'] = 0.5
            
            # Price vs moving averages
            day_50_avg = fundamental_data.get('50_day_avg', current_price)
            day_200_avg = fundamental_data.get('200_day_avg', current_price)
            if day_50_avg > 0:
                features['price_vs_50ma'] = (current_price - day_50_avg) / day_50_avg
            else:
                features['price_vs_50ma'] = 0.0
            if day_200_avg > 0:
                features['price_vs_200ma'] = (current_price - day_200_avg) / day_200_avg
            else:
                features['price_vs_200ma'] = 0.0
        else:
            # Set all fundamental features to 0 if not available
            fundamental_features = [
                'pe_ratio', 'peg_ratio', 'price_to_book', 'price_to_sales',
                'dividend_yield', 'payout_ratio', 'debt_to_equity', 'current_ratio',
                'profit_margins', 'revenue_growth', 'earnings_growth',
                'price_vs_52w_high', 'price_vs_52w_low', 'price_in_52w_range',
                'price_vs_50ma', 'price_vs_200ma'
            ]
            for feat in fundamental_features:
                features[feat] = 0.0
        
        # Select feature columns (exclude non-numeric and target columns)
        exclude_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 
                       'Dividends', 'Stock Splits']
        
        # Get all numeric columns that aren't in exclude list
        feature_cols = [col for col in features.columns 
                       if col not in exclude_cols and features[col].dtype in ['float64', 'int64']]
        
        # Create feature matrix
        feature_df = features[feature_cols].copy()
        
        # Fill any remaining NaN values
        feature_df = feature_df.bfill().fillna(0)
        
        # Store feature columns for later use
        self.feature_columns = feature_cols
        
        return feature_df
    
    def create_target(self, price_data: pd.DataFrame, days_ahead: int = 1) -> pd.Series:
        """
        Create target variable (future price) for prediction.
        
        Args:
            price_data: DataFrame with historical prices
            days_ahead: Number of days ahead to predict (default: 1 day)
            
        Returns:
            Series with future prices (shifted back to align with features)
        """
        # Shift close price forward by days_ahead to create target
        # This means for each row, we're predicting the price 'days_ahead' days in the future
        target = price_data['Close'].shift(-days_ahead)
        return target
    
    def train(self, price_data: pd.DataFrame,
              news_sentiment: Optional[Dict] = None,
              social_sentiment: Optional[Dict] = None,
              fundamental_data: Optional[Dict] = None,
              days_ahead: int = 1,
              test_size: float = 0.2) -> Dict[str, float]:
        """
        Train the prediction model.
        
        Args:
            price_data: DataFrame with historical prices and technical indicators
            news_sentiment: Dictionary with news sentiment metrics
            social_sentiment: Dictionary with social media sentiment metrics
            days_ahead: Number of days ahead to predict
            test_size: Proportion of data to use for testing
            
        Returns:
            Dictionary with model performance metrics
        """
        # Prepare features and target
        features = self.prepare_features(price_data, news_sentiment, social_sentiment, fundamental_data)
        target = self.create_target(price_data, days_ahead)
        
        # Remove rows where target is NaN (last 'days_ahead' rows)
        valid_mask = ~target.isna()
        X = features[valid_mask].values
        y = target[valid_mask].values
        
        if len(X) == 0:
            raise ValueError("No valid data for training")
        
        # Split into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False  # Don't shuffle time series data
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train models
        metrics = {}
        
        if self.model_type in ['rf', 'ensemble']:
            # Random Forest: Good for capturing non-linear relationships
            self.rf_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
            self.rf_model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred_rf = self.rf_model.predict(X_test_scaled)
            metrics['rf_mae'] = mean_absolute_error(y_test, y_pred_rf)
            metrics['rf_rmse'] = np.sqrt(mean_squared_error(y_test, y_pred_rf))
            metrics['rf_r2'] = r2_score(y_test, y_pred_rf)
        
        if self.model_type in ['gb', 'ensemble']:
            # Gradient Boosting: Good for sequential learning and handling complex patterns
            self.gb_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
            self.gb_model.fit(X_train_scaled, y_train)
            
            # Evaluate
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
        Predict future stock price.
        
        Args:
            price_data: DataFrame with historical prices and technical indicators
            news_sentiment: Dictionary with news sentiment metrics
            social_sentiment: Dictionary with social media sentiment metrics
            days_ahead: Number of days ahead to predict
            
        Returns:
            Dictionary with predictions and confidence intervals
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare features from the most recent data
        features = self.prepare_features(price_data, news_sentiment, social_sentiment, fundamental_data)
        
        # Get the most recent row (last valid row)
        latest_features = features.iloc[-1:].values
        
        # Scale features
        latest_features_scaled = self.scaler.transform(latest_features)
        
        predictions = {}
        
        # Make predictions with both models if available
        if self.rf_model:
            pred_rf = self.rf_model.predict(latest_features_scaled)[0]
            predictions['rf_prediction'] = float(pred_rf)
            
            # Get prediction intervals from tree-based model
            # Use individual tree predictions to estimate uncertainty
            tree_preds = [tree.predict(latest_features_scaled)[0] 
                         for tree in self.rf_model.estimators_]
            predictions['rf_std'] = float(np.std(tree_preds))
            predictions['rf_lower'] = float(pred_rf - 1.96 * predictions['rf_std'])
            predictions['rf_upper'] = float(pred_rf + 1.96 * predictions['rf_std'])
        
        if self.gb_model:
            pred_gb = self.gb_model.predict(latest_features_scaled)[0]
            predictions['gb_prediction'] = float(pred_gb)
        
        # Ensemble prediction (average if both models available)
        if self.rf_model and self.gb_model:
            ensemble_pred = (predictions['rf_prediction'] + predictions['gb_prediction']) / 2
            predictions['ensemble_prediction'] = float(ensemble_pred)
            predictions['prediction'] = float(ensemble_pred)  # Default prediction
        elif self.rf_model:
            predictions['prediction'] = predictions['rf_prediction']
        elif self.gb_model:
            predictions['prediction'] = predictions['gb_prediction']
        else:
            raise ValueError("No trained model available")
        
        return predictions
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance from trained models.
        
        Returns:
            DataFrame with feature importance scores
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before getting feature importance")
        
        importance_data = []
        
        if self.rf_model and self.feature_columns:
            rf_importance = self.rf_model.feature_importances_
            for feature, importance in zip(self.feature_columns, rf_importance):
                importance_data.append({
                    'feature': feature,
                    'rf_importance': importance
                })
        
        if self.gb_model and self.feature_columns:
            gb_importance = self.gb_model.feature_importances_
            for i, (feature, importance) in enumerate(zip(self.feature_columns, gb_importance)):
                if i < len(importance_data):
                    importance_data[i]['gb_importance'] = importance
                else:
                    importance_data.append({
                        'feature': feature,
                        'gb_importance': importance
                    })
        
        df = pd.DataFrame(importance_data)
        
        # Calculate average importance if both models available
        if 'rf_importance' in df.columns and 'gb_importance' in df.columns:
            df['avg_importance'] = (df['rf_importance'] + df['gb_importance']) / 2
            df = df.sort_values('avg_importance', ascending=False)
        elif 'rf_importance' in df.columns:
            df = df.sort_values('rf_importance', ascending=False)
        elif 'gb_importance' in df.columns:
            df = df.sort_values('gb_importance', ascending=False)
        
        return df

