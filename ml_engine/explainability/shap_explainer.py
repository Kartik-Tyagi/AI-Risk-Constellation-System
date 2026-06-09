"""
SHAP Explainer
Uses SHAP (SHapley Additive exPlanations) to explain risk predictions
"""

import numpy as np
import pandas as pd
import shap
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SHAPExplainer:
    """SHAP-based explainability for risk models"""
    
    def __init__(self, model, feature_names: List[str]):
        """
        Initialize SHAP explainer
        
        Args:
            model: Trained model (sklearn-compatible)
            feature_names: List of feature names
        """
        self.model = model
        self.feature_names = feature_names
        self.explainer = None
        self._initialize_explainer()
        
    def _initialize_explainer(self):
        """Initialize SHAP explainer based on model type"""
        try:
            # Try TreeExplainer first (for tree-based models)
            self.explainer = shap.TreeExplainer(self.model)
            logger.info("Initialized TreeExplainer")
        except Exception:
            try:
                # Fall back to KernelExplainer (model-agnostic)
                # Use a small background dataset for efficiency
                background = shap.sample(np.random.randn(100, len(self.feature_names)), 10)
                self.explainer = shap.KernelExplainer(self.model.predict, background)
                logger.info("Initialized KernelExplainer")
            except Exception as e:
                logger.error(f"Failed to initialize SHAP explainer: {e}")
                self.explainer = None
    
    def explain_prediction(
        self,
        features: np.ndarray,
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Explain a single prediction
        
        Args:
            features: Feature vector for prediction
            entity_id: Optional entity identifier
            
        Returns:
            Dictionary containing explanation
        """
        if self.explainer is None:
            return self._fallback_explanation(features, entity_id)
        
        try:
            # Calculate SHAP values
            shap_values = self.explainer.shap_values(features.reshape(1, -1))
            
            # Handle multi-output models
            if isinstance(shap_values, list):
                shap_values = shap_values[0]
            
            # Get base value (expected value)
            if hasattr(self.explainer, 'expected_value'):
                base_value = self.explainer.expected_value
                if isinstance(base_value, np.ndarray):
                    base_value = float(base_value[0])
                else:
                    base_value = float(base_value)
            else:
                base_value = 0.0
            
            # Get prediction
            prediction = float(self.model.predict(features.reshape(1, -1))[0])
            
            # Create feature importance ranking
            feature_importance = []
            for i, (name, shap_val, feat_val) in enumerate(
                zip(self.feature_names, shap_values[0], features)
            ):
                feature_importance.append({
                    'feature': name,
                    'value': float(feat_val),
                    'shap_value': float(shap_val),
                    'abs_shap_value': abs(float(shap_val)),
                    'contribution': 'positive' if shap_val > 0 else 'negative'
                })
            
            # Sort by absolute SHAP value
            feature_importance.sort(key=lambda x: x['abs_shap_value'], reverse=True)
            
            # Get top contributing features
            top_features = feature_importance[:10]
            
            return {
                'entity_id': entity_id,
                'prediction': prediction,
                'base_value': base_value,
                'feature_importance': feature_importance,
                'top_features': top_features,
                'explanation_type': 'shap',
                'model_type': type(self.model).__name__
            }
            
        except Exception as e:
            logger.error(f"Error explaining prediction: {e}")
            return self._fallback_explanation(features, entity_id)
    
    def explain_batch(
        self,
        features: np.ndarray,
        entity_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Explain multiple predictions
        
        Args:
            features: Feature matrix (n_samples, n_features)
            entity_ids: Optional list of entity identifiers
            
        Returns:
            List of explanations
        """
        if entity_ids is None:
            entity_ids = [f"entity_{i}" for i in range(len(features))]
        
        explanations = []
        for i, (feat, eid) in enumerate(zip(features, entity_ids)):
            explanation = self.explain_prediction(feat, eid)
            explanations.append(explanation)
        
        return explanations
    
    def get_global_feature_importance(
        self,
        features: np.ndarray
    ) -> Dict[str, Any]:
        """
        Get global feature importance across dataset
        
        Args:
            features: Feature matrix
            
        Returns:
            Global feature importance
        """
        if self.explainer is None:
            return {'error': 'Explainer not initialized'}
        
        try:
            # Calculate SHAP values for all samples
            shap_values = self.explainer.shap_values(features)
            
            # Handle multi-output models
            if isinstance(shap_values, list):
                shap_values = shap_values[0]
            
            # Calculate mean absolute SHAP values
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            
            # Create feature importance list
            global_importance = []
            for name, importance in zip(self.feature_names, mean_abs_shap):
                global_importance.append({
                    'feature': name,
                    'importance': float(importance)
                })
            
            # Sort by importance
            global_importance.sort(key=lambda x: x['importance'], reverse=True)
            
            return {
                'global_importance': global_importance,
                'top_features': global_importance[:10],
                'n_samples': len(features)
            }
            
        except Exception as e:
            logger.error(f"Error calculating global importance: {e}")
            return {'error': str(e)}
    
    def generate_force_plot_data(
        self,
        features: np.ndarray,
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate data for SHAP force plot visualization
        
        Args:
            features: Feature vector
            entity_id: Optional entity identifier
            
        Returns:
            Force plot data
        """
        explanation = self.explain_prediction(features, entity_id)
        
        if 'error' in explanation:
            return explanation
        
        # Prepare data for force plot
        force_plot_data = {
            'entity_id': entity_id,
            'base_value': explanation['base_value'],
            'prediction': explanation['prediction'],
            'features': []
        }
        
        for feat in explanation['feature_importance']:
            force_plot_data['features'].append({
                'name': feat['feature'],
                'value': feat['value'],
                'effect': feat['shap_value']
            })
        
        return force_plot_data
    
    def generate_waterfall_data(
        self,
        features: np.ndarray,
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate data for waterfall chart
        
        Args:
            features: Feature vector
            entity_id: Optional entity identifier
            
        Returns:
            Waterfall chart data
        """
        explanation = self.explain_prediction(features, entity_id)
        
        if 'error' in explanation:
            return explanation
        
        # Prepare waterfall data
        waterfall_data = {
            'entity_id': entity_id,
            'base_value': explanation['base_value'],
            'prediction': explanation['prediction'],
            'steps': []
        }
        
        cumulative = explanation['base_value']
        
        # Add top features
        for feat in explanation['top_features']:
            cumulative += feat['shap_value']
            waterfall_data['steps'].append({
                'feature': feat['feature'],
                'value': feat['shap_value'],
                'cumulative': cumulative
            })
        
        return waterfall_data
    
    def _fallback_explanation(
        self,
        features: np.ndarray,
        entity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fallback explanation when SHAP is not available
        
        Args:
            features: Feature vector
            entity_id: Optional entity identifier
            
        Returns:
            Basic explanation
        """
        try:
            prediction = float(self.model.predict(features.reshape(1, -1))[0])
            
            # Simple feature importance based on feature values
            feature_importance = []
            for name, value in zip(self.feature_names, features):
                feature_importance.append({
                    'feature': name,
                    'value': float(value),
                    'importance': abs(float(value)),
                    'contribution': 'positive' if value > 0 else 'negative'
                })
            
            feature_importance.sort(key=lambda x: x['importance'], reverse=True)
            
            return {
                'entity_id': entity_id,
                'prediction': prediction,
                'feature_importance': feature_importance,
                'top_features': feature_importance[:10],
                'explanation_type': 'fallback',
                'note': 'SHAP explainer not available, using fallback method'
            }
            
        except Exception as e:
            logger.error(f"Error in fallback explanation: {e}")
            return {
                'entity_id': entity_id,
                'error': str(e),
                'explanation_type': 'error'
            }


def create_explainer(model, feature_names: List[str]) -> SHAPExplainer:
    """
    Factory function to create SHAP explainer
    
    Args:
        model: Trained model
        feature_names: List of feature names
        
    Returns:
        SHAPExplainer instance
    """
    return SHAPExplainer(model, feature_names)


# Made with Bob