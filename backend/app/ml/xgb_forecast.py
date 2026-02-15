"""
XGBoost-based price forecaster with ONNX runtime support.

This module provides training and inference capabilities for
agricultural commodity price forecasting using XGBoost models.
"""
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit, cross_val_score

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

try:
    from onnxmltools.convert import convert_xgboost
    from skl2onnx.common.data_types import FloatTensorType
    ONNX_CONVERT_AVAILABLE = True
except ImportError:
    ONNX_CONVERT_AVAILABLE = False


@dataclass
class XGBoostConfig:
    """Configuration for XGBoost model."""
    # Model parameters
    n_estimators: int = 200
    max_depth: int = 6
    learning_rate: float = 0.1
    min_child_weight: int = 1
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    colsample_bylevel: float = 0.8
    gamma: float = 0.0
    reg_alpha: float = 0.0
    reg_lambda: float = 1.0
    
    # Training parameters
    objective: str = "reg:squarederror"
    eval_metric: str = "rmse"
    early_stopping_rounds: int = 20
    random_state: int = 42
    n_jobs: int = -1
    
    # Cross-validation
    cv_folds: int = 5
    
    # ONNX
    use_onnx: bool = True
    onnx_opset: int = 12
    
    def to_xgb_params(self) -> Dict[str, Any]:
        """Convert to XGBoost parameter dictionary."""
        return {
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "learning_rate": self.learning_rate,
            "min_child_weight": self.min_child_weight,
            "subsample": self.subsample,
            "colsample_bytree": self.colsample_bytree,
            "colsample_bylevel": self.colsample_bylevel,
            "gamma": self.gamma,
            "reg_alpha": self.reg_alpha,
            "reg_lambda": self.reg_lambda,
            "objective": self.objective,
            "eval_metric": self.eval_metric,
            "random_state": self.random_state,
            "n_jobs": self.n_jobs,
        }


@dataclass
class TrainingResult:
    """Result of model training."""
    model: xgb.XGBRegressor
    feature_columns: List[str]
    metrics: Dict[str, float]
    feature_importance: Dict[str, float]
    training_time_seconds: float
    model_version: str
    onnx_session: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "feature_columns": self.feature_columns,
            "metrics": self.metrics,
            "feature_importance": self.feature_importance,
            "training_time_seconds": self.training_time_seconds,
            "model_version": self.model_version,
            "onnx_available": self.onnx_session is not None,
        }


@dataclass
class PredictionResult:
    """Result of price prediction."""
    predicted_price: float
    lower_bound: float
    upper_bound: float
    confidence: float
    feature_contributions: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "predicted_price": self.predicted_price,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "confidence": self.confidence,
            "feature_contributions": self.feature_contributions,
        }


class XGBoostForecaster:
    """
    XGBoost-based price forecaster.
    
    Supports training, evaluation, and inference for agricultural
    commodity price forecasting with optional ONNX runtime.
    """
    
    def __init__(
        self,
        config: Optional[XGBoostConfig] = None,
        model_dir: Optional[Path] = None,
    ):
        """
        Initialize the forecaster.
        
        Args:
            config: Model configuration
            model_dir: Directory for saving/loading models
        """
        self.config = config or XGBoostConfig()
        self.model_dir = model_dir or Path("models")
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.model: Optional[xgb.XGBRegressor] = None
        self.onnx_session: Optional[ort.InferenceSession] = None
        self.feature_columns: List[str] = []
        self.model_version: str = ""
        self._fitted = False
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_columns: List[str],
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
    ) -> TrainingResult:
        """
        Train the XGBoost model.
        
        Args:
            X: Training features
            y: Training targets
            feature_columns: Names of feature columns
            X_val: Validation features (optional)
            y_val: Validation targets (optional)
            
        Returns:
            TrainingResult with model and metrics
        """
        import time
        start_time = time.time()
        
        # Store feature columns
        self.feature_columns = feature_columns
        
        # Create model
        self.model = xgb.XGBRegressor(**self.config.to_xgb_params())
        
        # Prepare evaluation set
        eval_set = None
        if X_val is not None and y_val is not None:
            eval_set = [(X_val, y_val)]
        
        # Train model
        self.model.fit(
            X, y,
            eval_set=eval_set,
            early_stopping_rounds=self.config.early_stopping_rounds if eval_set else None,
            verbose=False,
        )
        
        # Calculate metrics
        metrics = self._calculate_metrics(X, y, X_val, y_val)
        
        # Get feature importance
        feature_importance = self._get_feature_importance()
        
        # Generate version
        self.model_version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Convert to ONNX if enabled
        if self.config.use_onnx and ONNX_CONVERT_AVAILABLE:
            self._convert_to_onnx(X)
        
        training_time = time.time() - start_time
        self._fitted = True
        
        return TrainingResult(
            model=self.model,
            feature_columns=feature_columns,
            metrics=metrics,
            feature_importance=feature_importance,
            training_time_seconds=training_time,
            model_version=self.model_version,
            onnx_session=self.onnx_session,
        )
    
    def _calculate_metrics(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """Calculate training and validation metrics."""
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        # Training metrics
        y_pred_train = self.model.predict(X_train)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        train_mae = mean_absolute_error(y_train, y_pred_train)
        train_r2 = r2_score(y_train, y_pred_train)
        train_mape = np.mean(np.abs((y_train - y_pred_train) / (y_train + 1e-8))) * 100
        
        metrics = {
            "train_rmse": train_rmse,
            "train_mae": train_mae,
            "train_r2": train_r2,
            "train_mape": train_mape,
        }
        
        # Validation metrics
        if X_val is not None and y_val is not None:
            y_pred_val = self.model.predict(X_val)
            val_rmse = np.sqrt(mean_squared_error(y_val, y_pred_val))
            val_mae = mean_absolute_error(y_val, y_pred_val)
            val_r2 = r2_score(y_val, y_pred_val)
            val_mape = np.mean(np.abs((y_val - y_pred_val) / (y_val + 1e-8))) * 100
            
            metrics.update({
                "val_rmse": val_rmse,
                "val_mae": val_mae,
                "val_r2": val_r2,
                "val_mape": val_mape,
            })
        
        # Cross-validation score
        try:
            tscv = TimeSeriesSplit(n_splits=self.config.cv_folds)
            cv_scores = cross_val_score(
                self.model, X_train, y_train,
                cv=tscv,
                scoring="neg_root_mean_squared_error",
            )
            metrics["cv_rmse_mean"] = -cv_scores.mean()
            metrics["cv_rmse_std"] = cv_scores.std()
        except Exception:
            pass
        
        return metrics
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model."""
        if self.model is None:
            return {}
        
        importance = self.model.feature_importances_
        return dict(zip(self.feature_columns, importance.tolist()))
    
    def _convert_to_onnx(self, X_sample: np.ndarray) -> bool:
        """Convert model to ONNX format."""
        if not ONNX_CONVERT_AVAILABLE:
            return False
        
        try:
            # Define input type
            initial_type = [("float_input", FloatTensorType([None, X_sample.shape[1]]))]
            
            # Convert
            onnx_model = convert_xgboost(
                self.model,
                initial_types=initial_type,
                target_opset=self.config.onnx_opset,
            )
            
            # Save ONNX model
            onnx_path = self.model_dir / f"model_{self.model_version}.onnx"
            with open(onnx_path, "wb") as f:
                f.write(onnx_model.SerializeToString())
            
            # Create inference session
            if ONNX_AVAILABLE:
                self.onnx_session = ort.InferenceSession(
                    str(onnx_path),
                    providers=["CPUExecutionProvider"],
                )
            
            return True
        except Exception as e:
            print(f"ONNX conversion failed: {e}")
            return False
    
    def predict(
        self,
        X: np.ndarray,
        return_confidence: bool = True,
    ) -> Union[float, PredictionResult]:
        """
        Make price predictions.
        
        Args:
            X: Feature array (single sample or batch)
            return_confidence: Whether to return confidence bounds
            
        Returns:
            Prediction or PredictionResult
        """
        if not self._fitted:
            raise ValueError("Model must be trained before prediction")
        
        # Ensure 2D array
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        # Use ONNX if available
        if self.onnx_session is not None:
            input_name = self.onnx_session.get_inputs()[0].name
            predictions = self.onnx_session.run(
                None,
                {input_name: X.astype(np.float32)},
            )[0].flatten()
        else:
            predictions = self.model.predict(X)
        
        # Single prediction
        if len(predictions) == 1:
            pred = float(predictions[0])
            
            if return_confidence:
                # Estimate confidence using training residuals
                # In practice, you'd use a more sophisticated method
                lower = pred * 0.90  # 10% lower bound
                upper = pred * 1.10  # 10% upper bound
                confidence = 0.80  # 80% confidence
                
                return PredictionResult(
                    predicted_price=pred,
                    lower_bound=lower,
                    upper_bound=upper,
                    confidence=confidence,
                )
            return pred
        
        # Batch predictions
        if return_confidence:
            return [
                PredictionResult(
                    predicted_price=float(p),
                    lower_bound=float(p * 0.90),
                    upper_bound=float(p * 1.10),
                    confidence=0.80,
                )
                for p in predictions
            ]
        return predictions
    
    def predict_with_contributions(
        self,
        X: np.ndarray,
    ) -> PredictionResult:
        """
        Make prediction with feature contributions (SHAP-like).
        
        Uses XGBoost's built-in feature contributions for interpretability.
        
        Args:
            X: Feature array (single sample)
            
        Returns:
            PredictionResult with feature contributions
        """
        if not self._fitted:
            raise ValueError("Model must be trained before prediction")
        
        # Ensure 2D array
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        # Get prediction with contributions
        # XGBoost provides SHAP values natively
        contributions = self.model.predict(X, output_margin=True, pred_contribs=True)
        
        # Extract base score and feature contributions
        base_score = contributions[0, -1]  # Last column is base score
        feature_contribs = contributions[0, :-1]  # All but last column
        
        # Create contribution dictionary
        contrib_dict = dict(zip(self.feature_columns, feature_contribs.tolist()))
        
        # Get prediction
        prediction = float(self.model.predict(X)[0])
        
        return PredictionResult(
            predicted_price=prediction,
            lower_bound=prediction * 0.90,
            upper_bound=prediction * 1.10,
            confidence=0.80,
            feature_contributions=contrib_dict,
        )
    
    def save(self, path: Optional[Path] = None) -> Path:
        """
        Save model to disk.
        
        Args:
            path: Custom save path
            
        Returns:
            Path to saved model
        """
        if not self._fitted:
            raise ValueError("Model must be trained before saving")
        
        if path is None:
            path = self.model_dir / f"model_{self.model_version}.json"
        
        # Save XGBoost model
        self.model.save_model(str(path))
        
        # Save metadata
        metadata = {
            "model_version": self.model_version,
            "feature_columns": self.feature_columns,
            "config": self.config.__dict__,
        }
        metadata_path = path.with_suffix(".metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        return path
    
    def load(self, path: Path) -> "XGBoostForecaster":
        """
        Load model from disk.
        
        Args:
            path: Path to saved model
            
        Returns:
            Self for chaining
        """
        # Load XGBoost model
        self.model = xgb.XGBRegressor()
        self.model.load_model(str(path))
        
        # Load metadata
        metadata_path = path.with_suffix(".metadata.json")
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            self.model_version = metadata.get("model_version", "")
            self.feature_columns = metadata.get("feature_columns", [])
        
        # Try to load ONNX
        onnx_path = path.with_suffix(".onnx")
        if onnx_path.exists() and ONNX_AVAILABLE:
            self.onnx_session = ort.InferenceSession(
                str(onnx_path),
                providers=["CPUExecutionProvider"],
            )
        
        self._fitted = True
        return self
    
    def get_top_features(self, n: int = 10) -> List[Tuple[str, float]]:
        """
        Get top N most important features.
        
        Args:
            n: Number of features to return
            
        Returns:
            List of (feature_name, importance) tuples
        """
        importance = self._get_feature_importance()
        sorted_importance = sorted(
            importance.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return sorted_importance[:n]


class MultiHorizonForecaster:
    """
    Multi-horizon price forecaster.
    
    Manages multiple XGBoost models for different forecast horizons.
    """
    
    def __init__(
        self,
        horizons: List[int] = None,
        config: Optional[XGBoostConfig] = None,
        model_dir: Optional[Path] = None,
    ):
        """
        Initialize multi-horizon forecaster.
        
        Args:
            horizons: List of forecast horizons in days
            config: Model configuration
            model_dir: Directory for models
        """
        self.horizons = horizons or [1, 3, 7, 14, 30]
        self.config = config or XGBoostConfig()
        self.model_dir = model_dir or Path("models")
        
        self.forecasters: Dict[int, XGBoostForecaster] = {}
        self._initialize_forecasters()
    
    def _initialize_forecasters(self):
        """Initialize forecaster for each horizon."""
        for horizon in self.horizons:
            horizon_dir = self.model_dir / f"horizon_{horizon}d"
            self.forecasters[horizon] = XGBoostForecaster(
                config=self.config,
                model_dir=horizon_dir,
            )
    
    def train_all(
        self,
        X: np.ndarray,
        y_dict: Dict[int, np.ndarray],
        feature_columns: List[str],
    ) -> Dict[int, TrainingResult]:
        """
        Train models for all horizons.
        
        Args:
            X: Feature array
            y_dict: Dictionary mapping horizon to target arrays
            feature_columns: Feature column names
            
        Returns:
            Dictionary of training results by horizon
        """
        results = {}
        for horizon, forecaster in self.forecasters.items():
            if horizon in y_dict:
                results[horizon] = forecaster.train(
                    X=X,
                    y=y_dict[horizon],
                    feature_columns=feature_columns,
                )
        return results
    
    def predict(
        self,
        X: np.ndarray,
        horizons: Optional[List[int]] = None,
    ) -> Dict[int, PredictionResult]:
        """
        Make predictions for specified horizons.
        
        Args:
            X: Feature array
            horizons: Specific horizons to predict (default: all)
            
        Returns:
            Dictionary of predictions by horizon
        """
        horizons = horizons or self.horizons
        predictions = {}
        
        for horizon in horizons:
            if horizon in self.forecasters and self.forecasters[horizon]._fitted:
                predictions[horizon] = self.forecasters[horizon].predict(X)
        
        return predictions
    
    def save_all(self, base_path: Optional[Path] = None):
        """Save all models."""
        for horizon, forecaster in self.forecasters.items():
            if forecaster._fitted:
                path = base_path / f"horizon_{horizon}d" if base_path else None
                forecaster.save(path)
    
    def load_all(self, base_path: Path):
        """Load all models."""
        for horizon, forecaster in self.forecasters.items():
            model_path = base_path / f"horizon_{horizon}d" / "model.json"
            if model_path.exists():
                forecaster.load(model_path)


def train_price_forecaster(
    price_df: pd.DataFrame,
    horizon_days: int = 7,
    config: Optional[XGBoostConfig] = None,
) -> Tuple[XGBoostForecaster, TrainingResult]:
    """
    Convenience function to train a price forecaster.
    
    Args:
        price_df: DataFrame with features and target
        horizon_days: Forecast horizon
        config: Model configuration
        
    Returns:
        Tuple of (forecaster, training_result)
    """
    from app.ml.feature_engineering import FeatureEngineer, prepare_training_data
    
    # Prepare data
    X, y, engineer, feature_columns = prepare_training_data(
        price_df=price_df,
        horizon_days=horizon_days,
        config=None,
    )
    
    # Split data
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    # Train model
    forecaster = XGBoostForecaster(config=config)
    result = forecaster.train(
        X=X_train,
        y=y_train,
        feature_columns=feature_columns,
        X_val=X_val,
        y_val=y_val,
    )
    
    return forecaster, result
