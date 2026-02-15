"""
Feature Engineering pipeline for price forecasting.

This module provides feature extraction and transformation utilities
for training ML models to forecast agricultural commodity prices.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler


@dataclass
class FeatureConfig:
    """Configuration for feature engineering."""
    # Temporal features
    include_day_of_week: bool = True
    include_day_of_month: bool = True
    include_day_of_year: bool = True
    include_week_of_year: bool = True
    include_month: bool = True
    include_quarter: bool = True
    include_year: bool = True
    include_is_weekend: bool = True
    include_is_month_start: bool = True
    include_is_month_end: bool = True
    
    # Lag features
    lag_days: List[int] = None  # type: ignore
    rolling_windows: List[int] = None  # type: ignore
    
    # Price features
    include_price_change: bool = True
    include_price_volatility: bool = True
    include_price_momentum: bool = True
    
    # Weather features
    include_weather: bool = True
    
    # Scaling
    scale_features: bool = True
    scaler_type: str = "standard"  # "standard" or "minmax"
    
    def __post_init__(self):
        if self.lag_days is None:
            self.lag_days = [1, 3, 7, 14, 30]
        if self.rolling_windows is None:
            self.rolling_windows = [7, 14, 30]


class FeatureEngineer:
    """
    Feature engineering for agricultural price forecasting.
    
    Creates temporal, lag, rolling, and external features from
    historical price data for ML model training and inference.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """Initialize feature engineer with configuration."""
        self.config = config or FeatureConfig()
        self.scalers: Dict[str, StandardScaler | MinMaxScaler] = {}
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self._fitted = False
    
    def create_temporal_features(
        self,
        df: pd.DataFrame,
        date_column: str = "price_date",
    ) -> pd.DataFrame:
        """
        Create temporal features from date column.
        
        Args:
            df: DataFrame with date column
            date_column: Name of the date column
            
        Returns:
            DataFrame with temporal features added
        """
        df = df.copy()
        
        # Ensure date column is datetime
        df[date_column] = pd.to_datetime(df[date_column])
        
        if self.config.include_day_of_week:
            df["day_of_week"] = df[date_column].dt.dayofweek
        
        if self.config.include_day_of_month:
            df["day_of_month"] = df[date_column].dt.day
        
        if self.config.include_day_of_year:
            df["day_of_year"] = df[date_column].dt.dayofyear
        
        if self.config.include_week_of_year:
            df["week_of_year"] = df[date_column].dt.isocalendar().week
        
        if self.config.include_month:
            df["month"] = df[date_column].dt.month
        
        if self.config.include_quarter:
            df["quarter"] = df[date_column].dt.quarter
        
        if self.config.include_year:
            df["year"] = df[date_column].dt.year
        
        if self.config.include_is_weekend:
            df["is_weekend"] = (df[date_column].dt.dayofweek >= 5).astype(int)
        
        if self.config.include_is_month_start:
            df["is_month_start"] = df[date_column].dt.is_month_start.astype(int)
        
        if self.config.include_is_month_end:
            df["is_month_end"] = df[date_column].dt.is_month_end.astype(int)
        
        # Cyclical encoding for periodic features
        if self.config.include_month:
            df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
            df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
        
        if self.config.include_day_of_week:
            df["day_of_week_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
            df["day_of_week_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
        
        return df
    
    def create_lag_features(
        self,
        df: pd.DataFrame,
        value_column: str = "modal_price",
        group_columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Create lag features for time series.
        
        Args:
            df: DataFrame sorted by date
            value_column: Column to create lags for
            group_columns: Columns to group by before creating lags
            
        Returns:
            DataFrame with lag features added
        """
        df = df.copy()
        
        if group_columns is None:
            group_columns = ["commodity_id", "mandi_id"]
        
        for lag in self.config.lag_days:
            lag_col = f"{value_column}_lag_{lag}"
            df[lag_col] = df.groupby(group_columns)[value_column].shift(lag)
        
        return df
    
    def create_rolling_features(
        self,
        df: pd.DataFrame,
        value_column: str = "modal_price",
        group_columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Create rolling window features.
        
        Args:
            df: DataFrame sorted by date
            value_column: Column to create rolling features for
            group_columns: Columns to group by
            
        Returns:
            DataFrame with rolling features added
        """
        df = df.copy()
        
        if group_columns is None:
            group_columns = ["commodity_id", "mandi_id"]
        
        for window in self.config.rolling_windows:
            # Rolling mean
            df[f"{value_column}_rolling_mean_{window}"] = (
                df.groupby(group_columns)[value_column]
                .transform(lambda x: x.rolling(window=window, min_periods=1).mean())
            )
            
            # Rolling std (volatility)
            if self.config.include_price_volatility:
                df[f"{value_column}_rolling_std_{window}"] = (
                    df.groupby(group_columns)[value_column]
                    .transform(lambda x: x.rolling(window=window, min_periods=1).std())
                )
            
            # Rolling min/max
            df[f"{value_column}_rolling_min_{window}"] = (
                df.groupby(group_columns)[value_column]
                .transform(lambda x: x.rolling(window=window, min_periods=1).min())
            )
            
            df[f"{value_column}_rolling_max_{window}"] = (
                df.groupby(group_columns)[value_column]
                .transform(lambda x: x.rolling(window=window, min_periods=1).max())
            )
        
        return df
    
    def create_price_features(
        self,
        df: pd.DataFrame,
        group_columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Create price-derived features.
        
        Args:
            df: DataFrame with price columns
            group_columns: Columns to group by
            
        Returns:
            DataFrame with price features added
        """
        df = df.copy()
        
        if group_columns is None:
            group_columns = ["commodity_id", "mandi_id"]
        
        # Price change (absolute and percentage)
        if self.config.include_price_change:
            df["price_change_1d"] = df.groupby(group_columns)["modal_price"].diff()
            df["price_change_pct_1d"] = df.groupby(group_columns)["modal_price"].pct_change()
            
            # Multi-day changes
            for days in [3, 7, 14]:
                df[f"price_change_pct_{days}d"] = (
                    df.groupby(group_columns)["modal_price"]
                    .pct_change(periods=days)
                )
        
        # Price momentum (rate of change)
        if self.config.include_price_momentum:
            # Momentum = current price / price N days ago - 1
            for days in [7, 14, 30]:
                df[f"price_momentum_{days}d"] = (
                    df.groupby(group_columns)["modal_price"]
                    .transform(lambda x: x / x.shift(days) - 1)
                )
        
        # Price range (max - min) as percentage of modal
        if "max_price" in df.columns and "min_price" in df.columns:
            df["price_range_pct"] = (df["max_price"] - df["min_price"]) / df["modal_price"]
        
        # Price position within range
        if all(col in df.columns for col in ["max_price", "min_price", "modal_price"]):
            price_range = df["max_price"] - df["min_price"]
            df["price_position"] = np.where(
                price_range > 0,
                (df["modal_price"] - df["min_price"]) / price_range,
                0.5
            )
        
        return df
    
    def create_weather_features(
        self,
        df: pd.DataFrame,
        weather_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Create weather-based features.
        
        Args:
            df: Price DataFrame
            weather_df: Weather data DataFrame
            
        Returns:
            DataFrame with weather features added
        """
        if not self.config.include_weather or weather_df is None:
            return df
        
        df = df.copy()
        
        # Merge weather data
        weather_cols = ["temperature_avg", "rainfall", "humidity"]
        available_cols = [c for c in weather_cols if c in weather_df.columns]
        
        if available_cols:
            df = df.merge(
                weather_df[["mandi_id", "weather_date"] + available_cols],
                left_on=["mandi_id", "price_date"],
                right_on=["mandi_id", "weather_date"],
                how="left",
            )
            
            # Create weather-derived features
            if "rainfall" in df.columns:
                # Rainy day flag
                df["is_rainy"] = (df["rainfall"] > 0).astype(int)
                
                # Cumulative rainfall (7-day)
                df["rainfall_7d_cumsum"] = df.groupby("mandi_id")["rainfall"].transform(
                    lambda x: x.rolling(window=7, min_periods=1).sum()
                )
        
        return df
    
    def create_target(
        self,
        df: pd.DataFrame,
        horizon_days: int = 7,
        target_column: str = "modal_price",
        group_columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Create target variable for forecasting.
        
        Args:
            df: DataFrame with price data
            horizon_days: Number of days to forecast ahead
            target_column: Column to forecast
            group_columns: Columns to group by
            
        Returns:
            DataFrame with target column added
        """
        df = df.copy()
        
        if group_columns is None:
            group_columns = ["commodity_id", "mandi_id"]
        
        # Future price (shift negative for forward-looking)
        df[f"target_{horizon_days}d"] = df.groupby(group_columns)[target_column].shift(-horizon_days)
        
        # Future price change percentage
        df[f"target_change_{horizon_days}d"] = (
            df[f"target_{horizon_days}d"] - df[target_column]
        ) / df[target_column]
        
        return df
    
    def fit(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
    ) -> "FeatureEngineer":
        """
        Fit scalers and encoders on training data.
        
        Args:
            df: Training DataFrame
            feature_columns: List of feature column names
            
        Returns:
            Self for method chaining
        """
        # Fit scaler
        if self.config.scale_features:
            if self.config.scaler_type == "standard":
                scaler = StandardScaler()
            else:
                scaler = MinMaxScaler()
            
            # Handle NaN values for fitting
            valid_data = df[feature_columns].dropna()
            scaler.fit(valid_data)
            self.scalers["features"] = scaler
        
        self._fitted = True
        return self
    
    def transform(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
    ) -> np.ndarray:
        """
        Transform features using fitted scalers.
        
        Args:
            df: DataFrame to transform
            feature_columns: List of feature column names
            
        Returns:
            Numpy array of scaled features
        """
        if not self._fitted:
            raise ValueError("FeatureEngineer must be fitted before transform")
        
        X = df[feature_columns].values
        
        if self.config.scale_features and "features" in self.scalers:
            # Handle NaN values
            X = np.nan_to_num(X, nan=0.0)
            X = self.scalers["features"].transform(X)
        
        return X
    
    def fit_transform(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
    ) -> np.ndarray:
        """
        Fit and transform in one step.
        
        Args:
            df: Training DataFrame
            feature_columns: List of feature column names
            
        Returns:
            Numpy array of scaled features
        """
        self.fit(df, feature_columns)
        return self.transform(df, feature_columns)
    
    def prepare_features(
        self,
        df: pd.DataFrame,
        weather_df: Optional[pd.DataFrame] = None,
        horizon_days: int = 7,
        is_training: bool = True,
    ) -> Tuple[pd.DataFrame, List[str], Optional[str]]:
        """
        Full feature preparation pipeline.
        
        Args:
            df: Raw price DataFrame
            weather_df: Optional weather DataFrame
            horizon_days: Forecast horizon in days
            is_training: Whether preparing training data
            
        Returns:
            Tuple of (processed_df, feature_columns, target_column)
        """
        # Sort by date
        df = df.sort_values(["commodity_id", "mandi_id", "price_date"]).reset_index(drop=True)
        
        # Create all features
        df = self.create_temporal_features(df)
        df = self.create_lag_features(df)
        df = self.create_rolling_features(df)
        df = self.create_price_features(df)
        
        if weather_df is not None:
            df = self.create_weather_features(df, weather_df)
        
        if is_training:
            df = self.create_target(df, horizon_days=horizon_days)
        
        # Define feature columns
        feature_columns = self._get_feature_columns(df, is_training)
        
        target_column = f"target_{horizon_days}d" if is_training else None
        
        return df, feature_columns, target_column
    
    def _get_feature_columns(
        self,
        df: pd.DataFrame,
        is_training: bool,
    ) -> List[str]:
        """Get list of feature columns from DataFrame."""
        exclude_patterns = [
            "target_", "id", "created_at", "updated_at",
            "price_date", "weather_date",
        ]
        
        feature_columns = []
        for col in df.columns:
            # Skip excluded patterns
            if any(pattern in col.lower() for pattern in exclude_patterns):
                continue
            # Skip string columns
            if df[col].dtype == "object":
                continue
            feature_columns.append(col)
        
        return feature_columns
    
    def create_sequence(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        sequence_length: int = 30,
        target_column: Optional[str] = None,
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Create sequences for LSTM/Transformer models.
        
        Args:
            df: DataFrame with features
            feature_columns: List of feature columns
            sequence_length: Number of time steps in each sequence
            target_column: Target column name (None for inference)
            
        Returns:
            Tuple of (X, y) arrays
        """
        X, y = [], []
        
        data = df[feature_columns].values
        if target_column:
            target = df[target_column].values
        
        for i in range(sequence_length, len(data)):
            X.append(data[i - sequence_length:i])
            if target_column:
                y.append(target[i])
        
        X = np.array(X)
        y = np.array(y) if target_column else None
        
        return X, y


def prepare_training_data(
    price_df: pd.DataFrame,
    weather_df: Optional[pd.DataFrame] = None,
    horizon_days: int = 7,
    config: Optional[FeatureConfig] = None,
) -> Tuple[np.ndarray, np.ndarray, FeatureEngineer, List[str]]:
    """
    Convenience function to prepare training data.
    
    Args:
        price_df: DataFrame with historical prices
        weather_df: Optional weather DataFrame
        horizon_days: Forecast horizon
        config: Feature engineering configuration
        
    Returns:
        Tuple of (X, y, feature_engineer, feature_columns)
    """
    engineer = FeatureEngineer(config)
    
    # Prepare features
    df, feature_columns, target_column = engineer.prepare_features(
        df=price_df,
        weather_df=weather_df,
        horizon_days=horizon_days,
        is_training=True,
    )
    
    # Drop rows with NaN target
    df = df.dropna(subset=[target_column])
    
    # Fit and transform
    X = engineer.fit_transform(df, feature_columns)
    y = df[target_column].values
    
    return X, y, engineer, feature_columns


def prepare_inference_data(
    price_df: pd.DataFrame,
    feature_engineer: FeatureEngineer,
    weather_df: Optional[pd.DataFrame] = None,
    horizon_days: int = 7,
) -> Tuple[np.ndarray, pd.DataFrame]:
    """
    Convenience function to prepare inference data.
    
    Args:
        price_df: DataFrame with recent prices
        feature_engineer: Fitted FeatureEngineer instance
        weather_df: Optional weather DataFrame
        horizon_days: Forecast horizon
        
    Returns:
        Tuple of (X, processed_df)
    """
    # Prepare features
    df, feature_columns, _ = feature_engineer.prepare_features(
        df=price_df,
        weather_df=weather_df,
        horizon_days=horizon_days,
        is_training=False,
    )
    
    # Transform using fitted engineer
    X = feature_engineer.transform(df, feature_columns)
    
    return X, df
