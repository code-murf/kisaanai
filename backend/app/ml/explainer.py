"""
SHAP explainer for model interpretability.

This module provides SHAP (SHapley Additive exPlanations) based
interpretability for price forecasting models.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


@dataclass
class ExplanationResult:
    """Result of SHAP explanation."""
    base_value: float
    shap_values: Dict[str, float]
    feature_values: Dict[str, Any]
    predicted_value: float
    top_positive_features: List[Tuple[str, float]]
    top_negative_features: List[Tuple[str, float]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "base_value": self.base_value,
            "predicted_value": self.predicted_value,
            "shap_values": self.shap_values,
            "feature_values": self.feature_values,
            "top_positive_features": self.top_positive_features,
            "top_negative_features": self.top_negative_features,
        }
    
    def get_natural_language_explanation(self) -> str:
        """Generate natural language explanation."""
        parts = [f"The base predicted price is ₹{self.base_value:.2f} per quintal."]
        
        if self.top_positive_features:
            top_pos = self.top_positive_features[0]
            parts.append(
                f"The price is pushed up by {top_pos[0]} (₹{top_pos[1]:.2f})."
            )
        
        if self.top_negative_features:
            top_neg = self.top_negative_features[0]
            parts.append(
                f"The price is pushed down by {top_neg[0]} (₹{top_neg[1]:.2f})."
            )
        
        parts.append(f"Final predicted price: ₹{self.predicted_value:.2f}.")
        
        return " ".join(parts)


class ShapExplainer:
    """
    SHAP explainer for XGBoost models.
    
    Provides local and global explanations for price predictions.
    """
    
    def __init__(
        self,
        model: Any,
        feature_columns: List[str],
        background_data: Optional[np.ndarray] = None,
    ):
        """
        Initialize SHAP explainer.
        
        Args:
            model: Trained XGBoost model
            feature_columns: Names of feature columns
            background_data: Background dataset for explainer
        """
        if not SHAP_AVAILABLE:
            raise ImportError("SHAP library not installed. Install with: pip install shap")
        
        self.model = model
        self.feature_columns = feature_columns
        self.background_data = background_data
        
        self._explainer: Optional[shap.Explainer] = None
        self._initialize_explainer()
    
    def _initialize_explainer(self):
        """Initialize the SHAP explainer."""
        try:
            # Use TreeExplainer for XGBoost models
            self._explainer = shap.TreeExplainer(self.model)
        except Exception:
            # Fallback to KernelExplainer
            if self.background_data is not None:
                self._explainer = shap.KernelExplainer(
                    self.model.predict,
                    self.background_data,
                )
            else:
                raise ValueError(
                    "Background data required for KernelExplainer. "
                    "Provide background_data or use TreeExplainer-compatible model."
                )
    
    def explain(
        self,
        X: np.ndarray,
        feature_values: Optional[Dict[str, Any]] = None,
    ) -> ExplanationResult:
        """
        Generate SHAP explanation for a single prediction.
        
        Args:
            X: Feature array (single sample)
            feature_values: Original feature values for display
            
        Returns:
            ExplanationResult with SHAP values and interpretation
        """
        # Ensure 2D array
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        # Get SHAP values
        shap_values = self._explainer.shap_values(X)
        
        # Handle different SHAP output formats
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        shap_values = np.array(shap_values).flatten()
        
        # Get base value (expected value)
        base_value = float(self._explainer.expected_value)
        if isinstance(base_value, np.ndarray):
            base_value = float(base_value[0])
        
        # Calculate predicted value
        predicted_value = base_value + shap_values.sum()
        
        # Create SHAP value dictionary
        shap_dict = dict(zip(self.feature_columns, shap_values.tolist()))
        
        # Create feature values dictionary
        if feature_values is None:
            feature_values = dict(zip(self.feature_columns, X.flatten().tolist()))
        
        # Sort features by impact
        sorted_shap = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
        
        # Get top positive and negative features
        positive_features = [(k, v) for k, v in sorted_shap if v > 0][:5]
        negative_features = [(k, v) for k, v in sorted_shap if v < 0][:5]
        negative_features = [(k, v) for k, v in negative_features]  # Keep negative sign
        
        return ExplanationResult(
            base_value=base_value,
            shap_values=shap_dict,
            feature_values=feature_values,
            predicted_value=predicted_value,
            top_positive_features=positive_features,
            top_negative_features=negative_features,
        )
    
    def explain_batch(
        self,
        X: np.ndarray,
    ) -> List[ExplanationResult]:
        """
        Generate explanations for multiple predictions.
        
        Args:
            X: Feature array (multiple samples)
            
        Returns:
            List of ExplanationResult
        """
        results = []
        for i in range(X.shape[0]):
            result = self.explain(X[i:i+1])
            results.append(result)
        return results
    
    def get_global_importance(
        self,
        X: np.ndarray,
    ) -> Dict[str, float]:
        """
        Calculate global feature importance using mean absolute SHAP values.
        
        Args:
            X: Feature array for importance calculation
            
        Returns:
            Dictionary mapping feature names to importance scores
        """
        # Get SHAP values for all samples
        shap_values = self._explainer.shap_values(X)
        
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        # Calculate mean absolute SHAP value per feature
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        return dict(zip(self.feature_columns, mean_abs_shap.tolist()))
    
    def plot_waterfall(
        self,
        X: np.ndarray,
        feature_values: Optional[Dict[str, Any]] = None,
        save_path: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Create waterfall plot for a single prediction.
        
        Args:
            X: Feature array (single sample)
            feature_values: Original feature values
            save_path: Path to save the plot
            
        Returns:
            Matplotlib figure if available
        """
        if not MATPLOTLIB_AVAILABLE:
            print("Matplotlib not available for plotting")
            return None
        
        explanation = self.explain(X, feature_values)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Prepare data for waterfall
        features = list(explanation.shap_values.keys())
        values = list(explanation.shap_values.values())
        
        # Sort by absolute value
        sorted_data = sorted(zip(features, values), key=lambda x: abs(x[1]), reverse=True)
        features, values = zip(*sorted_data) if sorted_data else ([], [])
        
        # Create bar colors
        colors = ["green" if v > 0 else "red" for v in values]
        
        # Plot
        y_pos = np.arange(len(features))
        ax.barh(y_pos, values, color=colors)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(features)
        ax.set_xlabel("SHAP Value (Impact on Price)")
        ax.set_title("Feature Impact on Price Prediction")
        
        # Add base and predicted values
        ax.axvline(x=0, color="black", linestyle="-", linewidth=0.5)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        
        return fig
    
    def plot_summary(
        self,
        X: np.ndarray,
        max_display: int = 20,
        save_path: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Create SHAP summary plot.
        
        Args:
            X: Feature array
            max_display: Maximum features to display
            save_path: Path to save the plot
            
        Returns:
            Matplotlib figure if available
        """
        if not MATPLOTLIB_AVAILABLE or not SHAP_AVAILABLE:
            print("Required libraries not available for plotting")
            return None
        
        # Get SHAP values
        shap_values = self._explainer.shap_values(X)
        
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        # Create summary plot
        fig = plt.figure(figsize=(10, 8))
        shap.summary_plot(
            shap_values,
            X,
            feature_names=self.feature_columns,
            max_display=max_display,
            show=False,
        )
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        
        return fig
    
    def plot_dependence(
        self,
        X: np.ndarray,
        feature: str,
        interaction_feature: Optional[str] = None,
        save_path: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Create SHAP dependence plot for a feature.
        
        Args:
            X: Feature array
            feature: Feature name to plot
            interaction_feature: Feature for interaction effect
            save_path: Path to save the plot
            
        Returns:
            Matplotlib figure if available
        """
        if not MATPLOTLIB_AVAILABLE or not SHAP_AVAILABLE:
            print("Required libraries not available for plotting")
            return None
        
        # Get feature index
        if feature not in self.feature_columns:
            raise ValueError(f"Feature {feature} not found")
        
        feature_idx = self.feature_columns.index(feature)
        
        # Get SHAP values
        shap_values = self._explainer.shap_values(X)
        
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        # Create dependence plot
        fig = plt.figure(figsize=(10, 6))
        
        interaction_idx = None
        if interaction_feature and interaction_feature in self.feature_columns:
            interaction_idx = self.feature_columns.index(interaction_feature)
        
        shap.dependence_plot(
            feature_idx,
            shap_values,
            X,
            feature_names=self.feature_columns,
            interaction_index=interaction_idx,
            show=False,
        )
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        
        return fig


class PriceExplanationService:
    """
    Service for generating user-friendly price explanations.
    
    Wraps SHAP explanations with domain-specific language for
    agricultural price predictions.
    """
    
    def __init__(self, explainer: ShapExplainer):
        """Initialize with SHAP explainer."""
        self.explainer = explainer
        
        # Feature name mappings for user-friendly display
        self.feature_translations = {
            "modal_price_lag_1": "Yesterday's Price",
            "modal_price_lag_7": "Price Last Week",
            "modal_price_lag_30": "Price Last Month",
            "modal_price_rolling_mean_7": "7-Day Average Price",
            "modal_price_rolling_std_7": "Price Volatility (7 days)",
            "price_change_pct_1d": "Daily Price Change",
            "price_change_pct_7d": "Weekly Price Change",
            "price_momentum_7d": "Price Momentum",
            "month": "Month",
            "day_of_week": "Day of Week",
            "is_weekend": "Weekend",
            "rainfall": "Rainfall",
            "temperature_avg": "Temperature",
        }
    
    def explain_prediction(
        self,
        X: np.ndarray,
        commodity_name: str = "commodity",
        mandi_name: str = "mandi",
        horizon_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive explanation for a price prediction.
        
        Args:
            X: Feature array (single sample)
            commodity_name: Name of the commodity
            mandi_name: Name of the mandi
            horizon_days: Forecast horizon
            
        Returns:
            Dictionary with explanation details
        """
        # Get SHAP explanation
        explanation = self.explainer.explain(X)
        
        # Translate feature names
        translated_shap = {}
        for feature, value in explanation.shap_values.items():
            display_name = self.feature_translations.get(feature, feature)
            translated_shap[display_name] = value
        
        # Generate summary
        summary = self._generate_summary(
            explanation=explanation,
            commodity_name=commodity_name,
            mandi_name=mandi_name,
            horizon_days=horizon_days,
        )
        
        # Generate actionable insights
        insights = self._generate_insights(explanation)
        
        return {
            "commodity": commodity_name,
            "mandi": mandi_name,
            "horizon_days": horizon_days,
            "predicted_price": explanation.predicted_value,
            "price_range": {
                "lower": explanation.predicted_value * 0.90,
                "upper": explanation.predicted_value * 1.10,
            },
            "base_price": explanation.base_value,
            "summary": summary,
            "key_factors": {
                "positive": [
                    {"factor": self.feature_translations.get(f, f), "impact": v}
                    for f, v in explanation.top_positive_features
                ],
                "negative": [
                    {"factor": self.feature_translations.get(f, f), "impact": v}
                    for f, v in explanation.top_negative_features
                ],
            },
            "all_factors": translated_shap,
            "insights": insights,
        }
    
    def _generate_summary(
        self,
        explanation: ExplanationResult,
        commodity_name: str,
        mandi_name: str,
        horizon_days: int,
    ) -> str:
        """Generate natural language summary."""
        direction = "increase" if explanation.predicted_value > explanation.base_value else "decrease"
        change_pct = abs(explanation.predicted_value - explanation.base_value) / explanation.base_value * 100
        
        summary = (
            f"The predicted price for {commodity_name} at {mandi_name} "
            f"in {horizon_days} days is ₹{explanation.predicted_value:.2f} per quintal. "
        )
        
        if change_pct > 5:
            summary += (
                f"This represents a significant {direction} of {change_pct:.1f}% "
                f"from the base price of ₹{explanation.base_value:.2f}. "
            )
        elif change_pct > 1:
            summary += (
                f"This represents a moderate {direction} of {change_pct:.1f}% "
                f"from the base price of ₹{explanation.base_value:.2f}. "
            )
        else:
            summary += "The price is expected to remain relatively stable. "
        
        # Add top factor explanation
        if explanation.top_positive_features:
            top_pos = explanation.top_positive_features[0]
            factor_name = self.feature_translations.get(top_pos[0], top_pos[0])
            summary += f"The main upward pressure comes from {factor_name}. "
        
        if explanation.top_negative_features:
            top_neg = explanation.top_negative_features[0]
            factor_name = self.feature_translations.get(top_neg[0], top_neg[0])
            summary += f"The main downward pressure comes from {factor_name}."
        
        return summary
    
    def _generate_insights(
        self,
        explanation: ExplanationResult,
    ) -> List[str]:
        """Generate actionable insights based on SHAP values."""
        insights = []
        
        shap_dict = explanation.shap_values
        
        # Price trend insight
        if shap_dict.get("price_change_pct_7d", 0) > 0:
            insights.append(
                "Prices have been rising over the past week. "
                "Consider selling soon if you have stock."
            )
        elif shap_dict.get("price_change_pct_7d", 0) < -0.05:
            insights.append(
                "Prices have been falling over the past week. "
                "Consider holding stock if storage is available."
            )
        
        # Volatility insight
        if shap_dict.get("modal_price_rolling_std_7", 0) > 100:
            insights.append(
                "High price volatility detected. "
                "Monitor the market closely before making decisions."
            )
        
        # Seasonal insight
        month = int(shap_dict.get("month", 0))
        if month in [10, 11, 12]:
            insights.append(
                "We are in the post-monsoon season. "
                "Prices typically stabilize during this period."
            )
        elif month in [6, 7, 8]:
            insights.append(
                "We are in the monsoon season. "
                "Prices may be affected by weather conditions."
            )
        
        # Momentum insight
        momentum = shap_dict.get("price_momentum_7d", 0)
        if momentum > 0.1:
            insights.append(
                "Strong upward price momentum. "
                "The market is trending bullish."
            )
        elif momentum < -0.1:
            insights.append(
                "Strong downward price momentum. "
                "The market is trending bearish."
            )
        
        return insights


def create_explainer(
    model: Any,
    feature_columns: List[str],
    background_data: Optional[np.ndarray] = None,
) -> ShapExplainer:
    """
    Convenience function to create a SHAP explainer.
    
    Args:
        model: Trained model
        feature_columns: Feature column names
        background_data: Background data for explainer
        
    Returns:
        ShapExplainer instance
    """
    return ShapExplainer(
        model=model,
        feature_columns=feature_columns,
        background_data=background_data,
    )
