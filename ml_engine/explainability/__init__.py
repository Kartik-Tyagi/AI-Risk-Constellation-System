"""
Explainability Module
AI explainability tools for risk models
"""

from .shap_explainer import SHAPExplainer, create_explainer
from .attention_visualizer import AttentionVisualizer, create_attention_visualizer
from .risk_narrative_generator import RiskNarrativeGenerator, create_narrative_generator

__all__ = [
    'SHAPExplainer',
    'create_explainer',
    'AttentionVisualizer',
    'create_attention_visualizer',
    'RiskNarrativeGenerator',
    'create_narrative_generator'
]

# Made with Bob