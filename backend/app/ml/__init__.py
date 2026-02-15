"""
ML module for price forecasting and model interpretability.
"""
from app.ml.feature_engineering import (
    FeatureConfig,
    FeatureEngineer,
    prepare_training_data,
    prepare_inference_data,
)
from app.ml.xgb_forecast import (
    XGBoostConfig,
    XGBoostForecaster,
    MultiHorizonForecaster,
    TrainingResult,
    PredictionResult,
)
from app.ml.explainer import (
    ShapExplainer,
    PriceExplanationService,
    ExplanationResult,
    create_explainer,
)

__all__ = [
    # Feature Engineering
    "FeatureConfig",
    "FeatureEngineer",
    "prepare_training_data",
    "prepare_inference_data",
    # XGBoost Forecaster
    "XGBoostConfig",
    "XGBoostForecaster",
    "MultiHorizonForecaster",
    "TrainingResult",
    "PredictionResult",
    # SHAP Explainer
    "ShapExplainer",
    "PriceExplanationService",
    "ExplanationResult",
    "create_explainer",
]
